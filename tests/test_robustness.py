"""Robustness analysis coverage: Pareto frontier + weight sensitivity."""

from decimal import Decimal

from second_perspective.decision.robustness import (
    _compute_pareto_frontier,
    analyze_robustness,
)
from second_perspective.models.enums import (
    AlternativeStatus,
    EvaluationMode,
)
from second_perspective.models.schemas import (
    AlternativeEvaluation,
    CriterionScore,
)


def _eval_with_scores(
    sid: str, scores: dict[str, Decimal], total: Decimal | None = None
) -> AlternativeEvaluation:
    return AlternativeEvaluation(
        alternative_id=sid,
        status=AlternativeStatus.ELIGIBLE,
        hard_constraints_passed=True,
        constraint_checks=[],
        criterion_scores=[
            CriterionScore(
                criterion_id=cid,
                actual=Decimal("1"),
                normalized_score=score,
                weighted_score=score,
            )
            for cid, score in scores.items()
        ],
        total_score=total,
    )


class TestParetoFrontier:
    def test_single_criterion_top_wins(self, make_request, make_criterion):
        request = make_request(
            criteria=[make_criterion("K1")],
            alternatives=[
                make_request().alternatives[0],
                make_request().alternatives[1],
            ],
        )
        evals = [
            _eval_with_scores("S1", {"K1": Decimal("1")}),
            _eval_with_scores("S2", {"K1": Decimal("0.1")}),
        ]
        assert _compute_pareto_frontier(evals, request) == ["S1"]

    def test_incomparable_both_on_frontier(self, make_request, make_criterion):
        request = make_request(
            criteria=[make_criterion("K1"), make_criterion(kid="K2")],
        )
        evals = [
            _eval_with_scores("S1", {"K1": Decimal("1"), "K2": Decimal("0")}),
            _eval_with_scores("S2", {"K1": Decimal("0"), "K2": Decimal("1")}),
        ]
        assert _compute_pareto_frontier(evals, request) == ["S1", "S2"]

    def test_dominated_excluded(self, make_request, make_criterion):
        request = make_request(
            criteria=[make_criterion("K1"), make_criterion(kid="K2")],
        )
        evals = [
            _eval_with_scores("S1", {"K1": Decimal("1"), "K2": Decimal("1")}),
            _eval_with_scores("S2", {"K1": Decimal("0.5"), "K2": Decimal("0.5")}),
        ]
        assert _compute_pareto_frontier(evals, request) == ["S1"]

    def test_no_criteria_returns_all_eligible(self, make_request):
        evals = [_eval_with_scores("S1", {}), _eval_with_scores("S2", {})]
        assert _compute_pareto_frontier(evals, make_request(criteria=[])) == [
            "S1",
            "S2",
        ]


class TestAnalyzeRobustness:
    def test_constraint_mode_no_sensitivity_cases(self, make_request):
        request = make_request(evaluation_mode=EvaluationMode.CONSTRAINT_ONLY)
        evals = [_eval_with_scores("S1", {"K1": Decimal("1")})]
        report = analyze_robustness(request, evals, ["S1"], Decimal("0.1"))
        assert report.sensitivity_cases == []
        assert report.stable_leader_ids == ["S1"]
        assert report.ranking_stability == Decimal("1")

    def test_weighted_sensitivity_flags_fragile(self, make_request, make_criterion):
        request = make_request(
            evaluation_mode=EvaluationMode.WEIGHTED,
            criteria=[
                make_criterion("K1", weight="0.5"),
                make_criterion("K2", weight="0.5"),
            ],
        )
        # S1 favors K1, S2 favors K2; leader flips when the favored weight drops
        evals = [
            _eval_with_scores(
                "S1", {"K1": Decimal("0.8"), "K2": Decimal("0.2")}, Decimal("0.5")
            ),
            _eval_with_scores(
                "S2", {"K1": Decimal("0.2"), "K2": Decimal("0.8")}, Decimal("0.5")
            ),
        ]
        report = analyze_robustness(request, evals, ["S1"], Decimal("0.1"))
        assert len(report.sensitivity_cases) == 4  # 2 criteria x up/down
        # K1 down and K2 up both flip the leader -> both criteria fragile
        assert set(report.fragile_criterion_ids) == {"K1", "K2"}

    def test_stable_leader_with_dominant_candidate(self, make_request, make_criterion):
        request = make_request(
            evaluation_mode=EvaluationMode.WEIGHTED,
            criteria=[
                make_criterion("K1", weight="0.5"),
                make_criterion("K2", weight="0.5"),
            ],
        )
        evals = [
            _eval_with_scores(
                "S1", {"K1": Decimal("0.9"), "K2": Decimal("0.9")}, Decimal("0.9")
            ),
            _eval_with_scores(
                "S2", {"K1": Decimal("0.1"), "K2": Decimal("0.1")}, Decimal("0.1")
            ),
        ]
        report = analyze_robustness(request, evals, ["S1"], Decimal("0.1"))
        assert report.stable_leader_ids == ["S1"]
        assert report.fragile_criterion_ids == []
