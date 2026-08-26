"""
GCAE — Second Perspective Language Cognitive Audit Engine (vendored)
=====================================================================

Vendored from the `second-perspective` Cognitive Audit Engine (SPL/GCAE).

This is the five-operator deterministic causal-audit pipeline:
    NS    Narrative Strip        — strip rhetoric/emotion/moral veneer
    IAP   Implicit Assumption    — surface unstated premises
    LCH   Latch / Fragility      — locate weakest variable, compute Delta D
    CCS   Causal-Chain Sync      — counterfactual & inverse-check
    STATE State Anchor           — pin responsibility + final verdict

The engine itself is a pure-Python, zero-dependency, fully deterministic
audit pipeline. No RNG, no LLM calls by default. An optional LLM provider
can be attached via :meth:`CognitiveAuditEngine.set_llm_provider`.

For usage in NOMOS, prefer the :class:`CognitiveRiskScanner` adapter in
:mod:`second_perspective.audit.cognitive.adapter`, which bridges the
typed :class:`~second_perspective.models.schemas.DecisionRequest` /
:class:`~second_perspective.models.schemas.DecisionResult` models to the
dict-based context expected by the GCAE engine.

Reference: second-perspective/Cognitive Audit Engine.py
"""

from .engine import CognitiveAuditEngine, ResponsibilityAccount, AuditConfigLoader, AuditPlugin
from .plugins import (
    CORE_PLUGINS,
    NarrativeStripPlugin,
    ImplicitAssumptionPlugin,
    FragilityLatchPlugin,
    CausalChainSyncPlugin,
    StateAnchorPlugin,
    ReportRenderer,
)

__all__ = [
    "CognitiveAuditEngine",
    "ResponsibilityAccount",
    "AuditConfigLoader",
    "AuditPlugin",
    "CORE_PLUGINS",
    "NarrativeStripPlugin",
    "ImplicitAssumptionPlugin",
    "FragilityLatchPlugin",
    "CausalChainSyncPlugin",
    "StateAnchorPlugin",
    "ReportRenderer",
]