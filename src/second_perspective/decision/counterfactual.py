from __future__ import annotations

from ..models.enums import AlternativeStatus, CounterfactualStatus
from ..models.schemas import (
    AlternativeEvaluation,
    CounterfactualResult,
    DecisionRequest,
    FailureBranch,
)
from .robustness import pareto_frontier
from .selection import select_leading_candidates


def analyze_counterfactuals(
    request: DecisionRequest,
    evaluations: list[AlternativeEvaluation],
    baseline_leaders: list[str],
    failure_branches: list[FailureBranch],
) -> list[CounterfactualResult]:
    results: list[CounterfactualResult] = []
    baseline_set = set(baseline_leaders)

    for branch in failure_branches:
        removed = set(branch.affected_alternative_ids)
        remaining = [
            evaluation
            for evaluation in evaluations
            if evaluation.alternative_id not in removed
        ]
        remaining_eligible = sorted(
            evaluation.alternative_id
            for evaluation in remaining
            if evaluation.status == AlternativeStatus.ELIGIBLE
        )
        counterfactual_leaders = select_leading_candidates(request, remaining)
        changed = set(counterfactual_leaders) != baseline_set

        if not remaining_eligible:
            status = CounterfactualStatus.NO_VIABLE_ALTERNATIVE
        elif changed:
            status = CounterfactualStatus.LEADER_CHANGED
        else:
            status = CounterfactualStatus.LEADER_STABLE

        results.append(
            CounterfactualResult(
                trigger_assumption_id=branch.assumption_id,
                status=status,
                invalidated_assumption_ids=branch.invalidated_assumption_ids,
                removed_alternative_ids=sorted(removed),
                remaining_eligible_alternative_ids=remaining_eligible,
                baseline_leading_candidate_ids=sorted(baseline_leaders),
                counterfactual_leading_candidate_ids=counterfactual_leaders,
                counterfactual_pareto_frontier_ids=pareto_frontier(remaining),
                decision_changed=changed,
            )
        )

    return results
