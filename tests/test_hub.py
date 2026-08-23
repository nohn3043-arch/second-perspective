import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from second_perspective import IntelligentDecisionEngine, IntelligentDecisionHub, verify_hub_report
from second_perspective.audit import verify_algorithm_audit
from second_perspective.canonical import canonical_json
from second_perspective.models import (
    DecisionRequest,
    HubAnalysisRequest,
    InformationPriorityTier,
    ScenarioOutcomeStatus,
    SessionStatus,
)


def load_example() -> dict:
    path = Path(__file__).parents[1] / "examples" / "market_entry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def hub_request() -> HubAnalysisRequest:
    return HubAnalysisRequest.model_validate(
        {
            "decision": load_example(),
            "scenarios": [
                {
                    "id": "SC1",
                    "name": "Partner assumption fails",
                    "failed_assumption_ids": ["A1"],
                },
                {
                    "id": "SC2",
                    "name": "Partner capital shock",
                    "metric_overrides": {"S2": {"capital_required": 6000000}},
                },
            ],
        }
    )


def test_algorithm_audit_records_and_verifies_every_major_operation():
    result = IntelligentDecisionEngine().evaluate(
        DecisionRequest.model_validate(load_example())
    )

    rule_ids = [event.rule_id for event in result.algorithm_audit]
    assert verify_algorithm_audit(result.algorithm_audit) is True
    assert verify_algorithm_audit(
        result.algorithm_audit,
        result.algorithm_audit_root_hash,
    ) is True
    assert verify_algorithm_audit(result.algorithm_audit, "0" * 64) is False
    assert verify_algorithm_audit([]) is False
    assert result.algorithm_audit_root_hash == result.algorithm_audit[-1].event_hash
    assert rule_ids.count("CONSTRAINT_COMPARISON") == 6
    assert rule_ids.count("CRITERION_NORMALIZATION") == 4
    assert "ASSUMPTION_INVALIDATION_CLOSURE" in rule_ids
    assert "COUNTERFACTUAL_RESELECTION" in rule_ids
    assert "WEIGHT_SENSITIVITY" in rule_ids
    assert "LEADING_CANDIDATE_SELECTION" in rule_ids
    assert all(
        case.adjusted_weights and case.alternative_scores
        for case in result.robustness.sensitivity_cases
    )

    tampered = [event.model_copy(deep=True) for event in result.algorithm_audit]
    tampered[1] = tampered[1].model_copy(update={"output": {"tampered": True}})
    assert verify_algorithm_audit(tampered) is False


def test_counterfactual_reselection_replaces_assumption_dependent_leader():
    result = IntelligentDecisionEngine().evaluate(
        DecisionRequest.model_validate(load_example())
    )

    counterfactual = result.counterfactuals[0]
    assert counterfactual.trigger_assumption_id == "A1"
    assert counterfactual.removed_alternative_ids == ["S2"]
    assert counterfactual.counterfactual_leading_candidate_ids == ["S1"]
    assert counterfactual.decision_changed is True
    assert counterfactual.status == "leader_changed"


def test_intelligent_hub_runs_scenarios_cognitive_challenges_and_information_queue():
    hub = IntelligentDecisionHub()
    report = hub.analyze(hub_request())

    assert report.hub_version == "0.3.0"
    assert report.algorithm_audit_verified is True
    assert len(report.report_hash) == 64
    assert report.decision_record.result.leading_candidate_ids == ["S2"]

    scenario_results = {item.scenario_id: item for item in report.scenarios}
    assert scenario_results["SC1"].outcome_status == ScenarioOutcomeStatus.EVALUATED
    assert scenario_results["SC1"].removed_alternative_ids == ["S2"]
    assert scenario_results["SC1"].leading_candidate_ids == ["S1"]
    assert scenario_results["SC2"].leading_candidate_ids == ["S1"]
    assert all(len(item.scenario_fingerprint) == 64 for item in report.scenarios)
    assert all(item.algorithm_audit_verified for item in report.scenarios)
    assert all(item.algorithm_audit for item in report.scenarios)
    assert all(
        item.algorithm_audit[-1].rule_id == "DECLARED_SCENARIO_APPLICATION"
        for item in report.scenarios
    )

    finding_codes = {item.code for item in report.cognitive_audit.findings}
    assert "LEADER_DEPENDS_ON_CRITICAL_ASSUMPTION" in finding_codes
    assert "AUTHORITY_CONCENTRATION" in finding_codes
    assert "CRITICAL_EVIDENCE_CONCENTRATION" in finding_codes

    first_priority = report.information_priorities[0]
    assert first_priority.variable_ref == "assumptions.A1"
    assert first_priority.tier == InformationPriorityTier.LEADER_EXPOSED

    expected_hash = hashlib.sha256(
        canonical_json(report.model_dump(mode="json", exclude={"report_hash"}))
    ).hexdigest()
    assert report.report_hash == expected_hash
    assert verify_hub_report(report) is True
    assert hub.get_report(report.hub_run_id) == report

    fetched = hub.get_report(report.hub_run_id)
    fetched.decision_record.request.objective = "tampered outside Hub storage"
    assert hub.get_report(report.hub_run_id).decision_record.request.objective != (
        fetched.decision_record.request.objective
    )


def test_hub_can_disable_optional_cognitive_challenge_layer():
    request = hub_request().model_copy(update={"run_cognitive_audit": False})

    report = IntelligentDecisionHub().analyze(request)

    assert report.cognitive_audit is None
    assert report.algorithm_audit_verified is True


def test_evidence_failure_scenario_is_blocked_and_prioritized():
    request = HubAnalysisRequest.model_validate(
        {
            "decision": load_example(),
            "scenarios": [
                {
                    "id": "SC3",
                    "name": "Evidence withdrawn",
                    "evidence_status_overrides": {"E1": "missing"},
                }
            ],
        }
    )

    report = IntelligentDecisionHub().analyze(request)

    assert report.scenarios[0].outcome_status == ScenarioOutcomeStatus.BLOCKED
    assert any(issue.blocking for issue in report.scenarios[0].issues)


def test_hub_request_rejects_unknown_scenario_references():
    data = {
        "decision": load_example(),
        "scenarios": [
            {
                "id": "SC4",
                "name": "Invalid override",
                "metric_overrides": {"S2": {"unknown_metric": 1}},
            }
        ],
    }

    with pytest.raises(ValidationError, match="unknown metrics"):
        HubAnalysisRequest.model_validate(data)


# ── Hub session integration tests ──


def test_hub_start_session_initializes_state():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    session = hub.start_session(request)
    assert session.session_id.startswith("SESS-")
    assert session.status == SessionStatus.ACTIVE
    assert len(session.rounds) == 0
    assert all(
        state == "assumed" for state in session.assumption_states.values()
    )


def test_hub_start_session_with_signals():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    from second_perspective.models.schemas import DeviationSignal
    from datetime import datetime, timezone

    signal = DeviationSignal(
        metric="capital_required",
        observed=5000000,
        baseline=3000000,
        direction="above",
        observed_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        source="test-scanner",
    )
    session = hub.start_session(request, signals=[signal])
    assert session.deviation_signals == [signal]


def test_hub_start_session_respects_budget():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    session = hub.start_session(request, max_iterations=3, max_evidence_requests=10)
    assert session.max_iterations == 3
    assert session.max_evidence_requests == 10


def test_hub_advance_session_without_delta():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    session = hub.start_session(request)
    session = hub.advance_session(session.session_id)
    assert len(session.rounds) == 1
    assert session.status == SessionStatus.AWAITING_HUMAN
    assert session.rounds[0].round_root_hash is not None


def test_hub_advance_session_with_delta():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    from second_perspective.models import DeltaVar

    session = hub.start_session(request)
    delta = DeltaVar(
        path="A1",
        value=False,
        reason="Falsify partner availability.",
    )
    session = hub.advance_session(session.session_id, delta_vars=[delta])
    assert len(session.rounds) == 1
    assert session.rounds[0].convergence is not None
    assert session.rounds[0].convergence.candidate_set_changed is True


def test_hub_advance_session_twice_links_hashes():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    session = hub.start_session(request)
    session = hub.advance_session(session.session_id)
    session = hub.advance_session(session.session_id)
    assert len(session.rounds) == 2
    assert session.rounds[1].previous_round_hash == session.rounds[0].round_root_hash


def test_hub_human_decision_approval_seals():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    session = hub.start_session(request)
    session = hub.advance_session(session.session_id)
    session = hub.human_session_decision(session.session_id, approved=True)
    assert session.status == SessionStatus.SEALED
    assert session.sealed_at is not None


def test_hub_human_decision_with_evidence_status():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    session = hub.start_session(request)
    session = hub.human_session_decision(
        session.session_id,
        evidence_status={"A1": "verified"},
    )
    assert session.assumption_states["A1"] == "verified"
    assert session.status == SessionStatus.ACTIVE


def test_hub_get_session_returns_stored_session():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    session = hub.start_session(request)
    fetched = hub.get_session(session.session_id)
    assert fetched.session_id == session.session_id
    assert fetched.status == session.status


def test_hub_get_session_raises_for_missing():
    from second_perspective.hub import SessionNotFoundError

    hub = IntelligentDecisionHub()
    with pytest.raises(SessionNotFoundError):
        hub.get_session("NONEXISTENT")


def test_hub_session_advance_nonexistent_raises():
    from second_perspective.hub import SessionNotFoundError

    hub = IntelligentDecisionHub()
    with pytest.raises(SessionNotFoundError):
        hub.advance_session("NONEXISTENT")


def test_hub_session_immutable_after_advance():
    hub = IntelligentDecisionHub()
    request = DecisionRequest.model_validate(load_example())
    session = hub.start_session(request)
    original_id = session.session_id
    original_round_count = len(session.rounds)

    session = hub.advance_session(session.session_id)
    assert session.session_id == original_id
    assert len(session.rounds) == original_round_count + 1

    # The stored session should also be updated
    stored = hub.get_session(session.session_id)
    assert len(stored.rounds) == original_round_count + 1
