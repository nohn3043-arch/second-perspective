"""Tests for the interaction layer (v0.4 upgrade — G1).

Covers:
  - AssumptionInteraction dataclass
  - InteractionDeclaration
  - All four invariants (I-1 through I-4)
  - InteractionEngine: triggered(), joint_effect(), augment()
  - Demo scenario from the upgrade doc
"""

import pytest

from second_perspective.interaction import (
    AssumptionInteraction,
    InteractionDeclaration,
    InteractionEffect,
    InteractionEngine,
    InvariantViolation,
    validate_all,
)


# ── model.py ──────────────────────────────────────────────────────────


class TestAssumptionInteraction:
    def test_conjunctive_sign(self):
        ix = AssumptionInteraction(
            id="I1", member_ids=frozenset({"A1", "A2"}),
            interaction_strength=0.5,
        )
        assert ix.effect is InteractionEffect.CONJUNCTIVE

    def test_disjunctive_sign(self):
        ix = AssumptionInteraction(
            id="I1", member_ids=frozenset({"A1", "A2"}),
            interaction_strength=-0.3,
        )
        assert ix.effect is InteractionEffect.DISJUNCTIVE

    def test_degenerate_when_zero(self):
        ix = AssumptionInteraction(
            id="I1", member_ids=frozenset({"A1", "A2"}),
            interaction_strength=0.0,
        )
        assert ix.effect is InteractionEffect.DEGENERATE

    def test_degenerate_when_none(self):
        ix = AssumptionInteraction(
            id="I1", member_ids=frozenset({"A1", "A2"}),
        )
        assert ix.effect is InteractionEffect.DEGENERATE

    def test_requires_at_least_two_members(self):
        with pytest.raises(ValueError, match="at least 2 members"):
            AssumptionInteraction(id="I1", member_ids=frozenset({"A1"}))

    def test_three_member_interaction(self):
        ix = AssumptionInteraction(
            id="I_triple",
            member_ids=frozenset({"A1", "A2", "A3"}),
            interaction_strength=0.9,
        )
        assert len(ix.member_ids) == 3
        assert ix.effect is InteractionEffect.CONJUNCTIVE


# ── invariants.py ─────────────────────────────────────────────────────


class TestInvariants:
    def _make_declaration(
        self,
        interactions=(),
        first_order=None,
        ceiling=2.0,
    ):
        return InteractionDeclaration(
            interactions=tuple(interactions),
            first_order_effects=dict(first_order or {}),
            amplification_ceiling=ceiling,
        )

    def test_i2_unknown_assumption_rejected(self):
        decl = self._make_declaration(
            interactions=[
                AssumptionInteraction(
                    id="I1",
                    member_ids=frozenset({"A1", "A9"}),
                    interaction_strength=0.3,
                ),
            ],
            first_order={"A1": 0.8},
        )
        with pytest.raises(InvariantViolation, match="I-2"):
            validate_all(decl)

    def test_i2_all_known_passes(self):
        decl = self._make_declaration(
            interactions=[
                AssumptionInteraction(
                    id="I1",
                    member_ids=frozenset({"A1", "A2"}),
                    interaction_strength=0.3,
                ),
            ],
            first_order={"A1": 0.8, "A2": 0.6},
        )
        validate_all(decl)  # should not raise

    def test_i3_ceiling_exceeded_rejected(self):
        # first_order sum = 1.4, ceiling × 2 = 2.8
        # amplifying interactions sum = 3.0 > 2.8 → violation
        decl = self._make_declaration(
            interactions=[
                AssumptionInteraction(
                    id="I1",
                    member_ids=frozenset({"A1", "A2"}),
                    interaction_strength=3.0,
                ),
            ],
            first_order={"A1": 0.8, "A2": 0.6},
            ceiling=2.0,
        )
        with pytest.raises(InvariantViolation, match="I-3"):
            validate_all(decl)

    def test_i3_within_ceiling_passes(self):
        decl = self._make_declaration(
            interactions=[
                AssumptionInteraction(
                    id="I1",
                    member_ids=frozenset({"A1", "A2"}),
                    interaction_strength=2.0,
                ),
            ],
            first_order={"A1": 0.8, "A2": 0.6},
            ceiling=2.0,
        )
        validate_all(decl)  # 2.0 ≤ 2.8 → ok

    def test_i3_redundant_interactions_dont_count(self):
        # Δ < 0 → redundant, doesn't count toward ceiling
        decl = self._make_declaration(
            interactions=[
                AssumptionInteraction(
                    id="I1",
                    member_ids=frozenset({"A1", "A2"}),
                    interaction_strength=-5.0,  # redundant
                ),
            ],
            first_order={"A1": 0.8, "A2": 0.6},
            ceiling=2.0,
        )
        validate_all(decl)  # should not raise

    def test_i3_empty_interactions_passes(self):
        decl = self._make_declaration(
            first_order={"A1": 0.8, "A2": 0.6},
        )
        validate_all(decl)

    def test_validate_all_runs_all_invariants(self):
        # Both I-2 and I-3 violated — I-2 fires first (order of checks)
        decl = self._make_declaration(
            interactions=[
                AssumptionInteraction(
                    id="I1",
                    member_ids=frozenset({"A1", "A9"}),
                    interaction_strength=10.0,
                ),
            ],
            first_order={"A1": 0.8},
        )
        with pytest.raises(InvariantViolation) as exc:
            validate_all(decl)
        assert exc.value.invariant == "I-2"


# ── engine.py ─────────────────────────────────────────────────────────


class TestInteractionEngine:
    def _make_engine(self):
        decl = InteractionDeclaration(
            interactions=(
                AssumptionInteraction(
                    id="I_policy_supply",
                    member_ids=frozenset({"A1", "A2"}),
                    description="policy gate + supply chain = amplified risk",
                    interaction_strength=0.7,
                ),
            ),
            first_order_effects={"A1": 0.8, "A2": 0.6},
            amplification_ceiling=2.0,
        )
        return InteractionEngine(decl)

    # -- triggered() ----------------------------------------------------

    def test_triggered_single_failure_no_interaction(self):
        engine = self._make_engine()
        result = engine.triggered({"A1"})
        assert len(result) == 0

    def test_triggered_both_members(self):
        engine = self._make_engine()
        result = engine.triggered({"A1", "A2"})
        assert len(result) == 1
        assert result[0].id == "I_policy_supply"

    def test_triggered_extra_assumptions_still_triggers(self):
        # Superset of members still triggers the interaction
        engine = self._make_engine()
        result = engine.triggered({"A1", "A2", "A3"})
        assert len(result) == 1

    def test_triggered_partial_members_no_trigger(self):
        engine = self._make_engine()
        result = engine.triggered({"A1", "A3"})
        assert len(result) == 0

    # -- joint_effect() -------------------------------------------------

    def test_joint_effect_single_assumption_first_order_only(self):
        engine = self._make_engine()
        result = engine.joint_effect({"A1"})
        assert result.first_order_sum == pytest.approx(0.8)
        assert result.interaction_sum == 0.0
        assert result.total_effect == pytest.approx(0.8)
        assert result.effect_classification is InteractionEffect.DEGENERATE
        assert not result.ceiling_applied

    def test_joint_effect_two_assumptions_conjunctive(self):
        engine = self._make_engine()
        result = engine.joint_effect({"A1", "A2"})
        assert result.first_order_sum == pytest.approx(1.4)
        assert result.interaction_sum == pytest.approx(0.7)
        assert result.total_effect == pytest.approx(2.1)
        assert result.effect_classification is InteractionEffect.CONJUNCTIVE
        assert not result.ceiling_applied

    def test_joint_effect_redundant_interaction(self):
        decl = InteractionDeclaration(
            interactions=(
                AssumptionInteraction(
                    id="I_red",
                    member_ids=frozenset({"A1", "A2"}),
                    interaction_strength=-0.3,
                ),
            ),
            first_order_effects={"A1": 0.8, "A2": 0.6},
        )
        engine = InteractionEngine(decl)
        result = engine.joint_effect({"A1", "A2"})
        assert result.interaction_sum == pytest.approx(-0.3)
        assert result.total_effect == pytest.approx(1.1)
        assert result.effect_classification is InteractionEffect.DISJUNCTIVE

    def test_joint_effect_ceiling_applied(self):
        # 设计：总共有 A1/A2/A3 三个假设，其中 A3 一阶效应很大（2.0），
        # 让声明的交互强度能通过 I-3（总 ceiling 够大），但当只有 A1+A2 失败时，
        # 子集 ceiling 较小，交互强度会超子集 ceiling，从而触发 joint_effect 的裁剪。
        #   总一阶绝对值 = 0.3 + 0.3 + 2.0 = 2.6
        #   总 ceiling = 2.0 × 2.6 = 5.2
        #   I(A1,A2) 强度 = 1.5   →  1.5 ≤ 5.2  →  I-3 通过
        #   子集一阶(A1+A2) = 0.6
        #   子集 ceiling = 2.0 × 0.6 = 1.2
        #   交互强度 1.5 > 1.2  →  ceiling_applied
        decl = InteractionDeclaration(
            interactions=(
                AssumptionInteraction(
                    id="I_12",
                    member_ids=frozenset({"A1", "A2"}),
                    interaction_strength=1.5,
                ),
            ),
            first_order_effects={"A1": 0.3, "A2": 0.3, "A3": 2.0},
            amplification_ceiling=2.0,
        )
        engine = InteractionEngine(decl)
        result = engine.joint_effect({"A1", "A2"})
        assert result.ceiling_applied
        # 裁剪后：interaction_sum = 1.2，total = 0.6 + 1.2 = 1.8
        assert result.total_effect == pytest.approx(1.8)

    def test_joint_effect_degenerate_interaction_zero_delta(self):
        decl = InteractionDeclaration(
            interactions=(
                AssumptionInteraction(
                    id="I_deg",
                    member_ids=frozenset({"A1", "A2"}),
                    interaction_strength=0.0,
                ),
            ),
            first_order_effects={"A1": 0.8, "A2": 0.6},
        )
        engine = InteractionEngine(decl)
        result = engine.joint_effect({"A1", "A2"})
        assert result.total_effect == pytest.approx(1.4)
        assert result.effect_classification is InteractionEffect.DEGENERATE

    def test_joint_effect_empty_failure_set(self):
        engine = self._make_engine()
        result = engine.joint_effect(set())
        assert result.total_effect == 0.0
        assert len(result.triggered_interactions) == 0

    # -- augment() ------------------------------------------------------

    def test_augment_adds_new_failure(self):
        engine = self._make_engine()
        result = engine.augment({"A1"}, "A2")
        assert result.failed_assumptions == frozenset({"A1", "A2"})
        assert len(result.triggered_interactions) == 1

    def test_augment_monotonic_never_untriggers(self):
        """I-4: adding a failure never un-triggers a triggered interaction."""
        engine = self._make_engine()
        # Start with both failed → interaction triggered
        result1 = engine.joint_effect({"A1", "A2"})
        # Add A3 → still triggered (monotonic)
        result2 = engine.augment({"A1", "A2"}, "A3")
        assert len(result2.triggered_interactions) >= len(result1.triggered_interactions)
        assert all(
            ix.id in {i.id for i in result2.triggered_interactions}
            for ix in result1.triggered_interactions
        )

    def test_augment_already_failed_is_noop(self):
        engine = self._make_engine()
        result = engine.augment({"A1", "A2"}, "A1")  # A1 already failed
        assert result.failed_assumptions == frozenset({"A1", "A2"})

    # -- demo scenario from the doc ------------------------------------

    def test_demo_scenario_policy_plus_supply_chain(self):
        """Verbatim the demo from the upgrade doc:
        A1=0.8 (policy), A2=0.6 (supply chain), Δ=+0.7
        naive first-order = 1.4, interaction-aware = 2.1, +50%
        """
        decl = InteractionDeclaration(
            interactions=(
                AssumptionInteraction(
                    id="I_policy_supply",
                    member_ids=frozenset({"A1", "A2"}),
                    interaction_strength=0.7,
                ),
            ),
            first_order_effects={"A1": 0.8, "A2": 0.6},
        )
        engine = InteractionEngine(decl)
        result = engine.joint_effect({"A1", "A2"})

        first_order = 0.8 + 0.6  # 1.4
        assert result.first_order_sum == pytest.approx(first_order)
        assert result.total_effect == pytest.approx(2.1)
        amplification = (result.total_effect - first_order) / first_order
        assert amplification == pytest.approx(0.5, abs=0.01)  # +50%

    # -- empty declaration ---------------------------------------------

    def test_engine_with_no_interactions(self):
        decl = InteractionDeclaration(
            first_order_effects={"A1": 0.5},
        )
        engine = InteractionEngine(decl)
        result = engine.joint_effect({"A1"})
        assert result.total_effect == pytest.approx(0.5)
        assert len(result.triggered_interactions) == 0
