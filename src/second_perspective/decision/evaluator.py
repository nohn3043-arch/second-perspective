from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from ..models.enums import (
    AlternativeStatus,
    ConstraintKind,
    ConstraintOperator,
    EvidenceStatus,
    EvaluationMode,
    ScoringRule,
)
from ..models.schemas import (
    Alternative,
    AlternativeEvaluation,
    Constraint,
    ConstraintCheck,
    Criterion,
    CriterionScore,
    DecisionRequest,
)

SIX_PLACES = Decimal("0.000001")


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool):
        raise InvalidOperation("boolean is not a numeric metric")
    return Decimal(str(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def check_constraint(constraint: Constraint, alternative: Alternative) -> ConstraintCheck:
    if constraint.metric not in alternative.metrics:
        return ConstraintCheck(
            constraint_id=constraint.id,
            passed=None,
            actual=None,
            expected=constraint.expected,
            reason=f"Missing metric: {constraint.metric}",
        )

    actual = alternative.metrics[constraint.metric]
    expected = constraint.expected

    try:
        match constraint.operator:
            case ConstraintOperator.EQ:
                passed = actual == expected
            case ConstraintOperator.NE:
                passed = actual != expected
            case ConstraintOperator.GT:
                passed = actual > expected
            case ConstraintOperator.GTE:
                passed = actual >= expected
            case ConstraintOperator.LT:
                passed = actual < expected
            case ConstraintOperator.LTE:
                passed = actual <= expected
            case ConstraintOperator.IN:
                if not isinstance(expected, (list, tuple, set)):
                    raise TypeError("expected must be a collection for 'in'")
                passed = actual in expected
            case ConstraintOperator.NOT_IN:
                if not isinstance(expected, (list, tuple, set)):
                    raise TypeError("expected must be a collection for 'not_in'")
                passed = actual not in expected
            case _:
                raise ValueError(f"Unsupported operator: {constraint.operator}")
    except (TypeError, ValueError) as exc:
        return ConstraintCheck(
            constraint_id=constraint.id,
            passed=None,
            actual=actual,
            expected=expected,
            reason=f"Constraint comparison failed: {exc}",
        )

    return ConstraintCheck(
        constraint_id=constraint.id,
        passed=passed,
        actual=actual,
        expected=expected,
        reason="passed" if passed else "failed",
    )


def score_criterion(criterion: Criterion, alternative: Alternative) -> CriterionScore | None:
    if criterion.metric not in alternative.metrics:
        return None

    try:
        actual = _decimal(alternative.metrics[criterion.metric])
    except (InvalidOperation, ValueError):
        return None

    span = criterion.max_value - criterion.min_value
    clamped = min(max(actual, criterion.min_value), criterion.max_value)

    if criterion.scoring_rule == ScoringRule.HIGHER_IS_BETTER:
        normalized = (clamped - criterion.min_value) / span
    elif criterion.scoring_rule == ScoringRule.LOWER_IS_BETTER:
        normalized = (criterion.max_value - clamped) / span
    else:
        assert criterion.target_value is not None
        max_distance = max(
            abs(criterion.target_value - criterion.min_value),
            abs(criterion.max_value - criterion.target_value),
        )
        if max_distance == 0:
            normalized = Decimal("1")
        else:
            normalized = Decimal("1") - (abs(clamped - criterion.target_value) / max_distance)
            normalized = max(Decimal("0"), normalized)

    weighted = normalized * criterion.weight
    return CriterionScore(
        criterion_id=criterion.id,
        actual=_quantize(actual),
        normalized_score=_quantize(normalized),
        weighted_score=_quantize(weighted),
    )


def evaluate_alternative(
    request: DecisionRequest,
    alternative: Alternative,
) -> AlternativeEvaluation:
    checks = [check_constraint(constraint, alternative) for constraint in request.constraints]
    missing_metrics = sorted(
        {
            constraint.metric
            for constraint, check in zip(request.constraints, checks, strict=True)
            if check.passed is None
        }
    )

    hard_failures = [
        check
        for constraint, check in zip(request.constraints, checks, strict=True)
        if constraint.kind == ConstraintKind.HARD and check.passed is False
    ]
    hard_unknowns = [
        check
        for constraint, check in zip(request.constraints, checks, strict=True)
        if constraint.kind == ConstraintKind.HARD and check.passed is None
    ]
    soft_penalty = sum(
        (
            constraint.penalty or Decimal("0")
            for constraint, check in zip(request.constraints, checks, strict=True)
            if constraint.kind == ConstraintKind.SOFT and check.passed is False
        ),
        Decimal("0"),
    )

    evidence_by_id = {item.id: item for item in request.evidence}
    unavailable_evidence_ids = sorted(
        evidence_id
        for evidence_id in alternative.evidence_ids
        if evidence_by_id[evidence_id].status != EvidenceStatus.SUPPLIED
    )

    criterion_scores: list[CriterionScore] = []
    if request.evaluation_mode == EvaluationMode.WEIGHTED:
        for criterion in request.criteria:
            score = score_criterion(criterion, alternative)
            if score is None:
                missing_metrics.append(criterion.metric)
            else:
                criterion_scores.append(score)

    missing_metrics = sorted(set(missing_metrics))

    if hard_failures:
        status = AlternativeStatus.INELIGIBLE
    elif hard_unknowns or missing_metrics or unavailable_evidence_ids:
        status = AlternativeStatus.INCOMPLETE
    else:
        status = AlternativeStatus.ELIGIBLE

    base_score = None
    total_score = None
    if request.evaluation_mode == EvaluationMode.WEIGHTED and len(criterion_scores) == len(request.criteria):
        base_score = _quantize(
            sum((score.weighted_score for score in criterion_scores), Decimal("0"))
        )
        total_score = _quantize(max(Decimal("0"), base_score - soft_penalty))

    return AlternativeEvaluation(
        alternative_id=alternative.id,
        status=status,
        hard_constraints_passed=not hard_failures and not hard_unknowns,
        constraint_checks=checks,
        criterion_scores=criterion_scores,
        base_score=base_score,
        soft_constraint_penalty=_quantize(soft_penalty),
        total_score=total_score,
        missing_metrics=missing_metrics,
        unavailable_evidence_ids=unavailable_evidence_ids,
    )
