from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ..models.hub import HubPolicySnapshot
from ..version import VERSION


@dataclass(frozen=True, slots=True)
class HubPolicy:
    policy_id: str = "SUPER-DECISION-HUB-BASELINE"
    version: str = VERSION
    weight_concentration_threshold: Decimal = Decimal("0.650000")
    authority_concentration_threshold: Decimal = Decimal("0.750000")
    minimum_eligible_alternatives: int = 2

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "weight_concentration_threshold",
            Decimal(str(self.weight_concentration_threshold)),
        )
        object.__setattr__(
            self,
            "authority_concentration_threshold",
            Decimal(str(self.authority_concentration_threshold)),
        )
        if not self.policy_id.strip() or not self.version.strip():
            raise ValueError("policy_id and version must not be empty")
        if not Decimal("0") < self.weight_concentration_threshold <= Decimal("1"):
            raise ValueError("weight_concentration_threshold must be in (0, 1]")
        if not Decimal("0") < self.authority_concentration_threshold <= Decimal("1"):
            raise ValueError("authority_concentration_threshold must be in (0, 1]")
        if self.minimum_eligible_alternatives < 1:
            raise ValueError("minimum_eligible_alternatives must be at least 1")

    def snapshot(self) -> HubPolicySnapshot:
        return HubPolicySnapshot(
            policy_id=self.policy_id,
            version=self.version,
            weight_concentration_threshold=self.weight_concentration_threshold,
            authority_concentration_threshold=self.authority_concentration_threshold,
            minimum_eligible_alternatives=self.minimum_eligible_alternatives,
        )
