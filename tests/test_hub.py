"""IntelligentDecisionHub coverage — analyze, repositories, sessions."""

from datetime import datetime, timezone

import pytest

from second_perspective.hub import (
    HubReportNotFoundError,
    IntelligentDecisionHub,
    SessionNotFoundError,
    verify_hub_report,
)
from second_perspective.hub.integrity import seal_hub_report
from second_perspective.hub.policy import HubPolicy
from second_perspective.hub.repository import (
    InMemoryHubReportRepository,
    InMemorySessionRepository,
)
from second_perspective.models.enums import SessionStatus
from second_perspective.models.hub import HubAnalysisRequest, HubReport
from second_perspective.models.schemas import DeltaVar, DeviationSignal

TZ = timezone.utc


def _signal() -> DeviationSignal:
    return DeviationSignal(
        metric="metric_K1",
        observed=40,
        baseline=80,
        direction="below",
        observed_at=datetime(2026, 2, 1, tzinfo=TZ),
        source="pipeline-obs-1",
    )


def test_analyze_full_pipeline_seals_report(make_request):
    request = HubAnalysisRequest(
        decision=make_request(),
        scenarios=[],
        run_causal_reconstruction=True,
        run_cognitive_audit=True,
    )
    hub = IntelligentDecisionHub()
    report = hub.analyze(request)
    assert report.hub_run_id.startswith("HUB-")
    assert report.hub_version == "0.3.0"
    assert report.decision_record.revision == 1
    assert verify_hub_report(report)
    assert report.algorithm_audit_verified is True
    assert report.cognitive_audit is not None
    assert report.causal_reconstruction is not None


def test_analyze_minimal_request(make_request):
    request = HubAnalysisRequest(
        decision=make_request(),
        run_causal_reconstruction=False,
        run_cognitive_audit=False,
    )
    hub = IntelligentDecisionHub()
    report = hub.analyze(request)
    assert verify_hub_report(report)
    assert report.cognitive_audit is None
    assert report.causal_reconstruction is None
    assert report.scenarios == []


def test_analyze_with_scenarios(make_request):
    from second_perspective.models.enums import ScenarioOutcomeStatus
    from second_perspective.models.schemas import ScenarioDefinition

    request = HubAnalysisRequest(
        decision=make_request(),
        scenarios=[
            ScenarioDefinition(
                id="SCN-A",
                name="kill A1",
                failed_assumption_ids=["A1"],
                metric_overrides={},
            )
        ],
    )
    hub = IntelligentDecisionHub()
    report = hub.analyze(request)
    assert len(report.scenarios) == 1
    assert (
        report.scenarios[0].outcome_status
        == ScenarioOutcomeStatus.NO_VIABLE_ALTERNATIVE
    )
    assert verify_hub_report(report)


def test_get_report_found_and_missing(make_request):
    hub = IntelligentDecisionHub()
    request = HubAnalysisRequest(decision=make_request())
    report = hub.analyze(request)
    got = hub.get_report(report.hub_run_id)
    assert got.hub_run_id == report.hub_run_id
    assert verify_hub_report(got)
    with pytest.raises(HubReportNotFoundError):
        hub.get_report("HUB-MISSING-0001")


def test_hub_uses_custom_repositories(make_request):
    repo = InMemoryHubReportRepository()
    hub = IntelligentDecisionHub(repository=repo)
    report = hub.analyze(HubAnalysisRequest(decision=make_request()))
    assert repo.get(report.hub_run_id) is not None


def test_hub_report_repository_rejects_unsealed(make_record):
    from second_perspective.decision.integrity import seal_record
    from second_perspective.hub.policy import HubPolicy
    from second_perspective.hub.repository import InMemoryHubReportRepository
    from second_perspective.models.hub import HubReport

    repo = InMemoryHubReportRepository()
    record = seal_record(make_record())
    # Build a HubReport that is NOT sealed (report_hash == "")
    report = HubReport(
        hub_run_id="HUB-UNSEALED-0001",
        hub_version="0.3.0",
        decision_record=record,
        hub_policy=HubPolicy().snapshot(),
        algorithm_audit_verified=True,
    )
    with pytest.raises(ValueError, match="integrity verification"):
        repo.put(report)


def test_hub_report_repository_duplicate_rejected(make_request):
    repo = InMemoryHubReportRepository()
    hub = IntelligentDecisionHub(repository=repo)
    report = hub.analyze(HubAnalysisRequest(decision=make_request()))
    with pytest.raises(ValueError, match="already exists"):
        repo.put(report)


def test_seal_and_verify_roundtrip(make_request):
    hub = IntelligentDecisionHub()
    report = hub.analyze(HubAnalysisRequest(decision=make_request()))
    tampered = report.model_copy(update={"hub_version": "9.9.9"})
    assert not verify_hub_report(tampered)
    # re-sealing fixes it
    fixed = seal_hub_report(tampered)
    assert verify_hub_report(fixed)


def test_session_lifecycle_through_hub(make_request):
    hub = IntelligentDecisionHub()
    session = hub.start_session(make_request(), [_signal()])
    assert hub.get_session(session.session_id).session_id == session.session_id

    updated = hub.advance_session(session.session_id)
    assert len(updated.rounds) == 1
    assert hub.get_session(session.session_id).status in (
        SessionStatus.AWAITING_HUMAN,
        SessionStatus.CONVERGED,
    )

    decided = hub.human_session_decision(
        session.session_id,
        approved=True,
    )
    assert decided.status == SessionStatus.SEALED


def test_session_lifecycle_with_delta(make_request):
    hub = IntelligentDecisionHub()
    session = hub.start_session(make_request(), [_signal()], max_iterations=1)
    delta = DeltaVar(
        path="criteria.K1.weight",
        value="0.9",
        reason="human override",
    )
    updated = hub.advance_session(session.session_id, [delta])
    assert updated.rounds[0].applied_delta_vars == [delta]


def test_advance_missing_session_raises(make_request):
    hub = IntelligentDecisionHub()
    with pytest.raises(SessionNotFoundError):
        hub.advance_session("SESS-NOPE-0001")


def test_human_decision_evidence_status(make_request):
    from second_perspective.models.enums import AssumptionState

    hub = IntelligentDecisionHub()
    session = hub.start_session(make_request(), [_signal()])
    updated = hub.human_session_decision(
        session.session_id,
        evidence_status={"A1": "verified"},
    )
    assert updated.assumption_states["A1"] == AssumptionState.VERIFIED


def test_session_repository_put_get_update(make_request):
    repo = InMemorySessionRepository()
    hub = IntelligentDecisionHub(session_repository=repo)
    session = hub.start_session(make_request(), [])
    assert repo.get(session.session_id) is not None
    updated = hub.advance_session(session.session_id)
    assert len(repo.get(session.session_id).rounds) == 1
    assert updated is not None


def test_session_repository_duplicate_rejected(make_request):
    repo = InMemorySessionRepository()
    hub = IntelligentDecisionHub(session_repository=repo)
    session = hub.start_session(make_request(), [])
    with pytest.raises(ValueError, match="already exists"):
        repo.put(session)


def test_session_repository_update_unknown_rejected(make_request):
    from second_perspective.hub.session import ReconstructionSessionEngine

    repo = InMemorySessionRepository()
    engine = ReconstructionSessionEngine()
    session = engine.start(make_request(), [])
    with pytest.raises(ValueError, match="does not exist"):
        repo.update(session)


def test_hub_policy_snapshot():
    policy = HubPolicy(
        version="9.9.9",
        max_scenarios=3,
        run_causal_reconstruction=False,
        run_cognitive_audit=False,
        build_information_priorities=False,
    )
    snap = policy.snapshot()
    assert snap.version == "9.9.9"
    assert snap.max_scenarios == 3
    assert snap.run_causal_reconstruction is False
    assert snap.run_cognitive_audit is False
    assert snap.build_information_priorities is False
    assert snap.policy_id.startswith("HUB-POL-")
