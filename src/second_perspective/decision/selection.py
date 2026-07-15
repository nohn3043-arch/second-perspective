from __future__ import annotations

from ..models.enums import AlternativeStatus, EvaluationMode
from ..models.schemas import AlternativeEvaluation, DecisionRequest


def select_leading_candidates(
    request: DecisionRequest,
    evaluations: list[AlternativeEvaluation],
) -> list[str]:
    eligible = [
        evaluation
        for evaluation in evaluations
        if evaluation.status == AlternativeStatus.ELIGIBLE
    ]
    if request.evaluation_mode == EvaluationMode.WEIGHTED:
        scored = [item for item in eligible if item.total_score is not None]
        if not scored:
            return []
        top_score = max(item.total_score for item in scored)
        return sorted(
            item.alternative_id for item in scored if item.total_score == top_score
        )

    if not eligible:
        return []
    lowest_penalty = min(item.soft_constraint_penalty for item in eligible)
    return sorted(
        item.alternative_id
        for item in eligible
        if item.soft_constraint_penalty == lowest_penalty
    )
