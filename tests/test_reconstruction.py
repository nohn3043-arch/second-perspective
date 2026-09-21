"""Causal reconstruction coverage: signal matching, backward BFS, delta vars."""

from datetime import datetime, timezone

import pytest

from second_perspective.decision.reconstruction import (
    CausalReconstructor,
    _backward_bfs,
    _collect_delta_invalidated,
    _collect_missing_evidence,
    _estimate_severity,
    _match_signal_to_assumptions,
    apply_delta_vars,
    build_assumption_index,
    build_evidence_index,
    build_reverse_dependency_map,
)
from second_perspective.models.enums import (
    AssumptionState,
    ConvergenceKind,
    EvidenceStatus,
    IssueSeverity,
)
from second_perspective.models.schemas import (
    DeltaVar,
    DeviationSignal,
)


def _signal(metric: str, observed_at: datetime | None = None) -> DeviationSignal:
    return DeviationSignal(
        metric=metric,
        observed=95,
        baseline=80,
        direction="above",
        observed_at=observed_at or datetime(2026, 2, 1, tzinfo=timezone.utc),
        source="perception-v1",
    )


@pytest.fixture
def _noise_request(make_request, make_assumption, make_evidence):
    """A request whose single assumption is protected by supplied evidence."""
    return make_request(
        assumptions=[make_assumption("A1", evidence_ids=["E1"])],
        # observed 2026-01-15 -> valid_until 2026-02-14, which covers the
        # 2026-02-01 signal time so the evidence is NOT expired
        evidence=[
            make_evidence(
                "E1",
                status=EvidenceStatus.SUPPLIED,
                observed_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            )
        ],
        constraints=[],
        criteria=[],
    )


class TestMatching:
    def test_metric_match_returns_assumption(self, make_request, make_assumption):
        request = make_request(assumptions=[make_assumption("A1", evidence_ids=[])])

        got = _match_signal_to_assumptions(
            _signal("metric_a1"),
            request.assumptions,
            build_evidence_index(request.evidence),
        )
        assert got == ["A1"]

    def test_verified_assumption_skipped(self, _noise_request):
        got = _match_signal_to_assumptions(
            _signal("metric_a1"),
            _noise_request.assumptions,
            build_evidence_index(_noise_request.evidence),
        )
        # evidence says the assumption holds -> not a candidate
        assert _noise_request.assumptions[0].evidence_ids == ["E1"]
        assert got == []

    def test_disputed_evidence_is_candidate(
        self, make_request, make_assumption, make_evidence
    ):
        request = make_request(
            assumptions=[make_assumption("A1", evidence_ids=["E1"])],
            evidence=[make_evidence("E1", status=EvidenceStatus.DISPUTED)],
            constraints=[],
            criteria=[],
        )
        got = _match_signal_to_assumptions(
            _signal("metric_a1"),
            request.assumptions,
            build_assumption_index(request.assumptions),
        )
        assert got == ["A1"]

    def test_no_match_returns_empty(self, make_request):
        got = _match_signal_to_assumptions(
            _signal("metric_unknown"), make_request().assumptions, {}
        )
        assert got == []


class TestReverseMapAndBfs:
    def test_reverse_dependency_map(self, make_request, make_assumption):
        request = make_request(
            assumptions=[
                make_assumption("A1"),
                make_assumption("A2", dependencies=["A1"]),
            ],
            constraints=[],
            criteria=[],
        )
        reverse = build_reverse_dependency_map(request.assumptions)
        assert reverse["A1"] == ["A2"]
        assert reverse["A2"] == []

    def test_isolated_seed_is_own_root(self, make_request):
        request = make_request(constraints=[], criteria=[])
        roots = _backward_bfs(
            {"A1"},
            build_reverse_dependency_map(request.assumptions),
            build_assumption_index(request.assumptions),
            {},
        )
        assert roots == {"A1": ["A1"]}

    def test_backward_chain_traced(self, make_request, make_assumption):
        request = make_request(
            assumptions=[
                make_assumption("A1"),
                make_assumption("A2", dependencies=["A1"]),
            ],
            constraints=[],
            criteria=[],
        )
        roots = _backward_bfs(
            {"A1"},
            build_reverse_dependency_map(request.assumptions),
            build_assumption_index(request.assumptions),
            {},
        )
        # A2 depends on A1, so the trace from A1 runs through A2
        assert roots["A2"] == ["A2", "A1"]


class TestSeverity:
    def test_missing_assumption_warning(self, make_request):
        assert _estimate_severity("NOPE", {}, 1) == IssueSeverity.WARNING

    def test_critical_wide_blast_error(self, make_request, make_assumption):
        index = build_assumption_index([make_assumption("A1")])
        assert _estimate_severity("A1", index, 2) == IssueSeverity.ERROR

    def test_critical_no_owner_error(self, make_request, make_assumption):
        index = build_assumption_index([make_assumption("A1", no_responsibility=True)])
        assert _estimate_severity("A1", index, 1) == IssueSeverity.ERROR

    def test_critical_single_signal_warning(self, make_request, make_assumption):
        index = build_assumption_index([make_assumption("A1")])
        assert _estimate_severity("A1", index, 1) == IssueSeverity.WARNING

    def test_non_critical_single_signal_info(self, make_request, make_assumption):
        index = build_assumption_index([make_assumption("A1", critical=False)])
        assert _estimate_severity("A1", index, 1) == IssueSeverity.INFO


class TestCollectMissingEvidence:
    def test_missing_and_not_supplied(
        self, make_request, make_assumption, make_evidence
    ):
        request = make_request(
            assumptions=[make_assumption("A1", evidence_ids=["E1", "E2"])],
            evidence=[
                make_evidence("E1", status=EvidenceStatus.MISSING),
                make_evidence("E2", status=EvidenceStatus.DISPUTED),
            ],
            constraints=[],
            criteria=[],
        )
        missing = _collect_missing_evidence(
            ["A1"],
            build_assumption_index(request.assumptions),
            {e.id: e for e in request.evidence},
        )
        assert missing == sorted(["E1", "E2"])

    def test_supplied_evidence_not_missing(
        self, make_request, make_assumption, make_evidence
    ):
        request = make_request(
            assumptions=[make_assumption("A1", evidence_ids=["E1"])],
            evidence=[make_evidence("E1", status=EvidenceStatus.SUPPLIED)],
            constraints=[],
            criteria=[],
        )
        missing = _collect_missing_evidence(
            ["A1"],
            build_assumption_index(request.assumptions),
            {e.id: e for e in request.evidence},
        )
        assert missing == []


class TestApplyDeltaVars:
    def test_falsify_assumption_drops_dependents(
        self, make_request, make_assumption, make_alternative
    ):
        request = make_request(
            assumptions=[
                make_assumption("A1"),
                make_assumption("A2", dependencies=["A1"]),
            ],
            alternatives=[
                make_alternative("S1", required_assumptions=["A2"], metrics={"x": 1}),
                make_alternative("S2", required_assumptions=[], metrics={"x": 2}),
            ],
            constraints=[],
            criteria=[],
        )
        patched = apply_delta_vars(
            request,
            [DeltaVar(path="A1", value=True, reason="init")],
        )
        assert [a.id for a in patched.alternatives] == ["S2"]
        assert _collect_delta_invalidated(
            request, [DeltaVar(path="A1", value=True, reason="init")]
        ) == ["A1", "A2"]

    def test_rewrite_criterion_weight(self, make_request):
        request = make_request(constraints=[], criteria=None)
        patched = apply_delta_vars(
            request,
            [DeltaVar(path="criteria.K1.weight", value="0.2", reason="init")],
        )
        assert str(patched.criteria[0].weight) == "0.2"

    def test_rewrite_alternative_metric(self, make_request):
        patched = apply_delta_vars(
            make_request(constraints=[], criteria=[]),
            [DeltaVar(path="alternatives.S1.metrics.budget", value=42, reason="init")],
        )
        assert patched.alternatives[0].metrics["budget"] == 42

    @pytest.mark.parametrize(
        "path",
        [
            "criteria.K1.name",
            "alternatives.S1.required_assumptions",
            "criteria.NOPE.weight",
            "alternatives.NOPE.metrics.x",
            "NOPE",
            "weird.path.here",
        ],
    )
    def test_unsupported_paths_raise(self, make_request, path):
        with pytest.raises(ValueError):
            apply_delta_vars(
                make_request(constraints=[], criteria=[]),
                [DeltaVar(path=path, value=1, reason="init")],
            )


class TestReconstructor:
    def test_empty_signals_no_hypotheses(self, make_request):
        report = CausalReconstructor().reconstruct(
            make_request(constraints=[], criteria=[]), []
        )
        assert report.signal_count == 0
        assert report.hypotheses == []
        assert report.unresolved_branches == []
        assert report.root_candidate_count == 0
        assert len(report.algorithm_audit) == 4

    def test_signal_maps_to_hypothesis(self, make_request):
        request = make_request(constraints=[], criteria=[])
        report = CausalReconstructor().reconstruct(request, [_signal("metric_a1")])
        assert report.signal_count == 1
        assert report.root_candidate_count == 1
        hyp = report.hypotheses[0]
        assert hyp.root_assumption_id == "A1"
        assert hyp.explained_signals == ["metric_a1"]
        assert hyp.severity == IssueSeverity.WARNING

    def test_unresolved_branch_listed(self, make_request):
        report = CausalReconstructor().reconstruct(
            make_request(constraints=[], criteria=[]),
            [_signal("metric_nonsense")],
        )
        assert report.unresolved_branches == ["metric_nonsense"]
        assert report.root_candidate_count == 0

    def test_verified_evidence_suppresses_hypothesis(self, _noise_request):
        report = CausalReconstructor().reconstruct(
            _noise_request, [_signal("metric_a1")]
        )
        assert report.unresolved_branches == ["metric_a1"]
        assert report.hypotheses == []

    def test_audit_chain_verifiable(self, make_request):
        from second_perspective.audit.ledger import verify_algorithm_audit

        report = CausalReconstructor().reconstruct(
            make_request(constraints=[], criteria=[]), [_signal("metric_a1")]
        )
        # chain integrity: sequence/previous_event_hash/per-event hash all valid
        assert verify_algorithm_audit(report.algorithm_audit)
        # root hash is the last event hash (ledger convention), so passing it
        # through the chain verifier must also hold
        assert verify_algorithm_audit(
            report.algorithm_audit, report.algorithm_audit[-1].event_hash
        )

    def test_forward_invalidation_used(
        self, make_request, make_assumption, make_alternative
    ):
        """Falsifying a root drops alternatives depending on derived assumptions."""
        request = make_request(
            assumptions=[
                make_assumption("A1"),
                make_assumption("A2", dependencies=["A1"]),
            ],
            alternatives=[
                make_alternative("S1", required_assumptions=["A2"], metrics={"x": 1}),
                make_alternative("S2", required_assumptions=["A1"], metrics={"x": 2}),
            ],
            constraints=[],
            criteria=[],
        )
        patched = apply_delta_vars(
            request, [DeltaVar(path="A1", value=True, reason="init")]
        )
        assert [a.id for a in patched.alternatives] == []


class TestDeltaReconstruction:
    def test_weight_shift_changes_candidates(
        self, make_request, make_criterion, make_alternative
    ):
        request = make_request(
            evaluation_mode="weighted",
            criteria=[
                make_criterion("K1", weight="0.5"),
                make_criterion("K2", weight="0.5"),
            ],
            alternatives=[
                make_alternative(
                    "S1",
                    metrics={"metric_K1": 80, "metric_K2": 20, "budget": 100},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
                make_alternative(
                    "S2",
                    metrics={"metric_K1": 50, "metric_K2": 50, "budget": 100},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
            ],
            constraints=[],
        )
        recon = CausalReconstructor()
        report = recon.reconstruct_with_delta(
            request,
            [],
            [
                DeltaVar(path="criteria.K1.weight", value="0.9", reason="shift"),
                DeltaVar(path="criteria.K2.weight", value="0.1", reason="shift"),
            ],
        )
        assert report.candidate_set_changed is True
        assert report.kind == ConvergenceKind.NO_GAIN
        assert report.is_converged is False
        assert report.before_leading_candidate_ids != report.after_leading_candidate_ids

    def test_no_delta_reaches_fixed_point(self, make_request):
        request = make_request(constraints=[], criteria=None)
        report = CausalReconstructor().reconstruct_with_delta(
            request,
            [],
            [DeltaVar(path="alternatives.S1.metrics.budget", value=800, reason="same")],
        )
        assert report.candidate_set_changed is False
        assert report.kind == ConvergenceKind.FIXED_POINT
        assert report.is_converged is True
