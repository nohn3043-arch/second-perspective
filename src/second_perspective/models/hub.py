from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import Field, model_validator

from .enums import (
    DecisionStatus,
    EvidenceStatus,
    InformationPriorityTier,
    IssueSeverity,
    ScenarioOutcomeStatus,
)
from .schemas import (
    AlgorithmAuditEvent,
    AuditIssue,
    CausalReconstructionReport,
    DecisionRecord,
    DecisionRequest,
    DeviationSignal,
    StrictModel,
)


class ScenarioDefinition(StrictModel):
    id: str = Field(pattern=r"^SC[0-9A-Za-z_-]+$")
    name: str = Field(min_length=1)
    description: str | None = None
    metric_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)
    failed_assumption_ids: list[str] = Field(default_factory=list)
    evidence_status_overrides: dict[str, EvidenceStatus] = Field(default_factory=dict)


class HubAnalysisRequest(StrictModel):
    decision: DecisionRequest
    scenarios: list[ScenarioDefinition] = Field(default_factory=list)
    run_cognitive_audit: bool = True
    run_causal_reconstruction: bool = False
    deviation_signals: list[DeviationSignal] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scenarios(self) -> "HubAnalysisRequest":
        scenario_ids = [scenario.id for scenario in self.scenarios]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("duplicate scenario IDs")

        alternatives = {item.id: item for item in self.decision.alternatives}
        assumption_ids = {item.id for item in self.decision.assumptions}
        evidence_ids = {item.id for item in self.decision.evidence}

        for scenario in self.scenarios:
            unknown_alternatives = set(scenario.metric_overrides) - set(alternatives)
            if unknown_alternatives:
                raise ValueError(
                    f"scenario {scenario.id} references unknown alternatives: "
                    f"{sorted(unknown_alternatives)}"
                )
            for alternative_id, overrides in scenario.metric_overrides.items():
                unknown_metrics = set(overrides) - set(alternatives[alternative_id].metrics)
                if unknown_metrics:
                    raise ValueError(
                        f"scenario {scenario.id} references unknown metrics for "
                        f"{alternative_id}: {sorted(unknown_metrics)}"
                    )
            unknown_assumptions = set(scenario.failed_assumption_ids) - assumption_ids
            if unknown_assumptions:
                raise ValueError(
                    f"scenario {scenario.id} references unknown assumptions: "
                    f"{sorted(unknown_assumptions)}"
                )
            unknown_evidence = set(scenario.evidence_status_overrides) - evidence_ids
            if unknown_evidence:
                raise ValueError(
                    f"scenario {scenario.id} references unknown evidence: "
                    f"{sorted(unknown_evidence)}"
                )
        return self


class ScenarioResult(StrictModel):
    scenario_id: str
    name: str
    outcome_status: ScenarioOutcomeStatus
    engine_status: DecisionStatus
    failed_assumption_ids: list[str]
    invalidated_assumption_ids: list[str]
    removed_alternative_ids: list[str]
    eligible_alternative_ids: list[str]
    leading_candidate_ids: list[str]
    baseline_leading_candidate_ids: list[str]
    decision_changed: bool
    alternative_scores: dict[str, Decimal | None]
    issues: list[AuditIssue]
    scenario_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    algorithm_audit: list[AlgorithmAuditEvent] = Field(default_factory=list)
    algorithm_audit_root_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    algorithm_audit_verified: bool


class CognitiveRiskFinding(StrictModel):
    code: str
    severity: IssueSeverity
    title: str
    explanation: str
    evidence_refs: list[str] = Field(default_factory=list)
    challenge_question: str


class CognitiveAuditReport(StrictModel):
    scanner_id: str
    version: str
    findings: list[CognitiveRiskFinding] = Field(default_factory=list)
    counts: dict[IssueSeverity, int] = Field(default_factory=dict)


class InformationPriority(StrictModel):
    rank: int = Field(ge=1)
    variable_ref: str
    tier: InformationPriorityTier
    affected_alternative_ids: list[str] = Field(default_factory=list)
    affected_leading_candidate_ids: list[str] = Field(default_factory=list)
    reason: str
    recommended_action: str


class HubPolicySnapshot(StrictModel):
    policy_id: str
    version: str
    weight_concentration_threshold: Decimal
    authority_concentration_threshold: Decimal
    minimum_eligible_alternatives: int


class HubReport(StrictModel):
    hub_run_id: str = Field(pattern=r"^HUB-[0-9A-Za-z_-]+$")
    hub_version: str
    decision_record: DecisionRecord
    scenarios: list[ScenarioResult] = Field(default_factory=list)
    cognitive_audit: CognitiveAuditReport | None = None
    causal_reconstruction: CausalReconstructionReport | None = None
    information_priorities: list[InformationPriority] = Field(default_factory=list)
    hub_policy: HubPolicySnapshot
    algorithm_audit_verified: bool
    report_hash: str = Field(default="", pattern=r"^$|^[0-9a-f]{64}$")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
