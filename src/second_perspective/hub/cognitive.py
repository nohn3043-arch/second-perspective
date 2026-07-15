from __future__ import annotations

from collections import Counter
from decimal import Decimal

from ..models.enums import AlternativeStatus, IssueSeverity
from ..models.hub import CognitiveAuditReport, CognitiveRiskFinding
from ..models.schemas import DecisionRequest, DecisionResult
from ..version import VERSION
from .policy import HubPolicy

SCANNER_ID = "SECOND-PERSPECTIVE-STRUCTURAL-COGNITIVE-SCANNER"


class CognitiveRiskScanner:
    """Deterministic challenge rules; it does not infer a person's mental state."""

    def __init__(self, policy: HubPolicy | None = None) -> None:
        self.policy = policy or HubPolicy()

    def scan(
        self,
        request: DecisionRequest,
        result: DecisionResult,
    ) -> CognitiveAuditReport:
        findings: list[CognitiveRiskFinding] = []
        findings.extend(self._weight_concentration(request))
        findings.extend(self._authority_concentration(request))
        findings.extend(self._leader_assumption_exposure(result))
        findings.extend(self._critical_evidence_concentration(request))
        findings.extend(self._ranking_fragility(result))
        findings.extend(self._eligible_set_size(result))
        findings.extend(self._soft_preference_reversal(result))

        findings.sort(key=lambda item: (self._severity_order(item.severity), item.code))
        counts = Counter(finding.severity for finding in findings)
        return CognitiveAuditReport(
            scanner_id=SCANNER_ID,
            version=VERSION,
            findings=findings,
            counts={severity: counts.get(severity, 0) for severity in IssueSeverity},
        )

    def _weight_concentration(
        self,
        request: DecisionRequest,
    ) -> list[CognitiveRiskFinding]:
        concentrated = [
            criterion
            for criterion in request.criteria
            if criterion.weight >= self.policy.weight_concentration_threshold
        ]
        if not concentrated:
            return []
        return [
            CognitiveRiskFinding(
                code="DOMINANT_CRITERION_WEIGHT",
                severity=IssueSeverity.WARNING,
                title="A single criterion can dominate the declared preference model",
                explanation=(
                    "At least one criterion meets the hub policy's concentration threshold. "
                    "This may be intentional, but it deserves explicit owner confirmation."
                ),
                evidence_refs=[criterion.id for criterion in concentrated],
                challenge_question=(
                    "Would the decision owner preserve these weights after seeing outcomes "
                    "with a less concentrated preference model?"
                ),
            )
        ]

    def _authority_concentration(
        self,
        request: DecisionRequest,
    ) -> list[CognitiveRiskFinding]:
        governed = [
            item.responsibility.owner.casefold()
            for item in [*request.criteria, *request.constraints]
        ]
        if not governed:
            return []
        owner = request.decision_owner.owner.casefold()
        controlled = sum(1 for governed_owner in governed if governed_owner == owner)
        ratio = Decimal(controlled) / Decimal(len(governed))
        if ratio < self.policy.authority_concentration_threshold:
            return []
        return [
            CognitiveRiskFinding(
                code="AUTHORITY_CONCENTRATION",
                severity=IssueSeverity.WARNING,
                title="Decision authority also controls most evaluation parameters",
                explanation=(
                    f"The decision owner controls {controlled} of {len(governed)} criterion "
                    "or constraint responsibility anchors."
                ),
                evidence_refs=[request.decision_owner.owner],
                challenge_question=(
                    "Has an independent owner reviewed the constraints and weights before approval?"
                ),
            )
        ]

    @staticmethod
    def _leader_assumption_exposure(
        result: DecisionResult,
    ) -> list[CognitiveRiskFinding]:
        exposed = [
            item
            for item in result.counterfactuals
            if item.decision_changed and item.baseline_leading_candidate_ids
        ]
        if not exposed:
            return []
        return [
            CognitiveRiskFinding(
                code="LEADER_DEPENDS_ON_CRITICAL_ASSUMPTION",
                severity=IssueSeverity.ERROR,
                title="A critical assumption failure changes the leading candidate",
                explanation=(
                    "The current leader is not structurally stable under at least one declared "
                    "assumption falsification branch."
                ),
                evidence_refs=[item.trigger_assumption_id for item in exposed],
                challenge_question=(
                    "What independent evidence would falsify or strengthen these assumptions "
                    "before the approval gate?"
                ),
            )
        ]

    @staticmethod
    def _critical_evidence_concentration(
        request: DecisionRequest,
    ) -> list[CognitiveRiskFinding]:
        evidence_by_id = {item.id: item for item in request.evidence}
        critical_ids = {
            evidence_id
            for assumption in request.assumptions
            if assumption.critical
            for evidence_id in assumption.evidence_ids
        }
        if not critical_ids:
            return []
        custodians = {
            evidence_by_id[evidence_id].responsibility.owner.casefold()
            for evidence_id in critical_ids
        }
        sources = {evidence_by_id[evidence_id].source for evidence_id in critical_ids}
        if len(custodians) > 1 and len(sources) > 1:
            return []
        return [
            CognitiveRiskFinding(
                code="CRITICAL_EVIDENCE_CONCENTRATION",
                severity=IssueSeverity.WARNING,
                title="Critical assumptions rely on a concentrated evidence channel",
                explanation=(
                    "Critical evidence is concentrated in one custodian or source channel, "
                    "creating a single-point validation risk."
                ),
                evidence_refs=sorted(critical_ids),
                challenge_question=(
                    "Can an independent source corroborate the evidence supporting the leader?"
                ),
            )
        ]

    @staticmethod
    def _ranking_fragility(result: DecisionResult) -> list[CognitiveRiskFinding]:
        if not result.robustness.fragile_criterion_ids:
            return []
        return [
            CognitiveRiskFinding(
                code="RANKING_WEIGHT_FRAGILITY",
                severity=IssueSeverity.WARNING,
                title="Small declared weight changes alter the leader set",
                explanation=(
                    "The deterministic sensitivity sweep found criteria capable of changing "
                    "the leading candidate set."
                ),
                evidence_refs=result.robustness.fragile_criterion_ids,
                challenge_question=(
                    "Are these weights authorized strongly enough to justify a fragile ranking?"
                ),
            )
        ]

    def _eligible_set_size(self, result: DecisionResult) -> list[CognitiveRiskFinding]:
        if len(result.eligible_alternative_ids) >= self.policy.minimum_eligible_alternatives:
            return []
        return [
            CognitiveRiskFinding(
                code="LIMITED_ELIGIBLE_SET",
                severity=IssueSeverity.WARNING,
                title="The decision is being made from a narrow viable alternative set",
                explanation=(
                    f"Only {len(result.eligible_alternative_ids)} alternatives remain eligible; "
                    f"hub policy expects at least {self.policy.minimum_eligible_alternatives}."
                ),
                evidence_refs=result.eligible_alternative_ids,
                challenge_question=(
                    "Was a materially different alternative excluded before structuring the input?"
                ),
            )
        ]

    @staticmethod
    def _soft_preference_reversal(result: DecisionResult) -> list[CognitiveRiskFinding]:
        eligible = [
            item
            for item in result.alternatives
            if item.status == AlternativeStatus.ELIGIBLE and item.base_score is not None
        ]
        if not eligible:
            return []
        top_base = max(item.base_score for item in eligible)
        base_leaders = {
            item.alternative_id for item in eligible if item.base_score == top_base
        }
        final_leaders = set(result.leading_candidate_ids)
        if base_leaders == final_leaders:
            return []
        return [
            CognitiveRiskFinding(
                code="SOFT_PREFERENCE_REVERSES_RANKING",
                severity=IssueSeverity.WARNING,
                title="Soft constraints reverse the base weighted ranking",
                explanation=(
                    "The leading set after explicit soft penalties differs from the base "
                    "criterion-weight result."
                ),
                evidence_refs=sorted(base_leaders | final_leaders),
                challenge_question=(
                    "Did the preference owner intend the declared penalties to be ranking-decisive?"
                ),
            )
        ]

    @staticmethod
    def _severity_order(severity: IssueSeverity) -> int:
        return {
            IssueSeverity.ERROR: 0,
            IssueSeverity.WARNING: 1,
            IssueSeverity.INFO: 2,
        }[severity]
