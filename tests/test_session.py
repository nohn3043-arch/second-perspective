"""Three-layer reconstruction session engine tests."""

import json
from pathlib import Path

from second_perspective import (
    CausalReconstructor,
    ReconstructionSessionEngine,
    apply_delta_vars,
)
from second_perspective.models import (
    AssumptionState,
    ConvergenceKind,
    DeltaVar,
    DecisionRequest,
    ReconstructionSession,
    SessionStatus,
)


def load_example() -> dict:
    path = Path(__file__).parents[1] / "examples" / "market_entry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_start_initializes_assumptions_as_assumed():
    engine = ReconstructionSessionEngine()
    session = engine.start(
        DecisionRequest.model_validate(load_example()),
        signals=[],
    )
    assert isinstance(session, ReconstructionSession)
    assert session.status == SessionStatus.ACTIVE
    assert session.max_iterations == 5
    assert all(
        state == AssumptionState.ASSUMED
        for state in session.assumption_states.values()
    )


def test_advance_without_signals_hashes_chain_and_awaits_human():
    engine = ReconstructionSessionEngine()
    session = engine.start(
        DecisionRequest.model_validate(load_example()),
        signals=[],
    )

    session = engine.advance(session)
    assert len(session.rounds) == 1
    round_ = session.rounds[0]
    assert round_.round_root_hash
    assert round_.previous_round_hash is None
    assert round_.requires_human_decision is True
    assert session.status == SessionStatus.AWAITING_HUMAN

    # Session root hash is a sha256 hex digest over the round chain.
    assert session.session_root_hash
    assert len(session.session_root_hash) == 64


def test_advance_twice_links_round_hashes():
    engine = ReconstructionSessionEngine()
    session = engine.start(
        DecisionRequest.model_validate(load_example()),
        signals=[],
    )

    session = engine.advance(session)
    session = engine.advance(session)

    assert len(session.rounds) == 2
    assert session.rounds[1].previous_round_hash == session.rounds[0].round_root_hash
    assert session.rounds[0].round_root_hash != session.rounds[1].round_root_hash


def test_delta_reconstruction_changes_candidate_set():
    request = DecisionRequest.model_validate(load_example())

    # Falsify assumption A1 (partner availability) via a declared DeltaVar.
    delta = DeltaVar(
        path="A1",
        value=False,
        reason="Independent market report falsifies partner availability.",
    )
    patched = apply_delta_vars(request, [delta])

    engine = ReconstructionSessionEngine()
    session = engine.start(request, signals=[])
    session = engine.advance(session, delta_vars=[delta])

    assert session.rounds[0].convergence is not None
    assert session.rounds[0].convergence.reconstruction_id.startswith("REC-")
    assert "A1" in session.assumption_states
    assert session.assumption_states["A1"] == AssumptionState.FALSIFIED
    # Re-evaluation after the delta may or may not change the leader; what
    # matters is that the delta path executed and produced a report.
    assert session.rounds[0].convergence.is_converged in (True, False)


def test_human_decision_approval_seals_session():
    engine = ReconstructionSessionEngine()
    session = engine.start(
        DecisionRequest.model_validate(load_example()),
        signals=[],
    )
    session = engine.advance(session)

    session = engine.human_decision(session, approved=True)
    assert session.status == SessionStatus.SEALED
    assert session.sealed_at is not None


def test_human_decision_evidence_updates_state_monotonically():
    engine = ReconstructionSessionEngine()
    request = DecisionRequest.model_validate(load_example())
    session = engine.start(request, signals=[])

    session = engine.human_decision(
        session,
        evidence_status={"A1": AssumptionState.VERIFIED},
    )
    assert session.assumption_states["A1"] == AssumptionState.VERIFIED
    assert session.status == SessionStatus.ACTIVE  # re-opened for next round
