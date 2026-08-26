"""Cognitive risk scanner — structured challenge layer backed by GCAE.

This module wraps the vendored SPL/GCAE five-operator cognitive audit engine
(NS/IAP/LCH/CCS/STATE) behind NOMOS typed models.  It does NOT diagnose
people, read motives, or replace human judgment.  Every finding is derived
deterministically from declared inputs and the decision structure.

The raw GCAE audit dictionary is preserved on the returned report so that
callers that want the full operator-level output (e.g. bilingual report
rendering) can use it directly.
"""

from __future__ import annotations

from typing import Any

from ..audit.cognitive.adapter import run_gcae_audit
from ..models.schemas import CognitiveAuditReport, DecisionRequest, DecisionResult


class CognitiveRiskScanner:
    """Deterministic structural cognitive-risk scanner (GCAE-backed).

    Wraps the five-operator SPL/GCAE pipeline:
        NS   — narrative strip (rhetoric/emotion/moral veneer)
        IAP  — implicit assumption perspective (unstated premises)
        LCH  — fragility latch (weakest variable, Delta D)
        CCS  — causal-chain sync (inverse / counterfactual / integrity)
        STATE — responsibility anchor + final verdict
    """

    SCANNER_VERSION = "GCAE-1.0.0"

    def __init__(self, policy: Any) -> None:
        self.policy = policy

    def scan(self, request: DecisionRequest, result: DecisionResult) -> CognitiveAuditReport:
        """Run the GCAE five-operator audit and return a NOMOS CognitiveAuditReport."""
        report, _raw = run_gcae_audit(request, result, self.policy)
        return report