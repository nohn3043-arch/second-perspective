"""Leading-candidate selection coverage (constraint_only vs weighted gap)."""

from decimal import Decimal

from second_perspective.decision.selection import select_leading_candidates
from second_perspective.models.enums import (
    AlternativeStatus,
    EvaluationMode,
)
from second_perspective.models.schemas import AlternativeEvaluation


def _eval(
    sid: str,
    status: AlternativeStatus = AlternativeStatus.ELIGIBLE,
    total: Decimal | None = Decimal("1"),
) -> AlternativeEvaluation:
    return AlternativeEvaluation(
        alternative_id=sid,
        status=status,
        hard_constraints_passed=status == AlternativeStatus.ELIGIBLE,
        constraint_checks=[],
        total_score=total,
    )


def test_no_eligible_returns_empty(make_request):
    evals = [_eval("S1", AlternativeStatus.INELIGIBLE, None)]
    assert select_leading_candidates(make_request(), evals) == []


def test_constraint_only_returns_all_sorted(make_request):
    evals = [_eval("S2"), _eval("S1"), _eval("S3")]
    got = select_leading_candidates(make_request(), evals)
    assert got == ["S1", "S2", "S3"]


def test_weighted_single_leader(make_request):
    request = make_request(evaluation_mode=EvaluationMode.WEIGHTED)
    evals = [_eval("S1", total=Decimal("0.9")), _eval("S2", total=Decimal("0.5"))]
    assert select_leading_candidates(request, evals) == ["S1"]


def test_weighted_beyond_gap_excluded(make_request):
    request = make_request(evaluation_mode=EvaluationMode.WEIGHTED)
    evals = [_eval("S1", total=Decimal("0.80")), _eval("S2", total=Decimal("0.70"))]
    # gap = 0.80*0.05 = 0.04; 0.10 > 0.04 -> only S1 leads
    assert select_leading_candidates(request, evals) == ["S1"]


def test_weighted_within_gap_both_leading(make_request):
    request = make_request(evaluation_mode=EvaluationMode.WEIGHTED)
    evals = [_eval("S1", total=Decimal("0.80")), _eval("S2", total=Decimal("0.79"))]
    # gap = 0.80*0.05 = 0.04; 0.01 <= 0.04 -> both leading
    assert select_leading_candidates(request, evals) == ["S1", "S2"]


def test_weighted_zero_score_treated_as_unscored(make_request):
    request = make_request(evaluation_mode=EvaluationMode.WEIGHTED)
    # Decimal("0") is falsy -> zero scores become "-inf" (unscored) in
    # selection, deterministic result: only the first unscored one leads
    evals = [_eval("S1", total=Decimal("0")), _eval("S2", total=Decimal("0"))]
    assert select_leading_candidates(request, evals) == ["S1"]


def test_weighted_unsorted_scores(make_request):
    request = make_request(evaluation_mode=EvaluationMode.WEIGHTED)
    evals = [_eval("S2", total=Decimal("0.3")), _eval("S1", total=Decimal("0.7"))]
    assert select_leading_candidates(request, evals) == ["S1"]
