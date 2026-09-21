"""Counterfactual analysis coverage."""

from decimal import Decimal

from second_perspective.decision.counterfactual import analyze_counterfactuals
from second_perspective.models.enums import (
    AlternativeStatus,
    CounterfactualStatus,
)
from second_perspective.models.schemas import (
    AlternativeEvaluation,
    FailureBranch,
)


def _eval(sid: str, score: Decimal | None = Decimal("1")) -> AlternativeEvaluation:
    return AlternativeEvaluation(
        alternative_id=sid,
        status=AlternativeStatus.ELIGIBLE,
        hard_constraints_passed=True,
        constraint_checks=[],
        total_score=score,
    )


def _branch(assumption_id: str, affected: list[str]) -> FailureBranch:
    return FailureBranch(
        assumption_id=assumption_id,
        expression=f"NOT {assumption_id}",
        invalidated_assumption_ids=[assumption_id],
        affected_alternative_ids=affected,
        affected_leading_candidate_ids=[a for a in affected if a in ("S1", "S2")],
        candidate_exposure_ratio=Decimal("1"),
        structural_effect="eligibility recomputed",
    )


def test_leader_stable_when_removed_not_leading(make_request):
    evals = [_eval("S1"), _eval("S2"), _eval("S3")]
    results = analyze_counterfactuals(
        make_request(),
        evals,
        ["S1", "S2"],
        [_branch("A1", ["S3"])],
    )
    assert len(results) == 1
    r = results[0]
    assert r.status == CounterfactualStatus.LEADER_STABLE
    assert r.decision_changed is False
    assert r.counterfactual_leading_candidate_ids == ["S1", "S2"]


def test_leader_changed_when_leader_removed(make_request):
    evals = [_eval("S1"), _eval("S2")]
    results = analyze_counterfactuals(
        make_request(),
        evals,
        ["S1", "S2"],
        [_branch("A1", ["S1"])],
    )
    r = results[0]
    assert r.status == CounterfactualStatus.LEADER_CHANGED
    assert r.decision_changed is True
    assert r.removed_alternative_ids == ["S1"]
    assert r.remaining_eligible_alternative_ids == ["S2"]
    assert r.counterfactual_leading_candidate_ids == ["S2"]


def test_no_viable_alternative(make_request):
    evals = [_eval("S1")]
    results = analyze_counterfactuals(
        make_request(),
        evals,
        ["S1"],
        [_branch("A1", ["S1"])],
    )
    r = results[0]
    assert r.status == CounterfactualStatus.NO_VIABLE_ALTERNATIVE
    assert r.decision_changed is True
    assert r.counterfactual_leading_candidate_ids == []


def test_empty_failure_branches(make_request):
    results = analyze_counterfactuals(make_request(), [_eval("S1")], ["S1"], [])
    assert results == []
