"""Deterministic evaluator coverage: 8 constraint operators + scoring rules."""

from decimal import Decimal

import pytest

from second_perspective.decision.evaluator import (
    _check_constraint,
    _normalize_score,
    evaluate_alternative,
)
from second_perspective.models.enums import (
    AlternativeStatus,
    ConstraintKind,
    ConstraintOperator,
    EvaluationMode,
    EvidenceStatus,
    ScoringRule,
)
from second_perspective.models.schemas import Alternative


class TestCheckConstraint:
    @pytest.mark.parametrize(
        "op,actual,expected,want",
        [
            (ConstraintOperator.EQ, "x", "x", True),
            (ConstraintOperator.EQ, "x", "y", False),
            (ConstraintOperator.NE, "x", "y", True),
            (ConstraintOperator.NE, "x", "x", False),
            (ConstraintOperator.GT, 5, 3, True),
            (ConstraintOperator.GT, 3, 5, False),
            (ConstraintOperator.GTE, 5, 5, True),
            (ConstraintOperator.LT, 3, 5, True),
            (ConstraintOperator.LTE, 5, 5, True),
            (ConstraintOperator.IN, 5, 5, True),
            (ConstraintOperator.IN, 7, 5, False),
            (ConstraintOperator.NOT_IN, 7, 5, True),
            (ConstraintOperator.NOT_IN, 5, 5, False),
        ],
    )
    def test_operators(self, op, actual, expected, want):
        assert _check_constraint(op, actual, expected) is want

    def test_missing_actual_returns_none(self):
        assert _check_constraint(ConstraintOperator.GT, None, 5) is None

    def test_non_numeric_comparison_returns_none(self):
        assert _check_constraint(ConstraintOperator.GT, "abc", 5) is None

    def test_list_expected_for_in_returns_none(self):
        # the deterministic engine converts expected via Decimal() before the
        # IN handler runs, so a list expected cannot be evaluated
        assert _check_constraint(ConstraintOperator.IN, "a", ["a", "b"]) is None


class TestNormalizeScore:
    def test_higher_is_better(self):
        assert _normalize_score(
            Decimal("80"),
            Decimal("0"),
            Decimal("100"),
            ScoringRule.HIGHER_IS_BETTER,
        ) == Decimal("0.8")

    def test_lower_is_better(self):
        assert _normalize_score(
            Decimal("20"),
            Decimal("0"),
            Decimal("100"),
            ScoringRule.LOWER_IS_BETTER,
        ) == Decimal("0.8")

    def test_target_is_better_midpoint(self):
        got = _normalize_score(
            Decimal("50"),
            Decimal("0"),
            Decimal("100"),
            ScoringRule.TARGET_IS_BETTER,
            target=Decimal("50"),
        )
        assert got == Decimal("1")

    def test_target_is_better_edge(self):
        got = _normalize_score(
            Decimal("100"),
            Decimal("0"),
            Decimal("100"),
            ScoringRule.TARGET_IS_BETTER,
            target=Decimal("50"),
        )
        assert got == Decimal("0")

    def test_zero_width_range_returns_zero(self):
        assert _normalize_score(
            Decimal("5"),
            Decimal("5"),
            Decimal("5"),
            ScoringRule.HIGHER_IS_BETTER,
        ) == Decimal("0")


class TestEvaluateAlternative:
    def test_rejects_non_alternative(self, make_request):
        with pytest.raises(TypeError):
            evaluate_alternative(make_request(), object())

    def test_hard_constraint_failure_marks_ineligible(
        self, make_request, make_constraint
    ):
        request = make_request(
            constraints=[
                make_constraint(
                    "C1",
                    metric="budget",
                    operator=ConstraintOperator.LTE,
                    expected=100,
                )
            ],
            alternatives=[
                Alternative(
                    id="S1",
                    name="a",
                    metrics={"metric_K1": 80, "budget": 5000},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
            ],
        )
        ev = evaluate_alternative(request, request.alternatives[0])
        assert ev.status == AlternativeStatus.INELIGIBLE
        assert ev.hard_constraints_passed is False
        assert ev.constraint_checks[0].passed is False

    def test_missing_metric_marks_incomplete(self, make_request):
        request = make_request(
            alternatives=[
                Alternative(
                    id="S1",
                    name="a",
                    metrics={"budget": 100},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
            ],
        )
        ev = evaluate_alternative(request, request.alternatives[0])
        assert ev.status == AlternativeStatus.INCOMPLETE
        assert ev.missing_metrics == ["metric_K1"]

    def test_disputed_evidence_listed_as_unavailable(
        self, make_request, make_evidence, make_alternative
    ):
        request = make_request(
            evidence=[
                make_evidence("E1"),
                make_evidence("E2", status=EvidenceStatus.DISPUTED),
            ],
            alternatives=[
                make_alternative(
                    "S1",
                    metrics={"metric_K1": 80, "budget": 100},
                    required_assumptions=["A1"],
                    evidence_ids=["E1", "E2"],
                ),
            ],
        )
        ev = evaluate_alternative(request, request.alternatives[0])
        assert ev.unavailable_evidence_ids == ["E2"]
        assert ev.status == AlternativeStatus.INCOMPLETE

    def test_soft_penalty_deducted(self, make_request, make_constraint):
        request = make_request(
            evaluation_mode=EvaluationMode.WEIGHTED,
            constraints=[
                make_constraint(
                    "C1",
                    metric="budget",
                    operator=ConstraintOperator.LTE,
                    expected=100,
                    kind=ConstraintKind.SOFT,
                    penalty=Decimal("0.2"),
                )
            ],
        )
        ev = evaluate_alternative(request, request.alternatives[0])
        # base_score = normalized(80) * 1.0 = 0.8; penalty 0.2
        assert ev.soft_constraint_penalty == Decimal("0.2")
        assert ev.total_score == Decimal("0.6")

    def test_missing_constraint_metric_passed_none(self, make_request):
        request = make_request(
            alternatives=[
                Alternative(
                    id="S1",
                    name="a",
                    metrics={"metric_K1": 80},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
            ],
        )
        ev = evaluate_alternative(request, request.alternatives[0])
        check = ev.constraint_checks[0]
        assert check.passed is None
        assert check.reason == "budget could not be evaluated (actual=None)"

    def test_eligible_when_complete(self, make_request):
        req = make_request()
        ev = evaluate_alternative(req, req.alternatives[0])
        assert ev.status == AlternativeStatus.ELIGIBLE
        assert ev.hard_constraints_passed is True
        assert len(ev.criterion_scores) == 1
        assert ev.criterion_scores[0].criterion_id == "K1"
