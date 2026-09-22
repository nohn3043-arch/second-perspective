"""Tests for the LLM compliance layer (v0.4 upgrade — G3).

Covers:
  - PermissionTier ordering
  - GuardViolationError
  - Provenance & prompt fingerprinting
  - LLMGate: zone isolation (L-1)
  - LLMGate: no adjudication (L-1)
  - LLMGate: strength stripping (L-2)
  - LLMGate: provenance requirement (L-3)
  - LLMGate: unknown assumption reference filtering
  - Demo guards from the upgrade doc
"""

import pytest

from second_perspective.llm_compliance import (
    GuardViolationError,
    GuardViolationSeverity,
    LLMGate,
    LLMOutput,
    PermissionTier,
    Provenance,
    make_prompt_fingerprint,
)


# ── types.py ──────────────────────────────────────────────────────────


class TestPermissionTier:
    def test_tier_ordering(self):
        assert PermissionTier.T1_ANNOTATION.rank == 1
        assert PermissionTier.T2_PROPOSAL.rank == 2
        assert PermissionTier.T3_NARRATIVE.rank == 3

    def test_permits_lower_or_equal(self):
        assert PermissionTier.T3_NARRATIVE.permits(PermissionTier.T1_ANNOTATION)
        assert PermissionTier.T3_NARRATIVE.permits(PermissionTier.T2_PROPOSAL)
        assert PermissionTier.T3_NARRATIVE.permits(PermissionTier.T3_NARRATIVE)

    def test_does_not_permit_higher(self):
        assert not PermissionTier.T1_ANNOTATION.permits(PermissionTier.T2_PROPOSAL)
        assert not PermissionTier.T2_PROPOSAL.permits(PermissionTier.T3_NARRATIVE)


class TestGuardViolationError:
    def test_attributes(self):
        err = GuardViolationError("L-1", GuardViolationSeverity.CRITICAL, "test reason")
        assert err.rule == "L-1"
        assert err.severity == GuardViolationSeverity.CRITICAL
        assert err.detail == "test reason"
        assert "L-1" in str(err)
        assert "critical" in str(err)


# ── provenance.py ─────────────────────────────────────────────────────


class TestProvenance:
    def test_requires_model(self):
        with pytest.raises(ValueError, match="model must not be empty"):
            Provenance(model="")

    def test_default_timestamp(self):
        p = Provenance(model="test-model")
        assert p.timestamp > 0

    def test_short_fingerprint(self):
        p = Provenance(model="test", prompt_fingerprint="a" * 64)
        assert len(p.short_fingerprint) == 12
        assert p.short_fingerprint == "a" * 12

    def test_short_fingerprint_empty_when_no_fingerprint(self):
        p = Provenance(model="test")
        assert p.short_fingerprint == ""


class TestMakePromptFingerprint:
    def test_deterministic(self):
        h1 = make_prompt_fingerprint("hello world")
        h2 = make_prompt_fingerprint("hello world")
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        h1 = make_prompt_fingerprint("hello")
        h2 = make_prompt_fingerprint("world")
        assert h1 != h2

    def test_line_ending_normalization(self):
        h_unix = make_prompt_fingerprint("line1\nline2")
        h_dos = make_prompt_fingerprint("line1\r\nline2")
        h_oldmac = make_prompt_fingerprint("line1\rline2")
        assert h_unix == h_dos == h_oldmac

    def test_is_hex_string(self):
        h = make_prompt_fingerprint("test")
        assert len(h) == 64
        int(h, 16)  # should not raise


# ── guard.py ──────────────────────────────────────────────────────────


class TestLLMGateL3Provenance:
    """L-3: T2+ output must carry provenance."""

    def test_t1_without_provenance_passes(self):
        gate = LLMGate()
        output = LLMOutput(
            content="some annotation",
            tier=PermissionTier.T1_ANNOTATION,
        )
        result = gate.process(output)
        assert result.content == "some annotation"

    def test_t2_without_provenance_rejected(self):
        gate = LLMGate()
        output = LLMOutput(
            content="proposed interaction: A1+A2",
            tier=PermissionTier.T2_PROPOSAL,
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.rule == "L-3"
        assert exc.value.severity == GuardViolationSeverity.HIGH

    def test_t3_without_provenance_rejected(self):
        gate = LLMGate()
        output = LLMOutput(
            content="explanation of the result",
            tier=PermissionTier.T3_NARRATIVE,
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.rule == "L-3"

    def test_t2_with_provenance_passes(self):
        gate = LLMGate()
        prov = Provenance(model="gpt-4o", prompt_fingerprint=make_prompt_fingerprint("hi"))
        output = LLMOutput(
            content="proposed interaction: A1+A2",
            tier=PermissionTier.T2_PROPOSAL,
            provenance=prov,
            zone="proposal",
        )
        result = gate.process(output)
        assert result.provenance is prov


class TestLLMGateL1ZoneIsolation:
    """L-1 part A: zone isolation — LLM output must not leak into decision zones."""

    def test_decision_zone_rejected(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="this should not be here",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
            zone="convergence",
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.rule == "L-1"
        assert exc.value.severity == GuardViolationSeverity.CRITICAL

    def test_narrative_zone_accepted(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        for zone in ("narrative", "explanation", "summary", "annotation"):
            output = LLMOutput(
                content="explanation text",
                tier=PermissionTier.T3_NARRATIVE,
                provenance=prov,
                zone=zone,
            )
            result = gate.process(output)
            assert result.zone == zone

    def test_proposal_zone_accepted_for_t2(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="proposal text",
            tier=PermissionTier.T2_PROPOSAL,
            provenance=prov,
            zone="proposal",
        )
        result = gate.process(output)
        assert result.zone == "proposal"

    def test_unknown_zone_medium_severity(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="text",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
            zone="mystery_zone",
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.rule == "L-1"
        assert exc.value.severity == GuardViolationSeverity.MEDIUM


class TestLLMGateL1NoAdjudication:
    """L-1 part B: LLM output must not contain verdicts / convergence / scoring."""

    def test_converged_keyword_rejected(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="The result is converged: true",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.rule == "L-1"
        assert exc.value.severity == GuardViolationSeverity.CRITICAL

    def test_overall_assessment_rejected(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="overall_assessment: high risk",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
        )
        with pytest.raises(GuardViolationError):
            gate.process(output)

    def test_bias_flags_rejected(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="bias_flag: confirmation_bias",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
        )
        with pytest.raises(GuardViolationError):
            gate.process(output)

    def test_score_numeric_rejected(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="score: 85 out of 100",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
        )
        with pytest.raises(GuardViolationError):
            gate.process(output)

    def test_structured_converged_key_rejected(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
            structured={"converged": True, "reason": "fixed point"},
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.rule == "L-1"
        assert "forbidden key" in exc.value.detail

    def test_structured_nested_forbidden_key(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
            structured={
                "analysis": {
                    "deep": {
                        "decision": "approve",
                    }
                }
            },
        )
        with pytest.raises(GuardViolationError):
            gate.process(output)

    def test_narrative_without_verdict_passes(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="The evaluation considered three alternatives and found that "
                    "the leading candidate satisfies all hard constraints.",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
        )
        result = gate.process(output)
        assert result is not None


class TestLLMGateL2StrengthStripping:
    """L-2: LLM-proposed interactions must have empty strength."""

    def test_t2_proposal_strips_strength_from_text(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="Proposed interaction: A1+A2, interaction_strength: 0.75",
            tier=PermissionTier.T2_PROPOSAL,
            provenance=prov,
            zone="proposal",
        )
        result = gate.process(output)
        assert "0.75" not in result.content
        assert "null" in result.content

    def test_t2_proposal_strips_delta(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="Strength: 0.5",
            tier=PermissionTier.T2_PROPOSAL,
            provenance=prov,
            zone="proposal",
        )
        result = gate.process(output)
        assert "0.5" not in result.content

    def test_t2_structured_strips_strength(self):
        gate = LLMGate()
        prov = Provenance(model="test")
        output = LLMOutput(
            content="",
            tier=PermissionTier.T2_PROPOSAL,
            provenance=prov,
            zone="proposal",
            structured={
                "interactions": [
                    {
                        "id": "I1",
                        "member_ids": ["A1", "A2"],
                        "interaction_strength": 0.75,
                    }
                ]
            },
        )
        result = gate.process(output)
        assert result.structured is not None
        assert result.structured["interactions"][0]["interaction_strength"] is None

    def test_t3_narrative_does_not_strip(self):
        """T3 is for explanations — strength stripping is only for T2 proposals."""
        gate = LLMGate()
        prov = Provenance(model="test")
        text = "The interaction strength was declared as 0.75 by the reviewer."
        output = LLMOutput(
            content=text,
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
        )
        result = gate.process(output)
        # T3 doesn't strip — this is narrative about someone else's declaration
        assert "0.75" in result.content


class TestLLMGateAssumptionRefFiltering:
    """T1/T2: filter references to unknown assumptions."""

    def test_t2_filters_unknown_assumption_ids(self):
        gate = LLMGate(known_assumption_ids={"A1", "A2"})
        prov = Provenance(model="test")
        output = LLMOutput(
            content="",
            tier=PermissionTier.T2_PROPOSAL,
            provenance=prov,
            zone="proposal",
            structured={
                "interactions": [
                    {
                        "id": "I1",
                        "member_ids": ["A1", "A9"],  # A9 unknown
                    }
                ]
            },
        )
        result = gate.process(output)
        assert result.structured is not None
        members = result.structured["interactions"][0]["member_ids"]
        assert "A1" in members
        assert "A9" not in members

    def test_t3_does_not_filter_refs(self):
        """T3 is narrative — no assumption reference validation needed."""
        gate = LLMGate(known_assumption_ids={"A1"})
        prov = Provenance(model="test")
        output = LLMOutput(
            content="The analysis mentions A9 which may not exist.",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
        )
        result = gate.process(output)
        assert "A9" in result.content  # not stripped in T3 narrative


class TestLLMGateAllowedTiers:
    def test_tier_not_in_allowed_set_rejected(self):
        gate = LLMGate(allowed_tiers={PermissionTier.T1_ANNOTATION})
        output = LLMOutput(
            content="some T3 narrative",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=Provenance(model="test"),
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.rule == "L-1"
        assert exc.value.severity == GuardViolationSeverity.CRITICAL

    def test_tier_in_allowed_set_passes(self):
        gate = LLMGate(allowed_tiers={PermissionTier.T1_ANNOTATION, PermissionTier.T2_PROPOSAL})
        prov = Provenance(model="test")
        output = LLMOutput(
            content="annotation text",
            tier=PermissionTier.T1_ANNOTATION,
            provenance=prov,
            zone="annotation",
        )
        result = gate.process(output)
        assert result is not None


# ── demo guards from the upgrade doc ──────────────────────────────────


class TestDemoGuards:
    """The four demo guard scenarios from the upgrade document."""

    def _make_gate(self):
        return LLMGate(
            allowed_tiers={
                PermissionTier.T1_ANNOTATION,
                PermissionTier.T2_PROPOSAL,
                PermissionTier.T3_NARRATIVE,
            },
            known_assumption_ids={"A1", "A2"},
        )

    def test_guard_1_unknown_assumption_discarded(self):
        """[1] LLM mentions nonexistent assumption A9 → A9 dropped ✅"""
        gate = self._make_gate()
        prov = Provenance(model="test-model")
        output = LLMOutput(
            content="",
            tier=PermissionTier.T2_PROPOSAL,
            provenance=prov,
            zone="proposal",
            structured={
                "interactions": [
                    {"id": "I1", "member_ids": ["A1", "A9"]},
                ]
            },
        )
        result = gate.process(output)
        members = result.structured["interactions"][0]["member_ids"]
        assert "A9" not in members
        assert "A1" in members

    def test_guard_2_strength_stripped(self):
        """[2] LLM tries to give strength 0.75 → strength forced null, narrative stripped of numbers ✅"""
        gate = self._make_gate()
        prov = Provenance(model="test-model")
        output = LLMOutput(
            content="interaction_strength: 0.75",
            tier=PermissionTier.T2_PROPOSAL,
            provenance=prov,
            zone="proposal",
            structured={
                "interactions": [
                    {"id": "I1", "member_ids": ["A1", "A2"], "interaction_strength": 0.75},
                ]
            },
        )
        result = gate.process(output)
        assert "0.75" not in result.content
        assert result.structured["interactions"][0]["interaction_strength"] is None

    def test_guard_3_convergence_verdict_blocked(self):
        """[3] LLM performs convergence judgement → GuardViolationError, severe=critical ✅"""
        gate = self._make_gate()
        prov = Provenance(model="test-model")
        output = LLMOutput(
            content="converged: true",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.severity == GuardViolationSeverity.CRITICAL

    def test_guard_4_zone_injection_detected(self):
        """[4] LLM sneaks into analysis zone → zone check catches it ✅"""
        gate = self._make_gate()
        prov = Provenance(model="test-model")
        output = LLMOutput(
            content="analysis text that should be in narrative",
            tier=PermissionTier.T3_NARRATIVE,
            provenance=prov,
            zone="analysis",
        )
        with pytest.raises(GuardViolationError) as exc:
            gate.process(output)
        assert exc.value.rule == "L-1"
        assert "Unknown output zone" in exc.value.detail
