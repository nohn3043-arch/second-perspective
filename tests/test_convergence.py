"""Tests for the convergence formalization layer (v0.4 upgrade — G2).

Covers:
  - ConvergenceStatus enum properties
  - ConvergenceResult convenience methods
  - All three propositions (P-1, P-2, P-3)
  - ConvergenceChecker: five-state classification
  - is_true_convergence guard function
"""

import pytest

from second_perspective.convergence import (
    ConvergenceChecker,
    ConvergenceResult,
    ConvergenceStatus,
    proposition_effect_boundedness,
    proposition_fixed_point,
    proposition_termination,
)


# ── types.py ──────────────────────────────────────────────────────────


class TestConvergenceStatus:
    def test_true_convergence_states(self):
        assert ConvergenceStatus.FIXED_POINT.is_true_convergence
        assert ConvergenceStatus.NO_GAIN.is_true_convergence

    def test_non_convergence_states(self):
        assert not ConvergenceStatus.BUDGET_EXHAUSTED.is_true_convergence
        assert not ConvergenceStatus.DIVERGED.is_true_convergence
        assert not ConvergenceStatus.BLOCKED.is_true_convergence

    def test_requires_human_states(self):
        assert ConvergenceStatus.BUDGET_EXHAUSTED.requires_human
        assert ConvergenceStatus.BLOCKED.requires_human

    def test_no_human_needed_states(self):
        assert not ConvergenceStatus.FIXED_POINT.requires_human
        assert not ConvergenceStatus.NO_GAIN.requires_human
        assert not ConvergenceStatus.DIVERGED.requires_human

    def test_terminal_states(self):
        assert ConvergenceStatus.FIXED_POINT.is_terminal
        assert ConvergenceStatus.NO_GAIN.is_terminal
        assert ConvergenceStatus.BUDGET_EXHAUSTED.is_terminal
        assert ConvergenceStatus.BLOCKED.is_terminal
        assert not ConvergenceStatus.DIVERGED.is_terminal

    def test_str_values_are_stable(self):
        # Enum values are part of the public API — changing them breaks clients.
        assert ConvergenceStatus.FIXED_POINT.value == "fixed_point"
        assert ConvergenceStatus.NO_GAIN.value == "no_gain"
        assert ConvergenceStatus.BUDGET_EXHAUSTED.value == "budget_exhausted"
        assert ConvergenceStatus.DIVERGED.value == "diverged"
        assert ConvergenceStatus.BLOCKED.value == "blocked"


class TestConvergenceResult:
    def test_is_true_convergence_mirrors_status(self):
        r = ConvergenceResult(
            status=ConvergenceStatus.FIXED_POINT, round_index=3,
        )
        assert r.is_true_convergence

    def test_requires_human_mirrors_status(self):
        r = ConvergenceResult(
            status=ConvergenceStatus.BUDGET_EXHAUSTED, round_index=5,
        )
        assert r.requires_human

    def test_is_terminal_mirrors_status(self):
        r = ConvergenceResult(
            status=ConvergenceStatus.DIVERGED, round_index=1,
        )
        assert not r.is_terminal


# ── propositions.py ───────────────────────────────────────────────────


class TestPropositionTermination:
    def test_positive_budgets_hold(self):
        ok, reason = proposition_termination(max_iterations=10, max_evidence_requests=5)
        assert ok
        assert "finite" in reason.lower()

    def test_zero_iterations_rejected(self):
        ok, _ = proposition_termination(max_iterations=0, max_evidence_requests=5)
        assert not ok

    def test_negative_iterations_rejected(self):
        ok, _ = proposition_termination(max_iterations=-3, max_evidence_requests=5)
        assert not ok

    def test_zero_evidence_requests_ok(self):
        # 0 evidence requests is allowed (no evidence-gathering phase)
        ok, _ = proposition_termination(max_iterations=10, max_evidence_requests=0)
        assert ok

    def test_non_int_rejected(self):
        ok, _ = proposition_termination(max_iterations=10.5, max_evidence_requests=5)  # type: ignore
        assert not ok


class TestPropositionFixedPoint:
    def test_identical_sets_is_fixed_point(self):
        ok, reason = proposition_fixed_point({"S1", "S2"}, {"S1", "S2"})
        assert ok
        assert "fixed point" in reason.lower()

    def test_different_sets_not_fixed_point(self):
        ok, reason = proposition_fixed_point({"S1"}, {"S1", "S2"})
        assert not ok
        assert "changed" in reason.lower()

    def test_empty_sets_is_fixed_point(self):
        ok, _ = proposition_fixed_point(set(), set())
        assert ok

    def test_order_independent(self):
        prev = ["S1", "S2", "S3"]
        curr = ["S3", "S1", "S2"]
        ok, _ = proposition_fixed_point(prev, curr)
        assert ok

    def test_single_member_change_detected(self):
        ok, reason = proposition_fixed_point({"S1", "S2"}, {"S1", "S3"})
        assert not ok
        assert "+['S3']" in reason
        assert "-['S2']" in reason


class TestPropositionEffectBoundedness:
    def test_within_ceiling_holds(self):
        ok, reason = proposition_effect_boundedness(
            first_order_sum_abs=1.4,
            interaction_amplifying_sum=2.0,
            ceiling_multiplier=2.0,
        )
        assert ok  # 2.0 ≤ 2.8
        assert "≤" in reason

    def test_at_ceiling_holds(self):
        ok, _ = proposition_effect_boundedness(
            first_order_sum_abs=1.0,
            interaction_amplifying_sum=2.0,
            ceiling_multiplier=2.0,
        )
        assert ok  # exactly at ceiling

    def test_exceeds_ceiling_fails(self):
        ok, reason = proposition_effect_boundedness(
            first_order_sum_abs=1.0,
            interaction_amplifying_sum=3.0,
            ceiling_multiplier=2.0,
        )
        assert not ok
        assert "EXCEEDS" in reason

    def test_negative_first_order_rejected(self):
        ok, _ = proposition_effect_boundedness(
            first_order_sum_abs=-0.5,
            interaction_amplifying_sum=0.5,
            ceiling_multiplier=2.0,
        )
        assert not ok

    def test_subone_ceiling_rejected(self):
        ok, _ = proposition_effect_boundedness(
            first_order_sum_abs=1.0,
            interaction_amplifying_sum=0.5,
            ceiling_multiplier=0.5,
        )
        assert not ok

    def test_zero_interaction_holds(self):
        ok, _ = proposition_effect_boundedness(
            first_order_sum_abs=1.0,
            interaction_amplifying_sum=0.0,
            ceiling_multiplier=1.0,
        )
        assert ok


# ── checker.py ────────────────────────────────────────────────────────


class TestConvergenceChecker:
    def _make_checker(self, max_iter=10, max_evidence=5):
        return ConvergenceChecker(
            max_iterations=max_iter,
            max_evidence_requests=max_evidence,
        )

    def test_constructor_rejects_invalid_budgets(self):
        with pytest.raises(ValueError):
            ConvergenceChecker(max_iterations=0, max_evidence_requests=5)

    # -- fixed point (highest convergence priority) --------------------

    def test_fixed_point_when_candidates_identical(self):
        checker = self._make_checker()
        result = checker.evaluate(
            round_index=2,
            candidate_set_prev={"S1", "S2"},
            candidate_set_curr={"S1", "S2"},
            iterations_used=3,
            evidence_requests_used=1,
            unresolved_branches=2,
        )
        assert result.status == ConvergenceStatus.FIXED_POINT
        assert result.is_true_convergence
        assert not result.requires_human

    def test_fixed_point_even_with_budget_remaining(self):
        """Fixed point takes priority over budget — if we've converged,
        remaining budget doesn't matter."""
        checker = self._make_checker(max_iter=10)
        result = checker.evaluate(
            round_index=1,
            candidate_set_prev={"S1"},
            candidate_set_curr={"S1"},
            iterations_used=1,
            evidence_requests_used=0,
            unresolved_branches=0,
        )
        assert result.status == ConvergenceStatus.FIXED_POINT

    # -- no gain -------------------------------------------------------

    def test_no_gain_when_no_branches_and_changing(self):
        """NO_GAIN: candidates still changing but no unresolved branches left."""
        checker = self._make_checker()
        result = checker.evaluate(
            round_index=3,
            candidate_set_prev={"S1", "S2"},
            candidate_set_curr={"S1"},
            iterations_used=3,
            evidence_requests_used=2,
            unresolved_branches=0,
        )
        assert result.status == ConvergenceStatus.NO_GAIN
        assert result.is_true_convergence

    # -- budget exhausted ----------------------------------------------

    def test_budget_exhausted_iterations(self):
        checker = self._make_checker(max_iter=5)
        result = checker.evaluate(
            round_index=5,
            candidate_set_prev={"S1"},
            candidate_set_curr={"S1", "S2"},
            iterations_used=5,
            evidence_requests_used=1,
            unresolved_branches=3,
        )
        assert result.status == ConvergenceStatus.BUDGET_EXHAUSTED
        assert not result.is_true_convergence
        assert result.requires_human

    def test_budget_exhausted_evidence(self):
        checker = self._make_checker(max_evidence=2)
        result = checker.evaluate(
            round_index=3,
            candidate_set_prev={"S1"},
            candidate_set_curr={"S1", "S2", "S3"},
            iterations_used=3,
            evidence_requests_used=2,
            unresolved_branches=5,
        )
        assert result.status == ConvergenceStatus.BUDGET_EXHAUSTED

    def test_budget_exhausted_not_true_convergence(self):
        """Critical guard: budget exhaustion must NEVER be classified as convergence."""
        checker = self._make_checker(max_iter=5)
        result = checker.evaluate(
            round_index=5,
            candidate_set_prev={"S1"},
            candidate_set_curr={"S2"},
            iterations_used=5,
            evidence_requests_used=0,
            unresolved_branches=10,
        )
        assert result.status == ConvergenceStatus.BUDGET_EXHAUSTED
        assert not result.is_true_convergence

    def test_fixed_point_at_budget_is_still_fixed_point(self):
        """If we hit budget AND have a fixed point, FIXED_POINT wins —
        we did converge, we just happened to also run out of budget."""
        checker = self._make_checker(max_iter=3)
        result = checker.evaluate(
            round_index=3,
            candidate_set_prev={"S1"},
            candidate_set_curr={"S1"},
            iterations_used=3,
            evidence_requests_used=0,
            unresolved_branches=0,
        )
        assert result.status == ConvergenceStatus.FIXED_POINT
        assert result.is_true_convergence

    # -- blocked -------------------------------------------------------

    def test_blocked_has_highest_priority(self):
        checker = self._make_checker()
        result = checker.evaluate(
            round_index=1,
            candidate_set_prev=set(),
            candidate_set_curr={"S1"},
            iterations_used=1,
            evidence_requests_used=0,
            unresolved_branches=5,
            blocked=True,
            blocking_reasons=["structural integrity failure"],
        )
        assert result.status == ConvergenceStatus.BLOCKED
        assert result.requires_human
        assert result.blocked
        assert "structural integrity failure" in result.blocking_reasons

    # -- diverged ------------------------------------------------------

    def test_diverged_when_still_changing_with_budget(self):
        checker = self._make_checker()
        result = checker.evaluate(
            round_index=2,
            candidate_set_prev={"S1"},
            candidate_set_curr={"S1", "S2"},
            iterations_used=2,
            evidence_requests_used=1,
            unresolved_branches=3,
        )
        assert result.status == ConvergenceStatus.DIVERGED
        assert not result.is_terminal
        assert not result.requires_human

    # -- is_true_convenience ------------------------------------------

    def test_is_true_convergence_shorthand_true(self):
        checker = self._make_checker()
        assert checker.is_true_convergence(
            round_index=2,
            candidate_set_prev={"S1"},
            candidate_set_curr={"S1"},
            iterations_used=2,
            evidence_requests_used=1,
        )

    def test_is_true_convergence_shorthand_false_for_budget(self):
        checker = self._make_checker(max_iter=2)
        assert not checker.is_true_convergence(
            round_index=2,
            candidate_set_prev={"S1"},
            candidate_set_curr={"S2"},
            iterations_used=2,
            evidence_requests_used=0,
            unresolved_branches=5,
        )

    def test_preserves_budget_values_in_result(self):
        checker = self._make_checker(max_iter=10, max_evidence=6)
        result = checker.evaluate(
            round_index=4,
            candidate_set_prev=set(),
            candidate_set_curr={"S1"},
            iterations_used=4,
            evidence_requests_used=2,
            unresolved_branches=1,
        )
        assert result.iterations_used == 4
        assert result.iterations_max == 10
        assert result.evidence_requests_used == 2
        assert result.evidence_requests_max == 6
        assert result.round_index == 4
