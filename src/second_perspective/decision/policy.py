from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..models.schemas import PolicySnapshot
from ..version import VERSION


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    """Versioned, explicit behavior controls for deterministic evaluation."""

    policy_id: str = "SP-FOUNDATION-BASELINE"
    version: str = VERSION
    require_all_alternatives_complete: bool = True
    require_critical_evidence_quality: bool = False
    critical_evidence_quality_threshold: Decimal = Decimal("0.600000")
    sensitivity_delta: Decimal = Decimal("0.100000")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "critical_evidence_quality_threshold",
            Decimal(str(self.critical_evidence_quality_threshold)),
        )
        object.__setattr__(self, "sensitivity_delta", Decimal(str(self.sensitivity_delta)))
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("policy_id and version must not be empty")
        if not Decimal("0") <= self.critical_evidence_quality_threshold <= Decimal("1"):
            raise ValueError("critical_evidence_quality_threshold must be in [0, 1]")
        if not Decimal("0") < self.sensitivity_delta < Decimal("1"):
            raise ValueError("sensitivity_delta must be in (0, 1)")

    def snapshot(self) -> PolicySnapshot:
        return PolicySnapshot(
            policy_id=self.policy_id,
            version=self.version,
            require_all_alternatives_complete=self.require_all_alternatives_complete,
            require_critical_evidence_quality=self.require_critical_evidence_quality,
            critical_evidence_quality_threshold=self.critical_evidence_quality_threshold,
            sensitivity_delta=self.sensitivity_delta,
        )
