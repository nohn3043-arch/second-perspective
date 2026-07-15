from __future__ import annotations

from dataclasses import dataclass

from ..models.enums import InformationPriorityTier
from ..models.hub import InformationPriority
from ..models.schemas import DecisionRequest, DecisionResult


@dataclass(slots=True)
class _PriorityCandidate:
    variable_ref: str
    tier: InformationPriorityTier
    affected_alternative_ids: list[str]
    affected_leading_candidate_ids: list[str]
    reason: str
    recommended_action: str


_TIER_ORDER = {
    InformationPriorityTier.BLOCKING: 0,
    InformationPriorityTier.LEADER_EXPOSED: 1,
    InformationPriorityTier.STRUCTURAL: 2,
    InformationPriorityTier.REVIEW: 3,
}


def build_information_priorities(
    request: DecisionRequest,
    result: DecisionResult,
) -> list[InformationPriority]:
    candidates: dict[str, _PriorityCandidate] = {}

    for issue in result.issues:
        tier = (
            InformationPriorityTier.BLOCKING
            if issue.blocking
            else InformationPriorityTier.REVIEW
        )
        alternative_ids = _affected_from_path(request, result, issue.path)
        _offer(
            candidates,
            _PriorityCandidate(
                variable_ref=issue.path,
                tier=tier,
                affected_alternative_ids=alternative_ids,
                affected_leading_candidate_ids=sorted(
                    set(alternative_ids).intersection(result.leading_candidate_ids)
                ),
                reason=issue.message,
                recommended_action=(
                    "Repair or supply this blocking input before decision approval."
                    if issue.blocking
                    else "Record an explicit review disposition for this audit finding."
                ),
            ),
        )

    for counterfactual in result.counterfactuals:
        if counterfactual.decision_changed:
            tier = InformationPriorityTier.LEADER_EXPOSED
            action = (
                "Test the falsification condition and obtain independent evidence before approval."
            )
        else:
            tier = InformationPriorityTier.STRUCTURAL
            action = "Confirm the assumption owner and monitor its falsification condition."
        _offer(
            candidates,
            _PriorityCandidate(
                variable_ref=f"assumptions.{counterfactual.trigger_assumption_id}",
                tier=tier,
                affected_alternative_ids=counterfactual.removed_alternative_ids,
                affected_leading_candidate_ids=sorted(
                    set(counterfactual.removed_alternative_ids).intersection(
                        counterfactual.baseline_leading_candidate_ids
                    )
                ),
                reason=(
                    "Falsifying this assumption changes the counterfactual leading set."
                    if counterfactual.decision_changed
                    else "This assumption supports one or more declared alternatives."
                ),
                recommended_action=action,
            ),
        )

    for criterion_id in result.robustness.fragile_criterion_ids:
        _offer(
            candidates,
            _PriorityCandidate(
                variable_ref=f"criteria.{criterion_id}.weight",
                tier=InformationPriorityTier.STRUCTURAL,
                affected_alternative_ids=result.eligible_alternative_ids,
                affected_leading_candidate_ids=result.leading_candidate_ids,
                reason="Sensitivity analysis shows this weight can alter the leader set.",
                recommended_action="Reconfirm the weight with its anchored responsibility owner.",
            ),
        )

    ordered = sorted(
        candidates.values(),
        key=lambda item: (
            _TIER_ORDER[item.tier],
            -len(item.affected_leading_candidate_ids),
            -len(item.affected_alternative_ids),
            item.variable_ref,
        ),
    )
    return [
        InformationPriority(
            rank=rank,
            variable_ref=item.variable_ref,
            tier=item.tier,
            affected_alternative_ids=item.affected_alternative_ids,
            affected_leading_candidate_ids=item.affected_leading_candidate_ids,
            reason=item.reason,
            recommended_action=item.recommended_action,
        )
        for rank, item in enumerate(ordered, start=1)
    ]


def _offer(
    candidates: dict[str, _PriorityCandidate],
    candidate: _PriorityCandidate,
) -> None:
    current = candidates.get(candidate.variable_ref)
    if current is None or _TIER_ORDER[candidate.tier] < _TIER_ORDER[current.tier]:
        candidates[candidate.variable_ref] = candidate


def _affected_from_path(
    request: DecisionRequest,
    result: DecisionResult,
    path: str,
) -> list[str]:
    parts = path.split(".")
    if len(parts) >= 2 and parts[0] == "alternatives":
        return [parts[1]]
    if len(parts) >= 2 and parts[0] == "evidence":
        evidence_id = parts[1]
        affected = {
            alternative.id
            for alternative in request.alternatives
            if evidence_id in alternative.evidence_ids
        }
        assumption_ids = {
            assumption.id
            for assumption in request.assumptions
            if evidence_id in assumption.evidence_ids
        }
        for counterfactual in result.counterfactuals:
            if counterfactual.trigger_assumption_id in assumption_ids:
                affected.update(counterfactual.removed_alternative_ids)
        return sorted(affected)
    if len(parts) >= 2 and parts[0] == "assumptions":
        assumption_id = parts[1]
        for counterfactual in result.counterfactuals:
            if counterfactual.trigger_assumption_id == assumption_id:
                return counterfactual.removed_alternative_ids
    if parts and parts[0] in {"criteria", "constraints"}:
        return result.eligible_alternative_ids
    return []
