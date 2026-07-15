from decimal import Decimal
import json
from pathlib import Path

from second_perspective.decision.engine import IntelligentDecisionEngine
from second_perspective.models.enums import DecisionStatus
from second_perspective.models.schemas import DecisionRequest


def load_example() -> dict:
    path = Path(__file__).parents[1] / "examples" / "market_entry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_weighted_evaluation_selects_leading_candidate():
    request = DecisionRequest.model_validate(load_example())
    result = IntelligentDecisionEngine().evaluate(request)

    assert result.status == DecisionStatus.HUMAN_APPROVAL_REQUIRED
    assert result.audit_passed is True
    assert result.leading_candidate_ids == ["S2"]
    assert result.human_approval_required is True

    branch = result.failure_branches[0]
    assert branch.expression == "¬A1 ⇒ ΔD"
    assert branch.affected_leading_candidate_ids == ["S2"]
    assert branch.candidate_exposure_ratio == Decimal("1.000000")


def test_missing_evidence_blocks_progress():
    data = load_example()
    data["evidence"][0]["status"] = "missing"
    request = DecisionRequest.model_validate(data)
    result = IntelligentDecisionEngine().evaluate(request)

    assert result.status == DecisionStatus.EVIDENCE_PENDING
    assert result.audit_passed is False
    assert any(issue.code == "EVIDENCE_NOT_SUPPLIED" for issue in result.issues)


def test_hard_constraint_makes_alternative_ineligible():
    data = load_example()
    data["alternatives"][0]["metrics"]["capital_required"] = 9000000
    request = DecisionRequest.model_validate(data)
    result = IntelligentDecisionEngine().evaluate(request)

    s1 = next(item for item in result.alternatives if item.alternative_id == "S1")
    assert s1.status == "ineligible"
    assert "S1" not in result.eligible_alternative_ids
