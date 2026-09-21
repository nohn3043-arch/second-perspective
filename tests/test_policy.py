"""DecisionPolicy snapshot coverage."""

from decimal import Decimal

from second_perspective.decision.policy import DecisionPolicy


def test_default_snapshot_fields():
    snap = DecisionPolicy().snapshot()
    assert snap.require_all_alternatives_complete is True
    assert snap.require_critical_evidence_quality is True
    assert snap.critical_evidence_quality_threshold == Decimal("0.7")
    assert snap.sensitivity_delta == Decimal("0.1")
    assert snap.version == "0.3.0"
    assert snap.policy_id.startswith("POL-")


def test_custom_policy():
    policy = DecisionPolicy(
        policy_id="POL-FIXED",
        version="9.9.9",
        require_all_alternatives_complete=False,
        require_critical_evidence_quality=False,
        critical_evidence_quality_threshold=Decimal("0.5"),
        sensitivity_delta=Decimal("0.05"),
    )
    snap = policy.snapshot()
    assert snap.policy_id == "POL-FIXED"
    assert snap.version == "9.9.9"
    assert snap.require_all_alternatives_complete is False
    assert snap.require_critical_evidence_quality is False
    assert snap.critical_evidence_quality_threshold == Decimal("0.5")
    assert snap.sensitivity_delta == Decimal("0.05")


def test_random_policy_id_generated_per_instance():
    assert DecisionPolicy().policy_id != DecisionPolicy().policy_id
