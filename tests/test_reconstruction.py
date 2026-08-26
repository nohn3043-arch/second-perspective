"""Causal reconstruction engine tests — backward tracing and delta reconstruction."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from second_perspective import CausalReconstructor, apply_delta_vars
from second_perspective.decision.reconstruction import (
    _backward_bfs,
    _collect_delta_invalidated,
    _estimate_severity,
    _match_signal_to_assumptions,
    build_assumption_index,
    build_evidence_index,
    build_reverse_dependency_map,
)
from second_perspective.models.enums import IssueSeverity
from second_perspective.models.schemas import (
    CausalReconstructionReport,
    ConvergenceKind,
    ConvergenceReport,
    DeltaVar,
    DecisionRequest,
    DeviationSignal,
)


def load_example() -> dict:
    path = Path(__file__).parents[1] / "examples" / "market_entry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _signal(metric: str, observed, baseline, direction: str = "above") -> DeviationSignal:
    return DeviationSignal(
        metric=metric,
        observed=observed,
        baseline=baseline,
        direction=direction,
        observed_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        source="test-scanner",
    )


def test_build_reverse_dependency_map_no_dependencies():
    request = DecisionRequest.model_validate(load_example())
    rev = build_reverse_dependency_map(request.assumptions)
    assert "A1" in rev
    assert rev["A1"] == []


def test_build_reverse_dependency_map_with_transitive():
    data = load_example()
    data["assumptions"].append(
        {
            "id": "A2",
            "statement": "Derived assumption",
            "source": "explicit",
            "falsification_condition": "Derived condition fails",
            "critical": False,
            "dependencies": ["A1"],
            "evidence_ids": [],
            "responsibility": data["assumptions"][0]["responsibility"],
        }
    )
    data["alternatives"][0]["required_assumptions"] = ["A2"]
    request = DecisionRequest.model_validate(data)
    rev = build_reverse_dependency_map(request.assumptions)
    assert "A1" in rev
    assert "A2" in rev["A1"]


def test_match_signal_to_assumptions_finds_metric_in_falsification_condition():
    request = DecisionRequest.model_validate(load_example())
    evidence_index = build_evidence_index(request.evidence)
    # Use observed_at after evidence expiry (E1 valid_until is 2027-07-01)
    # Use "coverage" which appears in A1's falsification_condition
    signal = DeviationSignal(
        metric="coverage",
        observed=40,
        baseline=60,
        direction="below",
        observed_at=datetime(2028, 1, 1, tzinfo=timezone.utc),
        source="test-scanner",
    )
    matched = _match_signal_to_assumptions(signal, request.assumptions, evidence_index)
    assert "A1" in matched


def test_match_signal_to_assumptions_skips_verified_assumptions():
    request = DecisionRequest.model_validate(load_example())
    evidence_index = build_evidence_index(request.evidence)
    # Use observed_at before evidence expiry → evidence is valid → assumption skipped
    signal = DeviationSignal(
        metric="capital_required",
        observed=5000000,
        baseline=3000000,
        direction="above",
        observed_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
        source="test-scanner",
    )
    matched = _match_signal_to_assumptions(signal, request.assumptions, evidence_index)
    assert "A1" not in matched


def test_match_signal_no_match():
    request = DecisionRequest.model_validate(load_example())
    evidence_index = build_evidence_index(request.evidence)
    signal = _signal("unrelated_metric", 100, 50)
    matched = _match_signal_to_assumptions(signal, request.assumptions, evidence_index)
    assert matched == []


def test_backward_bfs_isolated_node():
    rev = {"A1": []}
    index = {}
    ev_index = {}
    roots = _backward_bfs({"A1"}, rev, index, ev_index)
    assert "A1" in roots
    assert roots["A1"] == ["A1"]


def test_reconstruct_no_signals_returns_empty_hypotheses():
    request = DecisionRequest.model_validate(load_example())
    report = CausalReconstructor().reconstruct(request, [])
    assert isinstance(report, CausalReconstructionReport)
    assert report.hypotheses == []
    assert report.signal_count == 0
    assert report.root_candidate_count == 0
    assert len(report.algorithm_audit) >= 1


def test_reconstruct_with_unmatched_signal_has_unresolved_branches():
    request = DecisionRequest.model_validate(load_example())
    signal = _signal("unknown_metric", 100, 50)
    report = CausalReconstructor().reconstruct(request, [signal])
    assert report.unresolved_branches == ["unknown_metric"]
    assert report.hypotheses == []


def test_reconstruct_audit_chain_is_hash_verified():
    request = DecisionRequest.model_validate(load_example())
    signal = DeviationSignal(
        metric="coverage",
        observed=40,
        baseline=60,
        direction="below",
        observed_at=datetime(2028, 1, 1, tzinfo=timezone.utc),
        source="test-scanner",
    )
    report = CausalReconstructor().reconstruct(request, [signal])
    assert report.reconstruction_id.startswith("REC-")
    assert len(report.algorithm_audit) >= 4
    for i, event in enumerate(report.algorithm_audit):
        if i == 0:
            assert event.previous_event_hash is None
        else:
            assert event.previous_event_hash == report.algorithm_audit[i - 1].event_hash


def test_delta_reconstruction_assumption_falsification_changes_leader():
    request = DecisionRequest.model_validate(load_example())
    delta = DeltaVar(
        path="A1",
        value=False,
        reason="Independent market report falsifies partner availability.",
    )
    report = CausalReconstructor().reconstruct_with_delta(request, [], [delta])
    assert isinstance(report, ConvergenceReport)
    assert report.reconstruction_id.startswith("REC-")
    assert report.candidate_set_changed is True
    assert report.delta_vars == [delta]
    assert report.is_converged is False
    assert report.kind == ConvergenceKind.NO_GAIN


def test_delta_reconstruction_weight_change():
    request = DecisionRequest.model_validate(load_example())
    from decimal import Decimal
    # K1=0.45, K2=0.55 → adjust K2 to 0.30, K1 to 0.70 to keep sum=1
    delta = DeltaVar(
        path="criteria.K2.weight",
        value=Decimal("0.30"),
        reason="Reduce market-size weight to test sensitivity.",
    )
    request = request.model_copy(
        update={
            "criteria": [
                c if c.id != "K1" else c.model_copy(update={"weight": Decimal("0.70")})
                for c in request.criteria
            ]
        }
    )
    report = CausalReconstructor().reconstruct_with_delta(request, [], [delta])
    assert isinstance(report, ConvergenceReport)
    assert report.reconstruction_id.startswith("REC-")
    assert len(report.algorithm_audit) == 5


def test_delta_reconstruction_metric_override():
    request = DecisionRequest.model_validate(load_example())
    delta = DeltaVar(
        path="alternatives.S1.metrics.capital_required",
        value=8000000,
        reason="Increase capital requirement for S1.",
    )
    before = request.alternatives[0].metrics["capital_required"]
    patched = apply_delta_vars(request, [delta])
    assert patched.alternatives[0].metrics["capital_required"] == 8000000
    assert request.alternatives[0].metrics["capital_required"] == before


def test_delta_reconstruction_unknown_path_raises():
    request = DecisionRequest.model_validate(load_example())
    delta = DeltaVar(path="nonexistent.path", value=1, reason="Invalid path.")
    with pytest.raises(ValueError, match="unsupported delta path"):
        apply_delta_vars(request, [delta])


def test_apply_delta_vars_removes_affected_alternatives():
    request = DecisionRequest.model_validate(load_example())
    delta = DeltaVar(path="A1", value=False, reason="Falsify A1.")
    patched = apply_delta_vars(request, [delta])
    alt_ids = [a.id for a in patched.alternatives]
    assert "S2" not in alt_ids
    assert "S1" in alt_ids


def test_collect_delta_invalidated():
    request = DecisionRequest.model_validate(load_example())
    delta = DeltaVar(path="A1", value=False, reason="Falsify.")
    ids = _collect_delta_invalidated(request, [delta])
    assert "A1" in ids


def test_estimate_severity_critical_with_wide_blast():
    data = load_example()
    request = DecisionRequest.model_validate(data)
    index = build_assumption_index(request.assumptions)
    severity = _estimate_severity("A1", index, 2)
    assert severity == IssueSeverity.ERROR