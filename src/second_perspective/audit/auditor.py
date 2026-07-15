from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .graph import find_dependency_cycles
from ..models.enums import AssumptionSource, EvidenceStatus, IssueSeverity
from ..models.schemas import (
    AuditIssue,
    DecisionRequest,
    ResponsibilityEntry,
)

if TYPE_CHECKING:
    from ..decision.policy import DecisionPolicy


class StructuralAuditor:
    """Audits structure only. It does not generate alternatives or choose an outcome."""

    def audit(
        self,
        request: DecisionRequest,
        policy: "DecisionPolicy | None" = None,
        evaluation_as_of: datetime | None = None,
    ) -> tuple[list[AuditIssue], list[ResponsibilityEntry], list[str]]:
        if policy is None:
            from ..decision.policy import DecisionPolicy

            policy = DecisionPolicy()
        issues: list[AuditIssue] = []
        unresolved: list[str] = []
        responsibility_map: list[ResponsibilityEntry] = []

        evidence_by_id = {item.id: item for item in request.evidence}
        critical_evidence_ids = {
            evidence_id
            for assumption in request.assumptions
            if assumption.critical
            for evidence_id in assumption.evidence_ids
        }

        responsibility_map.append(
            self._responsibility_entry("decision", request.decision_id or "pending", request.decision_owner)
        )

        for criterion in request.criteria:
            responsibility_map.append(
                self._responsibility_entry("criterion_weight", criterion.id, criterion.responsibility)
            )

        for constraint in request.constraints:
            responsibility_map.append(
                self._responsibility_entry("constraint", constraint.id, constraint.responsibility)
            )

        criterion_metrics: dict[str, list[str]] = {}
        for criterion in request.criteria:
            criterion_metrics.setdefault(criterion.metric, []).append(criterion.id)
        for metric, criterion_ids in sorted(criterion_metrics.items()):
            if len(criterion_ids) > 1:
                issues.append(
                    AuditIssue(
                        code="DUPLICATE_CRITERION_METRIC",
                        severity=IssueSeverity.WARNING,
                        path="criteria",
                        message=(
                            f"Metric {metric!r} is scored by multiple criteria: "
                            f"{', '.join(sorted(criterion_ids))}. Confirm this is not double counting."
                        ),
                        blocking=False,
                    )
                )

        evaluation_as_of = evaluation_as_of or request.evaluation_as_of or datetime.now(timezone.utc)
        for evidence in request.evidence:
            responsibility_map.append(
                self._responsibility_entry("evidence", evidence.id, evidence.responsibility)
            )
            is_critical = evidence.id in critical_evidence_ids
            if evidence.valid_until is not None:
                valid_until = evidence.valid_until
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                if valid_until <= evaluation_as_of:
                    path = f"evidence.{evidence.id}.valid_until"
                    issues.append(
                        AuditIssue(
                            code="EVIDENCE_EXPIRED",
                            severity=IssueSeverity.ERROR if is_critical else IssueSeverity.WARNING,
                            path=path,
                            message="Evidence validity period has expired.",
                            blocking=is_critical,
                        )
                    )
                    unresolved.append(path)

            if is_critical and evidence.quality is None:
                issues.append(
                    AuditIssue(
                        code="EVIDENCE_QUALITY_UNASSESSED",
                        severity=(
                            IssueSeverity.ERROR
                            if policy.require_critical_evidence_quality
                            else IssueSeverity.WARNING
                        ),
                        path=f"evidence.{evidence.id}.quality",
                        message="Critical evidence has no explicit quality assessment.",
                        blocking=policy.require_critical_evidence_quality,
                    )
                )
                if policy.require_critical_evidence_quality:
                    unresolved.append(f"evidence.{evidence.id}.quality")
            elif is_critical and evidence.quality is not None:
                score = evidence.quality.composite_score
                if score < policy.critical_evidence_quality_threshold:
                    path = f"evidence.{evidence.id}.quality"
                    issues.append(
                        AuditIssue(
                            code="EVIDENCE_QUALITY_BELOW_THRESHOLD",
                            severity=IssueSeverity.ERROR,
                            path=path,
                            message=(
                                f"Evidence quality score {score} is below policy threshold "
                                f"{policy.critical_evidence_quality_threshold}."
                            ),
                            blocking=True,
                        )
                    )
                    unresolved.append(path)

        for assumption in request.assumptions:
            responsibility_map.append(
                self._responsibility_entry("assumption", assumption.id, assumption.responsibility)
            )
            if assumption.responsibility is None:
                path = f"assumptions.{assumption.id}.responsibility"
                issues.append(
                    AuditIssue(
                        code="RESPONSIBILITY_GAP",
                        severity=IssueSeverity.ERROR if assumption.critical else IssueSeverity.WARNING,
                        path=path,
                        message="No accountable node is assigned to acceptance of this assumption.",
                        blocking=assumption.critical,
                    )
                )
                unresolved.append(path)

            if assumption.source == AssumptionSource.INFERRED:
                issues.append(
                    AuditIssue(
                        code="INFERRED_ASSUMPTION",
                        severity=IssueSeverity.WARNING,
                        path=f"assumptions.{assumption.id}",
                        message="Assumption was inferred and must not be represented as user-stated fact.",
                        blocking=False,
                    )
                )

            if assumption.critical and not assumption.evidence_ids:
                path = f"assumptions.{assumption.id}.evidence_ids"
                issues.append(
                    AuditIssue(
                        code="CRITICAL_ASSUMPTION_WITHOUT_EVIDENCE",
                        severity=IssueSeverity.ERROR,
                        path=path,
                        message="Critical assumption has no linked evidence.",
                        blocking=True,
                    )
                )
                unresolved.append(path)

            for evidence_id in assumption.evidence_ids:
                evidence = evidence_by_id[evidence_id]
                if evidence.status != EvidenceStatus.SUPPLIED:
                    path = f"evidence.{evidence_id}.status"
                    issues.append(
                        AuditIssue(
                            code="EVIDENCE_NOT_SUPPLIED",
                            severity=IssueSeverity.ERROR,
                            path=path,
                            message=f"Evidence status is {evidence.status}.",
                            blocking=assumption.critical,
                        )
                    )
                    unresolved.append(path)

        graph = {assumption.id: assumption.dependencies for assumption in request.assumptions}
        for cycle in find_dependency_cycles(graph):
            issues.append(
                AuditIssue(
                    code="CAUSAL_DEPENDENCY_CYCLE",
                    severity=IssueSeverity.ERROR,
                    path="assumptions",
                    message="Dependency cycle detected: " + " -> ".join(cycle),
                    blocking=True,
                )
            )

        for alternative in request.alternatives:
            for evidence_id in alternative.evidence_ids:
                evidence = evidence_by_id[evidence_id]
                if evidence.status != EvidenceStatus.SUPPLIED:
                    path = f"alternatives.{alternative.id}.evidence_ids.{evidence_id}"
                    issues.append(
                        AuditIssue(
                            code="ALTERNATIVE_EVIDENCE_NOT_SUPPLIED",
                            severity=IssueSeverity.WARNING,
                            path=path,
                            message=f"Alternative depends on evidence with status {evidence.status}.",
                            blocking=False,
                        )
                    )
                    unresolved.append(path)

        return issues, responsibility_map, sorted(set(unresolved))

    @staticmethod
    def _responsibility_entry(element_type: str, element_id: str, responsibility):
        if responsibility is None:
            return ResponsibilityEntry(
                element_type=element_type,
                element_id=element_id,
                owner=None,
                source=None,
                status="RESPONSIBILITY_GAP",
            )
        return ResponsibilityEntry(
            element_type=element_type,
            element_id=element_id,
            owner=responsibility.owner,
            source=responsibility.source,
            status="ANCHORED",
        )
