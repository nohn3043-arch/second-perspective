"""Integration tests for v0.4 formal modules wired into the core engine.

These tests verify that:
  1. InteractionDeclaration validates correctly inside DecisionRequest.
  2. invalidation_closure_with_interaction() produces interaction effects
     when a declaration is present, and is a no-op when it isn't.
  3. ReconstructionSessionEngine._stop_condition still produces the same
     outcomes as before (regression guard for the ConvergenceChecker swap).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from second_perspective.decision.causal import (
    InteractionPropagationResult,
    invalidation_closure_with_interaction,
)
from second_perspective.hub.session import ReconstructionSessionEngine
from second_perspective.models.enums import (
    AssumptionSource,
    AssumptionState,
    EvaluationMode,
    InteractionEffectType,
    SessionStatus,
)
from second_perspective.models.schemas import (
    Alternative,
    Assumption,
    DecisionRequest,
    InteractionDecl,
    InteractionDeclaration,
    ResponsibilityRef,
)


# ── helpers ────────────────────────────────────────────────────────────

def _owner() -> ResponsibilityRef:
    return ResponsibilityRef(owner="qa", source="test")


def _minimal_request(
    assumptions: list[Assumption] | None = None,
    interaction_declaration: InteractionDeclaration | None = None,
) -> DecisionRequest:
    alts = [
        Alternative(
            id="S1",
            name="Alt 1",
            required_assumptions=["A1"],
        ),
        Alternative(
            id="S2",
            name="Alt 2",
            required_assumptions=["A2"],
        ),
    ]
    if assumptions is None:
        assumptions = [
            Assumption(
                id="A1",
                statement="Policy allows it",
                source=AssumptionSource.EXPLICIT,
                falsification_condition="policy review rejects",
                responsibility=_owner(),
            ),
            Assumption(
                id="A2",
                statement="Supply chain stable",
                source=AssumptionSource.EXPLICIT,
                falsification_condition="supplier outage",
                responsibility=_owner(),
            ),
        ]
    return DecisionRequest(
        objective="test",
        decision_owner=_owner(),
        evaluation_mode=EvaluationMode.CONSTRAINT_ONLY,
        assumptions=assumptions,
        alternatives=alts,
        interaction_declaration=interaction_declaration,
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. Schema validation for InteractionDeclaration inside DecisionRequest
# ═══════════════════════════════════════════════════════════════════════

class TestInteractionSchema:
    def test_valid_declaration_accepted(self):
        decl = InteractionDeclaration(
            interactions=[
                InteractionDecl(
                    id="I1",
                    member_ids=["A1", "A2"],
                    interaction_strength=Decimal("0.5"),
                    effect_type=InteractionEffectType.CONJUNCTIVE,
                    responsibility=_owner(),
                ),
            ],
            first_order_effects={"A1": Decimal("0.8"), "A2": Decimal("0.6")},
            amplification_ceiling=Decimal("2.0"),
        )
        req = _minimal_request(interaction_declaration=decl)
        assert req.interaction_declaration is not None
        assert len(req.interaction_declaration.interactions) == 1

    def test_unknown_assumption_in_interaction_rejected(self):
        decl = InteractionDeclaration(
            interactions=[
                InteractionDecl(
                    id="I1",
                    member_ids=["A1", "A99"],
                    interaction_strength=Decimal("0.3"),
                ),
            ],
            first_order_effects={"A1": Decimal("0.8"), "A99": Decimal("0.5")},
        )
        with pytest.raises(ValidationError) as exc:
            _minimal_request(interaction_declaration=decl)
        assert "A99" in str(exc.value)
        assert "unknown assumptions" in str(exc.value)

    def test_interaction_without_first_order_rejected(self):
        with pytest.raises(ValidationError) as exc:
            InteractionDeclaration(
                interactions=[
                    InteractionDecl(
                        id="I1",
                        member_ids=["A1", "A2"],
                        interaction_strength=Decimal("0.5"),
                    ),
                ],
                first_order_effects={"A1": Decimal("0.8")},
            )
        assert "A2" in str(exc.value)
        assert "first-order" in str(exc.value)

    def test_ceiling_violation_rejected(self):
        # total |interaction| = 3.0, ceiling = 1.0 × (0.8 + 0.6) = 1.4
        with pytest.raises(ValidationError) as exc:
            InteractionDeclaration(
                interactions=[
                    InteractionDecl(
                        id="I_big",
                        member_ids=["A1", "A2"],
                        interaction_strength=Decimal("3.0"),
                    ),
                ],
                first_order_effects={"A1": Decimal("0.8"), "A2": Decimal("0.6")},
                amplification_ceiling=Decimal("1.0"),
            )
        assert "ceiling" in str(exc.value)

    def test_no_declaration_is_v03_behavior(self):
        req = _minimal_request()  # no interaction_declaration
        assert req.interaction_declaration is None

    def test_empty_interactions_list_is_valid(self):
        decl = InteractionDeclaration(interactions=[], first_order_effects={})
        req = _minimal_request(interaction_declaration=decl)
        assert req.interaction_declaration is not None
        assert req.interaction_declaration.interactions == []

    def test_duplicate_member_ids_rejected(self):
        with pytest.raises(ValidationError):
            InteractionDecl(
                id="I1",
                member_ids=["A1", "A1"],
                interaction_strength=Decimal("0.3"),
            )

    def test_single_member_rejected(self):
        with pytest.raises(ValidationError):
            InteractionDecl(
                id="I1",
                member_ids=["A1"],
                interaction_strength=Decimal("0.3"),
            )


# ═══════════════════════════════════════════════════════════════════════
# 2. invalidation_closure_with_interaction()
# ═══════════════════════════════════════════════════════════════════════

class TestCausalWithInteraction:
    def test_no_declaration_returns_none_interaction(self):
        req = _minimal_request()
        inv, aff, inter = invalidation_closure_with_interaction(req, "A1")
        assert "A1" in inv
        assert "S1" in aff
        assert inter is None

    def test_with_declaration_returns_interaction_result(self):
        decl = InteractionDeclaration(
            interactions=[
                InteractionDecl(
                    id="I1",
                    member_ids=["A1", "A2"],
                    interaction_strength=Decimal("0.5"),
                    effect_type=InteractionEffectType.CONJUNCTIVE,
                ),
            ],
            first_order_effects={"A1": Decimal("0.8"), "A2": Decimal("0.6")},
            amplification_ceiling=Decimal("2.0"),
        )
        # Make A2 depend on A1 so both fail together
        assumptions = [
            Assumption(
                id="A1",
                statement="Policy allows it",
                source=AssumptionSource.EXPLICIT,
                falsification_condition="policy review rejects",
                responsibility=_owner(),
            ),
            Assumption(
                id="A2",
                statement="Supply chain stable",
                source=AssumptionSource.EXPLICIT,
                falsification_condition="supplier outage",
                dependencies=["A1"],
                responsibility=_owner(),
            ),
        ]
        req = _minimal_request(assumptions=assumptions, interaction_declaration=decl)
        inv, aff, inter = invalidation_closure_with_interaction(req, "A1")

        assert set(inv) == {"A1", "A2"}
        assert "S1" in aff and "S2" in aff
        assert inter is not None
        assert isinstance(inter, InteractionPropagationResult)
        assert "I1" in inter.triggered_interaction_ids
        # first_order = 0.8 + 0.6 = 1.4; interaction +0.5; total = 1.9
        assert inter.first_order_sum == Decimal("1.4")
        assert inter.interaction_contribution == Decimal("0.5")
        assert inter.total_effect == Decimal("1.9")
        assert inter.ceiling_applied is False

    def test_single_failure_no_interaction_triggered(self):
        decl = InteractionDeclaration(
            interactions=[
                InteractionDecl(
                    id="I1",
                    member_ids=["A1", "A2"],
                    interaction_strength=Decimal("0.5"),
                ),
            ],
            first_order_effects={"A1": Decimal("0.8"), "A2": Decimal("0.6")},
        )
        req = _minimal_request(interaction_declaration=decl)
        # A1 fails alone, A2 still holds → no interaction triggered
        inv, aff, inter = invalidation_closure_with_interaction(req, "A1")
        assert inter is not None
        assert inter.triggered_interaction_ids == []
        assert inter.interaction_contribution == Decimal("0")
        assert inter.first_order_sum == Decimal("0.8")

    def test_disjunctive_interaction_negative_contribution(self):
        decl = InteractionDeclaration(
            interactions=[
                InteractionDecl(
                    id="I_red",
                    member_ids=["A1", "A2"],
                    interaction_strength=Decimal("-0.3"),
                    effect_type=InteractionEffectType.DISJUNCTIVE,
                ),
            ],
            first_order_effects={"A1": Decimal("0.8"), "A2": Decimal("0.6")},
            amplification_ceiling=Decimal("2.0"),
        )
        assumptions = [
            Assumption(
                id="A1",
                statement="A1",
                source=AssumptionSource.EXPLICIT,
                falsification_condition="f1",
                responsibility=_owner(),
            ),
            Assumption(
                id="A2",
                statement="A2",
                source=AssumptionSource.EXPLICIT,
                falsification_condition="f2",
                dependencies=["A1"],
                responsibility=_owner(),
            ),
        ]
        req = _minimal_request(assumptions=assumptions, interaction_declaration=decl)
        inv, aff, inter = invalidation_closure_with_interaction(req, "A1")
        assert inter is not None
        assert inter.interaction_contribution == Decimal("-0.3")
        # total = 1.4 + (-0.3) = 1.1
        assert inter.total_effect == Decimal("1.1")
        assert inter.ceiling_applied is False

    def test_ceiling_applied_in_propagation(self):
        # A3's large first-order effect lets the declaration pass I-3,
        # but when only A1+A2 fail, subset ceiling is lower.
        decl = InteractionDeclaration(
            interactions=[
                InteractionDecl(
                    id="I12",
                    member_ids=["A1", "A2"],
                    interaction_strength=Decimal("1.5"),
                ),
            ],
            first_order_effects={
                "A1": Decimal("0.3"),
                "A2": Decimal("0.3"),
                "A3": Decimal("2.0"),
            },
            amplification_ceiling=Decimal("2.0"),
        )
        assumptions = [
            Assumption(
                id=f"A{i}",
                statement=f"A{i}",
                source=AssumptionSource.EXPLICIT,
                falsification_condition=f"f{i}",
                responsibility=_owner(),
            )
            for i in range(1, 4)
        ]
        # A2 depends on A1, A3 independent
        assumptions[1].dependencies = ["A1"]
        alts = [
            Alternative(id=f"S{i}", name=f"Alt {i}", required_assumptions=[f"A{i}"])
            for i in range(1, 4)
        ]
        req = DecisionRequest(
            objective="test",
            decision_owner=_owner(),
            evaluation_mode=EvaluationMode.CONSTRAINT_ONLY,
            assumptions=assumptions,
            alternatives=alts,
            interaction_declaration=decl,
        )
        inv, aff, inter = invalidation_closure_with_interaction(req, "A1")
        assert inter is not None
        assert inter.ceiling_applied is True
        # subset first_order = 0.3 + 0.3 = 0.6; ceiling = 2.0 × 0.6 = 1.2
        # interaction clipped from 1.5 to 1.2
        assert inter.interaction_contribution == Decimal("1.2")
        assert inter.total_effect == Decimal("1.8")  # 0.6 + 1.2


# ═══════════════════════════════════════════════════════════════════════
# 3. Session stop-condition regression guard
# ═══════════════════════════════════════════════════════════════════════

class TestSessionStopConditionRegression:
    """After swapping _stop_condition to use ConvergenceChecker, these
    tests pin that the externally-visible behaviour hasn't changed."""

    def _engine(self) -> ReconstructionSessionEngine:
        return ReconstructionSessionEngine()

    def test_active_session_returns_awaiting_human(self):
        req = _minimal_request()
        engine = self._engine()
        session = engine.start(req, signals=[], max_iterations=5)
        # advance once — no delta vars, no hypotheses → should be awaiting
        session = engine.advance(session)
        assert session.status == SessionStatus.AWAITING_HUMAN
        assert session.convergence_kind is None

    def test_budget_exhausted_sets_budget_status(self):
        req = _minimal_request()
        engine = self._engine()
        session = engine.start(req, signals=[], max_iterations=1)
        # first advance consumes the only iteration budget
        session = engine.advance(session)
        assert session.status == SessionStatus.BUDGET_EXCEEDED
        assert session.convergence_kind is not None
        assert session.convergence_kind.value == "budget"

    def test_human_approval_seals_session(self):
        req = _minimal_request()
        engine = self._engine()
        session = engine.start(req, signals=[])
        session = engine.advance(session)
        sealed = engine.human_decision(session, approved=True)
        assert sealed.status == SessionStatus.SEALED
        assert sealed.sealed_at is not None

    def test_assumption_state_monotonicity(self):
        req = _minimal_request()
        engine = self._engine()
        session = engine.start(req, signals=[])
        session = engine.advance(session)
        # human marks A1 as verified
        updated = engine.human_decision(
            session,
            evidence_status={"A1": AssumptionState.VERIFIED},
        )
        assert updated.assumption_states["A1"] == AssumptionState.VERIFIED
        # can't go back to assumed
        again = engine.human_decision(
            updated,
            evidence_status={"A1": AssumptionState.ASSUMED},
        )
        assert again.assumption_states["A1"] == AssumptionState.VERIFIED
