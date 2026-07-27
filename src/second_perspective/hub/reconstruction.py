"""Hub integration layer for causal reconstruction.

Bridges the CausalReconstructor engine with the Hub orchestration layer.
When the Hub receives deviation_signals, this module invokes the
reconstruction engine and returns a sealed CausalReconstructionReport.
"""

from __future__ import annotations

from ..decision.reconstruction import CausalReconstructor
from ..models.schemas import CausalReconstructionReport, DecisionRequest, DeviationSignal


def run_causal_reconstruction(
    request: DecisionRequest,
    signals: list[DeviationSignal],
) -> CausalReconstructionReport | None:
    """Entry point called by the IntelligentDecisionHub.

    Returns None (not an error) when there is nothing to reconstruct —
    e.g. no assumptions declared in the request, or no signals provided.
    This lets the Hub treat reconstruction as an optional diagnostic layer.
    """
    if not signals:
        return None
    if not request.assumptions:
        return None

    engine = CausalReconstructor()
    return engine.reconstruct(request, signals)
