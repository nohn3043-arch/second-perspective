"""ReconstructionSessionEngine coverage — start / advance / human_decision / stop."""

from datetime import datetime, timezone

from second_perspective.hub.session import ReconstructionSessionEngine
from second_perspective.models.enums import (
    AssumptionState,
    SessionStatus,
)
from second_perspective.models.schemas import DeviationSignal, DeltaVar

TZ = timezone.utc


def _signal(metric: str = "metric_K1") -> DeviationSignal:
    return DeviationSignal(
        metric=metric,
        observed=40,
        baseline=80,
        direction="below",
        observed_at=datetime(2026, 2, 1, tzinfo=TZ),
        source="pipeline-obs-1",
    )


def test_start_creates_active_session(make_request):
    engine = ReconstructionSessionEngine()
    request = make_request()
    session = engine.start(request, [_signal()])
    assert session.session_id.startswith("SESS-")
    assert session.status == SessionStatus.ACTIVE
    assert session.rounds == []
    assert set(session.assumption_states) == {a.id for a in request.assumptions}
    assert all(s == AssumptionState.ASSUMED for s in session.assumption_states.values())
    assert session.max_iterations == 5
    assert session.max_evidence_requests == 20


def test_start_respects_budgets(make_request):
    engine = ReconstructionSessionEngine()
    session = engine.start(
        make_request(), [], max_iterations=2, max_evidence_requests=3
    )
    assert session.max_iterations == 2
    assert session.max_evidence_requests == 3


def test_advance_adds_round_and_hash_chain(make_request):
    engine = ReconstructionSessionEngine()
    session = engine.start(make_request(), [_signal()])
    assert session.session_root_hash is None
    updated = engine.advance(session)
    assert len(updated.rounds) == 1
    round_ = updated.rounds[0]
    assert round_.round_index == 0
    assert round_.round_root_hash and len(round_.round_root_hash) == 64
    assert round_.previous_round_hash is None
    assert updated.session_root_hash and len(updated.session_root_hash) == 64
    assert updated.status in (SessionStatus.AWAITING_HUMAN, SessionStatus.CONVERGED)


def test_advance_second_round_links_hash_chain(make_request):
    engine = ReconstructionSessionEngine()
    session = engine.start(make_request(), [_signal()])
    r1 = engine.advance(session)
    r2 = engine.advance(r1)
    assert len(r2.rounds) == 2
    assert r2.rounds[1].previous_round_hash == r1.rounds[0].round_root_hash
    assert r2.rounds[1].round_root_hash != r1.rounds[0].round_root_hash


def test_human_decision_without_approval_reopens(make_request):
    engine = ReconstructionSessionEngine()
    session = engine.start(make_request(), [_signal()])
    updated = engine.human_decision(session, approved=False)
    assert updated.status == SessionStatus.ACTIVE
    assert updated.session_root_hash == session.session_root_hash  # no new rounds yet


def test_human_decision_approval_seals(make_request):
    engine = ReconstructionSessionEngine()
    session = engine.start(make_request(), [_signal()])
    updated = engine.human_decision(session, approved=True)
    assert updated.status == SessionStatus.SEALED
    assert updated.sealed_at is not None
    assert updated.session_root_hash is not None


def test_human_decision_advances_assumption_states(make_request):
    engine = ReconstructionSessionEngine()
    request = make_request()  # A1 exists by default
    session = engine.start(request, [_signal()])
    updated = engine.human_decision(
        session,
        evidence_status={"A1": AssumptionState.VERIFIED},
    )
    assert updated.assumption_states["A1"] == AssumptionState.VERIFIED


def test_human_decision_ignores_unknown_assumption(make_request):
    engine = ReconstructionSessionEngine()
    session = engine.start(make_request(), [_signal()])
    updated = engine.human_decision(
        session,
        evidence_status={"A99": AssumptionState.VERIFIED},
    )
    assert "A99" not in updated.assumption_states
    assert updated.status == SessionStatus.ACTIVE


def test_human_decision_sealed_session_is_noop(make_request):
    engine = ReconstructionSessionEngine()
    session = engine.start(make_request(), [_signal()])
    sealed = engine.human_decision(session, approved=True)
    again = engine.human_decision(sealed, approved=True)
    assert again.status == SessionStatus.SEALED


def test_advance_with_delta_vars_marks_delta_kind(make_request):
    engine = ReconstructionSessionEngine()
    session = engine.start(make_request(), [_signal()])
    delta = DeltaVar(
        path="criteria.K1.weight",
        value="0.9",
        reason="human overrides weight",
    )
    updated = engine.advance(session, [delta])
    assert len(updated.rounds) == 1
    assert updated.rounds[0].applied_delta_vars == [delta]
    assert updated.status in (
        SessionStatus.AWAITING_HUMAN,
        SessionStatus.CONVERGED,
        SessionStatus.BUDGET_EXCEEDED,
    )
