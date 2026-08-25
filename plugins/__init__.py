"""
SPL Core Audit Plugins — Official Five-Operator Pack
=====================================================

This package contains the five core audit operators that form the
deterministic causal-audit pipeline of the Second Perspective Language:

    NS    Narrative Strip        — strip rhetoric/emotion/moral veneer
    IAP   Implicit Assumption    — surface unstated premises
    LCH   Latch / Fragility      — locate weakest variable, compute Delta D
    CCS   Causal-Chain Sync     — counterfactual & inverse-check
    STATE State Anchor           — pin responsibility + final verdict

All plugins are pure-Python, zero-dependency, deterministic (no RNG,
no LLM calls).  They are auto-loaded by CognitiveAuditEngine when
``engine.load_core_plugins()`` is called.

Copyright (c) 2026 Shanghai Linming Junhua Technology Co., Ltd.
              and NOHN AI TECHNOLOGY PTE. LTD.
All rights reserved.  Dual-track license — see ../LICENSE.
"""

from .ns   import NarrativeStripPlugin
from .iap  import ImplicitAssumptionPlugin
from .lch  import FragilityLatchPlugin
from .ccs  import CausalChainSyncPlugin
from .state import StateAnchorPlugin
from .report import ReportRenderer

CORE_PLUGINS = [
    NarrativeStripPlugin,
    ImplicitAssumptionPlugin,
    FragilityLatchPlugin,
    CausalChainSyncPlugin,
    StateAnchorPlugin,
]

__all__ = [
    "CORE_PLUGINS",
    "NarrativeStripPlugin",
    "ImplicitAssumptionPlugin",
    "FragilityLatchPlugin",
    "CausalChainSyncPlugin",
    "StateAnchorPlugin",
    "ReportRenderer",
]
