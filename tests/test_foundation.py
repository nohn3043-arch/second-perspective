from decimal import Decimal
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from second_perspective.decision.engine import IntelligentDecisionEngine
from second_perspective.decision.policy import DecisionPolicy
from second_perspective.governance.approval import ApprovalError
from second_perspective.models.enums import DecisionStatus
from second_perspective.models.schemas import ApprovalRequest, DecisionRequest
from second_perspective.repository import InMemoryDecisionRepository
from second_perspective.service import DecisionService


def load_example() -> dict:
    path = Path(__file__).parents[1] / "examples" / "market_entry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_soft_constraint_penalty_changes_ranking():
    data = load_example()
    data["constraints"].append(
        {
            "id": "C4",
            "name": "Prefer controlled distribution scope",
            "kind": "soft",
            "metric": "distribution_coverage",
            "operator": "lte",
            "expected": 50,
            "penalty": "0.60",
            "responsibility": data["decision_owner"],
        }
    )

    result = IntelligentDecisionEngine().evaluate(DecisionRequest.model_validate(data))
    s2 = next(item for item in result.alternatives if item.alternative_id == "S2")

    assert s2.base_score == Decimal("0.739000")
    assert s2.soft_constraint_penalty == Decimal("0.600000")
    assert s2.total_score == Decimal("0.139000")
    assert result.leading_candidate_ids == ["S1"]


def test_soft_constraint_requires_explicit_penalty():
    data = load_example()
    data["constraints"].append(
        {
            "id": "C4",
            "name": "Unpriced preference",
            "kind": "soft",
            "metric": "distribution_coverage",
            "operator": "gte",
            "expected": 60,
            "responsibility": data["decision_owner"],
        }
    )

    with pytest.raises(ValidationError, match="explicit penalty"):
        DecisionRequest.model_validate(data)


def test_constraint_only_mode_prefers_lowest_soft_penalty():
    data = load_example()
    data["evaluation_mode"] = "constraint_only"
    data["criteria"] = []

    result = IntelligentDecisionEngine().evaluate(DecisionRequest.model_validate(data))

    assert result.leading_candidate_ids == ["S2"]
    assert result.robustness.ranking_stability == Decimal("1.000000")


def test_transitive_assumption_failure_propagates_to_dependent_alternatives():
    data = load_example()
    data["assumptions"].append(
        {
            "id": "A2",
            "statement": "The operating plan depends on the partner coverage claim.",
            "source": "explicit",
            "falsification_condition": "The coverage claim fails due diligence.",
            "critical": True,
            "dependencies": ["A1"],
            "evidence_ids": ["E1"],
            "responsibility": data["assumptions"][0]["responsibility"],
        }
    )
    data["alternatives"][0]["required_assumptions"] = ["A2"]

    result = IntelligentDecisionEngine().evaluate(DecisionRequest.model_validate(data))
    branch = next(item for item in result.failure_branches if item.assumption_id == "A1")

    assert branch.invalidated_assumption_ids == ["A1", "A2"]
    assert branch.affected_alternative_ids == ["S1", "S2"]


def test_assumption_dependency_cycle_is_blocking():
    data = load_example()
    data["assumptions"][0]["dependencies"] = ["A2"]
    data["assumptions"].append(
        {
            "id": "A2",
            "statement": "The second assumption depends on the first.",
            "source": "explicit",
            "falsification_condition": "The first assumption fails.",
            "critical": True,
            "dependencies": ["A1"],
            "evidence_ids": ["E1"],
            "responsibility": data["assumptions"][0]["responsibility"],
        }
    )

    result = IntelligentDecisionEngine().evaluate(DecisionRequest.model_validate(data))

    assert result.status == DecisionStatus.EVIDENCE_PENDING
    assert any(issue.code == "CAUSAL_DEPENDENCY_CYCLE" for issue in result.issues)


def test_strict_evidence_quality_policy_blocks_unassessed_critical_evidence():
    data = load_example()
    data["evidence"][0].pop("quality")
    request = DecisionRequest.model_validate(data)
    policy = DecisionPolicy(require_critical_evidence_quality=True)

    result = IntelligentDecisionEngine(policy=policy).evaluate(request)

    assert result.status == DecisionStatus.EVIDENCE_PENDING
    assert any(
        issue.code == "EVIDENCE_QUALITY_UNASSESSED" and issue.blocking
        for issue in result.issues
    )


def test_low_quality_critical_evidence_is_blocking():
    data = load_example()
    data["evidence"][0]["quality"] = {
        "reliability": "0.4",
        "relevance": "0.5",
        "independence": "0.3",
        "freshness": "0.6",
        "assessed_by": data["evidence"][0]["responsibility"],
        "method": "document review",
    }

    result = IntelligentDecisionEngine().evaluate(DecisionRequest.model_validate(data))

    assert result.status == DecisionStatus.EVIDENCE_PENDING
    assert any(issue.code == "EVIDENCE_QUALITY_BELOW_THRESHOLD" for issue in result.issues)


def test_evidence_expiry_uses_explicit_replay_time():
    data = load_example()
    data["evaluation_as_of"] = "2028-01-01T00:00:00Z"

    result = IntelligentDecisionEngine().evaluate(DecisionRequest.model_validate(data))

    assert result.status == DecisionStatus.EVIDENCE_PENDING
    assert result.evaluation_as_of.isoformat().startswith("2028-01-01T00:00:00")
    assert any(issue.code == "EVIDENCE_EXPIRED" for issue in result.issues)


def test_same_effective_input_has_stable_fingerprint():
    request = DecisionRequest.model_validate(load_example())

    first = IntelligentDecisionEngine().evaluate(request)
    second = IntelligentDecisionEngine().evaluate(request)

    assert first.decision_id != second.decision_id
    assert first.input_fingerprint == second.input_fingerprint
    assert first.generated_at == first.evaluation_as_of


def test_robustness_report_exposes_pareto_and_sensitivity():
    result = IntelligentDecisionEngine().evaluate(
        DecisionRequest.model_validate(load_example())
    )

    assert result.robustness.pareto_frontier_ids == ["S2"]
    assert len(result.robustness.sensitivity_cases) == 4
    assert result.robustness.stable_leader_ids == ["S2"]
    assert result.robustness.ranking_stability == Decimal("1.000000")


def test_no_eligible_alternative_has_no_stability_claim():
    data = load_example()
    for alternative in data["alternatives"]:
        alternative["metrics"]["capital_required"] = 9000000

    result = IntelligentDecisionEngine().evaluate(DecisionRequest.model_validate(data))

    assert result.status == DecisionStatus.AUDIT_FAILED
    assert result.leading_candidate_ids == []
    assert result.robustness.ranking_stability is None


def test_approval_requires_anchored_authorization_reference():
    service = DecisionService()
    record = service.evaluate(DecisionRequest.model_validate(load_example()))

    with pytest.raises(ApprovalError, match="authorization_ref"):
        service.approve(
            record.result.decision_id,
            ApprovalRequest(
                approved=True,
                approver="Board Strategy Committee",
                authorization_ref="WRONG-AUTHORITY",
            ),
        )


def test_approval_rejects_owner_without_authority_anchor():
    data = load_example()
    data["decision_owner"].pop("authorization_ref")
    service = DecisionService()
    record = service.evaluate(DecisionRequest.model_validate(data))

    with pytest.raises(ApprovalError, match="no anchored authorization_ref"):
        service.approve(
            record.result.decision_id,
            ApprovalRequest(
                approved=True,
                approver="Board Strategy Committee",
                authorization_ref="UNANCHORED",
            ),
        )


def test_decision_history_is_append_only_and_hash_chained():
    service = DecisionService()
    first = service.evaluate(DecisionRequest.model_validate(load_example()))
    second = service.approve(
        first.result.decision_id,
        ApprovalRequest(
            approved=True,
            approver="Board Strategy Committee",
            authorization_ref="GOV-2026-01",
        ),
    )

    history = service.history(first.result.decision_id)

    assert [record.revision for record in history] == [1, 2]
    assert len(first.record_hash) == 64
    assert second.parent_record_hash == first.record_hash
    assert second.record_hash != first.record_hash
    assert history[0].approval is None
    assert history[1].result.status == DecisionStatus.APPROVED
    assert history[1].result.human_approval_required is False

    history[0].request.objective = "tampered outside the repository"
    assert service.history(first.result.decision_id)[0].request.objective != history[0].request.objective

    tampered = first.model_copy(update={"record_hash": "0" * 64})
    with pytest.raises(ValueError, match="record_hash"):
        InMemoryDecisionRepository().put(tampered)


def test_temporal_fields_require_timezones_and_valid_order():
    data = load_example()
    data["evaluation_as_of"] = "2026-07-15T12:00:00"

    with pytest.raises(ValidationError, match="timezone offset"):
        DecisionRequest.model_validate(data)

    data = load_example()
    data["evidence"][0]["valid_until"] = "2026-06-01T00:00:00Z"
    with pytest.raises(ValidationError, match="later than observed_at"):
        DecisionRequest.model_validate(data)
