from __future__ import annotations

from ..models.enums import DecisionStatus
from ..models.schemas import (
    AlternativeEvaluation,
    AuditIssue,
    CounterfactualResult,
    DecisionRequest,
    FailureBranch,
    PolicySnapshot,
    RobustnessReport,
)
from .ledger import AlgorithmAuditLedger


def build_execution_audit(
    *,
    request: DecisionRequest,
    input_fingerprint: str,
    issues: list[AuditIssue],
    evaluations: list[AlternativeEvaluation],
    failure_branches: list[FailureBranch],
    counterfactuals: list[CounterfactualResult],
    robustness: RobustnessReport,
    leading_candidate_ids: list[str],
    status: DecisionStatus,
    policy: PolicySnapshot,
) -> AlgorithmAuditLedger:
    ledger = AlgorithmAuditLedger()
    ledger.append(
        stage="input",
        rule_id="REQUEST_CONTRACT",
        operation="validate_structured_request",
        inputs={
            "decision_id": request.decision_id,
            "evaluation_mode": request.evaluation_mode,
            "criteria_count": len(request.criteria),
            "constraint_count": len(request.constraints),
            "assumption_count": len(request.assumptions),
            "alternative_count": len(request.alternatives),
            "evidence_count": len(request.evidence),
            "evaluation_as_of": request.evaluation_as_of,
        },
        output={"accepted": True, "input_fingerprint": input_fingerprint},
        references=[request.decision_id or "pending"],
    )

    for evidence in request.evidence:
        ledger.append(
            stage="audit",
            rule_id="EVIDENCE_STATE",
            operation="inspect_evidence",
            inputs={
                "status": evidence.status,
                "observed_at": evidence.observed_at,
                "valid_until": evidence.valid_until,
                "quality_dimensions": (
                    evidence.quality.model_dump(mode="json") if evidence.quality else None
                ),
            },
            output={
                "quality_composite": (
                    evidence.quality.composite_score if evidence.quality else None
                ),
                "responsible_owner": evidence.responsibility.owner,
            },
            references=[evidence.id],
        )

    for assumption in request.assumptions:
        ledger.append(
            stage="audit",
            rule_id="ASSUMPTION_DEPENDENCY",
            operation="inspect_assumption_basis",
            inputs={
                "critical": assumption.critical,
                "source": assumption.source,
                "dependencies": assumption.dependencies,
                "evidence_ids": assumption.evidence_ids,
            },
            output={
                "responsible_owner": (
                    assumption.responsibility.owner if assumption.responsibility else None
                )
            },
            references=[assumption.id],
        )

    for issue in issues:
        ledger.append(
            stage="audit",
            rule_id=issue.code,
            operation="emit_audit_finding",
            inputs={"path": issue.path},
            output={
                "severity": issue.severity,
                "blocking": issue.blocking,
                "message": issue.message,
            },
            references=[issue.path],
        )

    constraints = {constraint.id: constraint for constraint in request.constraints}
    criteria = {criterion.id: criterion for criterion in request.criteria}
    for evaluation in evaluations:
        for check in evaluation.constraint_checks:
            constraint = constraints[check.constraint_id]
            ledger.append(
                stage="evaluation",
                rule_id="CONSTRAINT_COMPARISON",
                operation=f"compare_{constraint.operator}",
                inputs={
                    "kind": constraint.kind,
                    "metric": constraint.metric,
                    "actual": check.actual,
                    "expected": check.expected,
                    "penalty": constraint.penalty,
                },
                output={"passed": check.passed, "reason": check.reason},
                references=[evaluation.alternative_id, constraint.id],
            )

        for score in evaluation.criterion_scores:
            criterion = criteria[score.criterion_id]
            ledger.append(
                stage="evaluation",
                rule_id="CRITERION_NORMALIZATION",
                operation=criterion.scoring_rule,
                inputs={
                    "metric": criterion.metric,
                    "actual": score.actual,
                    "min_value": criterion.min_value,
                    "max_value": criterion.max_value,
                    "target_value": criterion.target_value,
                    "weight": criterion.weight,
                },
                output={
                    "normalized_score": score.normalized_score,
                    "weighted_score": score.weighted_score,
                },
                references=[evaluation.alternative_id, criterion.id],
            )

        ledger.append(
            stage="evaluation",
            rule_id="ALTERNATIVE_AGGREGATION",
            operation="aggregate_alternative_result",
            inputs={
                "base_score": evaluation.base_score,
                "soft_constraint_penalty": evaluation.soft_constraint_penalty,
                "missing_metrics": evaluation.missing_metrics,
                "unavailable_evidence_ids": evaluation.unavailable_evidence_ids,
            },
            output={
                "status": evaluation.status,
                "total_score": evaluation.total_score,
                "hard_constraints_passed": evaluation.hard_constraints_passed,
            },
            references=[evaluation.alternative_id],
        )

    for branch in failure_branches:
        ledger.append(
            stage="causal",
            rule_id="ASSUMPTION_INVALIDATION_CLOSURE",
            operation="propagate_assumption_failure",
            inputs={"failed_assumption_id": branch.assumption_id},
            output={
                "invalidated_assumption_ids": branch.invalidated_assumption_ids,
                "affected_alternative_ids": branch.affected_alternative_ids,
                "candidate_exposure_ratio": branch.candidate_exposure_ratio,
            },
            references=[branch.assumption_id, *branch.affected_alternative_ids],
        )

    for counterfactual in counterfactuals:
        ledger.append(
            stage="counterfactual",
            rule_id="COUNTERFACTUAL_RESELECTION",
            operation="remove_invalidated_alternatives_and_reselect",
            inputs={
                "trigger_assumption_id": counterfactual.trigger_assumption_id,
                "removed_alternative_ids": counterfactual.removed_alternative_ids,
                "baseline_leading_candidate_ids": (
                    counterfactual.baseline_leading_candidate_ids
                ),
            },
            output={
                "status": counterfactual.status,
                "counterfactual_leading_candidate_ids": (
                    counterfactual.counterfactual_leading_candidate_ids
                ),
                "decision_changed": counterfactual.decision_changed,
            },
            references=[counterfactual.trigger_assumption_id],
        )

    ledger.append(
        stage="robustness",
        rule_id="PARETO_FRONTIER",
        operation="compute_non_dominated_alternatives",
        inputs={"eligible_alternatives": [item.alternative_id for item in evaluations]},
        output={"pareto_frontier_ids": robustness.pareto_frontier_ids},
        references=robustness.pareto_frontier_ids,
    )
    for case in robustness.sensitivity_cases:
        ledger.append(
            stage="robustness",
            rule_id="WEIGHT_SENSITIVITY",
            operation=f"perturb_weight_{case.direction}",
            inputs={
                "criterion_id": case.criterion_id,
                "adjusted_weight": case.adjusted_weight,
                "adjusted_weights": case.adjusted_weights,
            },
            output={
                "alternative_scores": case.alternative_scores,
                "leading_candidate_ids": case.leading_candidate_ids,
            },
            references=[case.criterion_id, *case.leading_candidate_ids],
        )

    ledger.append(
        stage="selection",
        rule_id="LEADING_CANDIDATE_SELECTION",
        operation="select_under_declared_policy",
        inputs={
            "evaluation_mode": request.evaluation_mode,
            "policy": policy.model_dump(mode="json"),
        },
        output={"leading_candidate_ids": leading_candidate_ids},
        references=leading_candidate_ids,
    )
    ledger.append(
        stage="governance",
        rule_id="DECISION_STATE_RESOLUTION",
        operation="resolve_pre_approval_status",
        inputs={
            "blocking_issue_count": sum(1 for issue in issues if issue.blocking),
            "eligible_candidate_count": sum(
                1 for item in evaluations if item.status == "eligible"
            ),
        },
        output={"status": status, "human_approval_required": True},
        references=[request.decision_owner.owner],
    )
    return ledger
