from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from ..models.enums import AlternativeStatus, EvaluationMode
from ..models.schemas import (
    AlternativeEvaluation,
    DecisionRequest,
    RobustnessReport,
    SensitivityCase,
)

SIX_PLACES = Decimal("0.000001")


def _q(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _normalized_vectors(
    evaluations: list[AlternativeEvaluation],
) -> dict[str, dict[str, Decimal]]:
    vectors: dict[str, dict[str, Decimal]] = {}
    for evaluation in evaluations:
        if evaluation.status != AlternativeStatus.ELIGIBLE:
            continue
        vectors[evaluation.alternative_id] = {
            score.criterion_id: score.normalized_score
            for score in evaluation.criterion_scores
        }
    return vectors


def pareto_frontier(evaluations: list[AlternativeEvaluation]) -> list[str]:
    vectors = _normalized_vectors(evaluations)
    if not vectors:
        return sorted(
            item.alternative_id
            for item in evaluations
            if item.status == AlternativeStatus.ELIGIBLE
        )

    frontier: list[str] = []
    for candidate_id, candidate in vectors.items():
        dominated = False
        for other_id, other in vectors.items():
            if other_id == candidate_id or set(other) != set(candidate):
                continue
            at_least_as_good = all(other[key] >= candidate[key] for key in candidate)
            strictly_better = any(other[key] > candidate[key] for key in candidate)
            if at_least_as_good and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate_id)
    return sorted(frontier)


def _adjust_weights(
    original: dict[str, Decimal],
    criterion_id: str,
    target_weight: Decimal,
) -> dict[str, Decimal]:
    adjusted = dict(original)
    target_weight = min(Decimal("1"), max(Decimal("0"), target_weight))
    adjusted[criterion_id] = target_weight

    other_ids = [key for key in original if key != criterion_id]
    if not other_ids:
        return {criterion_id: Decimal("1")}

    remaining = Decimal("1") - target_weight
    original_other_total = sum((original[key] for key in other_ids), Decimal("0"))
    if original_other_total == 0:
        share = remaining / Decimal(len(other_ids))
        for key in other_ids:
            adjusted[key] = share
    else:
        for key in other_ids:
            adjusted[key] = remaining * original[key] / original_other_total
    return adjusted


def _leaders_for_weights(
    evaluations: list[AlternativeEvaluation],
    weights: dict[str, Decimal],
) -> tuple[list[str], dict[str, Decimal]]:
    totals: dict[str, Decimal] = {}
    for evaluation in evaluations:
        if evaluation.status != AlternativeStatus.ELIGIBLE:
            continue
        normalized = {
            score.criterion_id: score.normalized_score
            for score in evaluation.criterion_scores
        }
        if set(normalized) != set(weights):
            continue
        total = sum(
            (normalized[key] * weight for key, weight in weights.items()),
            Decimal("0"),
        ) - evaluation.soft_constraint_penalty
        totals[evaluation.alternative_id] = max(Decimal("0"), _q(total))

    if not totals:
        return [], {}
    top = max(totals.values())
    leaders = sorted(candidate_id for candidate_id, score in totals.items() if score == top)
    return leaders, dict(sorted(totals.items()))


def analyze_robustness(
    request: DecisionRequest,
    evaluations: list[AlternativeEvaluation],
    baseline_leaders: list[str],
    sensitivity_delta: Decimal,
) -> RobustnessReport:
    frontier = pareto_frontier(evaluations)
    if not baseline_leaders:
        return RobustnessReport(
            pareto_frontier_ids=frontier,
            stable_leader_ids=[],
            ranking_stability=None,
        )
    if request.evaluation_mode != EvaluationMode.WEIGHTED or not request.criteria:
        return RobustnessReport(
            pareto_frontier_ids=frontier,
            stable_leader_ids=sorted(baseline_leaders),
            ranking_stability=Decimal("1.000000"),
        )

    original = {criterion.id: criterion.weight for criterion in request.criteria}
    baseline_set = set(baseline_leaders)
    cases: list[SensitivityCase] = []
    fragile: set[str] = set()
    stable = set(baseline_leaders)
    unchanged = 0

    for criterion in request.criteria:
        for direction, sign in (("decrease", Decimal("-1")), ("increase", Decimal("1"))):
            target = criterion.weight + sign * sensitivity_delta
            adjusted = _adjust_weights(original, criterion.id, target)
            leaders, alternative_scores = _leaders_for_weights(evaluations, adjusted)
            cases.append(
                SensitivityCase(
                    criterion_id=criterion.id,
                    direction=direction,
                    adjusted_weight=_q(adjusted[criterion.id]),
                    adjusted_weights={
                        criterion_id: _q(weight)
                        for criterion_id, weight in sorted(adjusted.items())
                    },
                    alternative_scores=alternative_scores,
                    leading_candidate_ids=leaders,
                )
            )
            leader_set = set(leaders)
            stable.intersection_update(leader_set)
            if leader_set == baseline_set:
                unchanged += 1
            else:
                fragile.add(criterion.id)

    stability = (
        Decimal(unchanged) / Decimal(len(cases))
        if cases
        else Decimal("1")
    )
    return RobustnessReport(
        pareto_frontier_ids=frontier,
        sensitivity_cases=cases,
        fragile_criterion_ids=sorted(fragile),
        stable_leader_ids=sorted(stable),
        ranking_stability=_q(stability),
    )
