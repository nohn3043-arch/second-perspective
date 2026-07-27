"""Causal reconstruction engine — trace observed deviations backward to root causes.

This module is the mirror image of causal.py. Where `invalidation_closure` propagates
assumption failures *forward* (A1 fails → what else breaks?), this module traces
*backward* (deviation observed → which assumption failure could explain it?).

Design invariants (aligned with NOMOS core):
  - No guessing: output is a set of candidate hypotheses, not a single "answer".
  - Deterministic: every trace path is derived from the declared dependency graph.
  - Audit trail: each reconstruction step generates AlgorithmAuditEvent entries.
  - Information-first: every hypothesis explicitly lists what is missing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from ..models.enums import IssueSeverity
from ..models.schemas import (
    AlgorithmAuditEvent,
    CausalReconstructionReport,
    DecisionRequest,
    DeviationSignal,
    RootCauseHypothesis,
)


# ── Graph helpers ────────────────────────────────────────────────────


def build_reverse_dependency_map(assumptions: list) -> dict[str, list[str]]:
    """Build reverse dependency graph from declared assumption dependencies.

    Forward:  A1.dependencies = [A2, A3]  →  "A1 depends on A2 and A3"
    Reverse:  A2 → [A1], A3 → [A1]        →  "A2 failure affects A1"

    This is the topological inverse needed for backward tracing.
    """
    reverse: dict[str, list[str]] = {}
    for assumption in assumptions:
        for dep in assumption.dependencies:
            reverse.setdefault(dep, []).append(assumption.id)
    for assumption in assumptions:
        reverse.setdefault(assumption.id, [])
    return reverse


def build_assumption_index(assumptions: list) -> dict[str, object]:
    """Index assumptions by ID for O(1) lookup."""
    return {a.id: a for a in assumptions}


def build_evidence_index(evidence_list: list) -> dict[str, object]:
    """Index evidence by ID."""
    return {e.id: e for e in evidence_list}


# ── Signal-to-assumption mapping ─────────────────────────────────────


def _match_signal_to_assumptions(
    signal: DeviationSignal,
    assumptions: list,
    evidence_index: dict[str, object],
) -> list[str]:
    """Return assumption IDs that could explain a single deviation signal.

    Matching logic:
      1. If the signal's metric name appears in an assumption's falsification_condition,
         that assumption is a candidate observed-failure.
      2. Exclude assumptions that have non-expired, supplied evidence directly backing them
         (the evidence says "this assumption holds", so it's less likely the root cause).
    """
    metric_lower = signal.metric.lower()
    candidates: list[str] = []

    for assumption in assumptions:
        # Loose match: metric name appears in falsification condition
        if metric_lower not in assumption.falsification_condition.lower():
            continue

        # Evidence check: if ALL of this assumption's evidence is supplied
        # and none is expired, the assumption is "verified" — skip it.
        if assumption.evidence_ids:
            all_supplied = True
            for eid in assumption.evidence_ids:
                ev = evidence_index.get(eid)
                if ev is None:
                    all_supplied = False
                    break
                from ..models.enums import EvidenceStatus

                if ev.status != EvidenceStatus.SUPPLIED:
                    all_supplied = False
                    break
                if ev.valid_until is not None and ev.valid_until <= signal.observed_at:
                    all_supplied = False
                    break
            if all_supplied:
                continue  # evidence says this assumption is fine

        candidates.append(assumption.id)

    return candidates


# ── Backward BFS ──────────────────────────────────────────────────────


def _backward_bfs(
    seed_assumption_ids: set[str],
    reverse_dep: dict[str, list[str]],
    assumption_index: dict[str, object],
    evidence_index: dict[str, object],
) -> dict[str, list[str]]:
    """BFS backward from observed failures to potential root causes.

    Returns:
        {root_id: [full chain from root to nearest seed]}

    Traversal rules:
      - Follow reverse_dep edges upward (against the dependency direction).
      - Stop at nodes where evidence is supplied and not expired (verified assumptions).
      - Record the root of each trace — the farthest node reached before stopping.
    """
    roots: dict[str, list[str]] = {}

    for seed in sorted(seed_assumption_ids):
        if seed not in reverse_dep:
            # Isolated node: it is its own root
            roots[seed] = [seed]
            continue

        # BFS
        visited: set[str] = {seed}
        frontier: list[tuple[str, list[str]]] = [(seed, [seed])]
        local_roots: list[tuple[str, list[str]]] = []

        while frontier:
            current, path = frontier.pop(0)
            parents = reverse_dep.get(current, [])

            if not parents:
                local_roots.append((current, list(path)))
                continue

            has_unverified_parent = False
            for parent in parents:
                if parent in visited:
                    continue
                visited.add(parent)

                # Check if parent is "verified" by evidence
                parent_assumption = assumption_index.get(parent)
                if parent_assumption and parent_assumption.evidence_ids:
                    all_supplied = True
                    for eid in parent_assumption.evidence_ids:
                        ev = evidence_index.get(eid)
                        if ev is None:
                            all_supplied = False
                            break
                        from ..models.enums import EvidenceStatus

                        if ev.status != EvidenceStatus.SUPPLIED:
                            all_supplied = False
                            break
                    if all_supplied:
                        # Verified parent: stop here, current is effectively a root
                        local_roots.append((current, list(path)))
                        continue

                new_path = [parent] + path
                frontier.append((parent, new_path))
                has_unverified_parent = True

            if not has_unverified_parent and not parents:
                local_roots.append((current, list(path)))

        for root_id, chain in local_roots:
            if root_id not in roots or len(chain) > len(roots[root_id]):
                roots[root_id] = chain

    return roots


# ── Severity estimation ──────────────────────────────────────────────


def _estimate_severity(
    assumption_id: str,
    assumption_index: dict[str, object],
    affected_signal_count: int,
) -> IssueSeverity:
    """Estimate root cause severity based on criticality and blast radius."""
    assumption = assumption_index.get(assumption_id)
    if assumption is None:
        return IssueSeverity.WARNING

    is_critical = getattr(assumption, "critical", False)
    has_responsibility = getattr(assumption, "responsibility", None) is not None

    if is_critical and affected_signal_count >= 2:
        return IssueSeverity.ERROR
    if is_critical and not has_responsibility:
        return IssueSeverity.ERROR
    if is_critical or affected_signal_count >= 2:
        return IssueSeverity.WARNING
    return IssueSeverity.INFO


# ── Missing evidence ──────────────────────────────────────────────────


def _collect_missing_evidence(
    chain: list[str],
    assumption_index: dict[str, object],
    evidence_index: dict[str, object],
) -> list[str]:
    """Collect evidence IDs along the causal chain that are missing or expired."""
    missing: list[str] = []
    for aid in chain:
        assumption = assumption_index.get(aid)
        if assumption is None:
            continue
        for eid in getattr(assumption, "evidence_ids", []):
            ev = evidence_index.get(eid)
            if ev is None:
                missing.append(eid)
                continue
            from ..models.enums import EvidenceStatus

            if ev.status != EvidenceStatus.SUPPLIED:
                missing.append(eid)
    return sorted(set(missing))


# ── Audit event builder ───────────────────────────────────────────────


def _build_audit_event(
    sequence: int,
    stage: str,
    rule_id: str,
    operation: str,
    inputs: dict,
    output,
    previous_hash: str | None,
) -> AlgorithmAuditEvent:
    """Build a single audit event with hash linking, matching ledger.py convention."""
    import hashlib

    from ..canonical import canonical_json

    # Build payload as dict, compute hash, then construct the pydantic model
    payload = {
        "sequence": sequence,
        "stage": stage,
        "rule_id": rule_id,
        "operation": operation,
        "inputs": inputs,
        "output": output,
        "references": [],
        "previous_event_hash": previous_hash,
    }
    digest = hashlib.sha256(canonical_json(payload)).hexdigest()
    payload["event_hash"] = digest
    return AlgorithmAuditEvent(**payload)


# ── Main engine ───────────────────────────────────────────────────────


class CausalReconstructor:
    """Deterministic backward causal tracer.

    Takes deviation signals from the perception layer and traces backward
    along the declared assumption dependency graph to identify candidate
    root cause hypotheses.  Does NOT produce a single "answer" — output is
    a structured set of hypotheses for human verification.
    """

    def reconstruct(
        self,
        request: DecisionRequest,
        signals: list[DeviationSignal],
    ) -> CausalReconstructionReport:
        reconstruction_id = f"REC-{uuid4().hex[:12].upper()}"
        audit_events: list[AlgorithmAuditEvent] = []
        prev_hash: str | None = None
        seq = 0

        # ── Phase 0: build indices ──
        assumption_index = build_assumption_index(request.assumptions)
        evidence_index = build_evidence_index(request.evidence)
        reverse_dep = build_reverse_dependency_map(request.assumptions)

        seq += 1
        ev = _build_audit_event(
            seq, "reconstruction", "REC-INDEX",
            "build_reverse_dep",
            {"assumption_count": len(request.assumptions)},
            {"reverse_edge_count": sum(len(v) for v in reverse_dep.values())},
            prev_hash,
        )
        audit_events.append(ev)
        prev_hash = ev.event_hash

        # ── Phase 1: map signals to affected assumptions ──
        signal_to_assumptions: dict[str, list[str]] = {}
        all_seed_ids: set[str] = set()

        for signal in signals:
            matched = _match_signal_to_assumptions(signal, request.assumptions, evidence_index)
            signal_to_assumptions[signal.metric] = matched
            all_seed_ids.update(matched)

        seq += 1
        ev = _build_audit_event(
            seq, "reconstruction", "REC-MAP",
            "signal_to_assumption_mapping",
            {"signals": [s.metric for s in signals]},
            {"matched_assumptions": sorted(all_seed_ids)},
            prev_hash,
        )
        audit_events.append(ev)
        prev_hash = ev.event_hash

        # ── Phase 2: backward BFS ──
        root_chains = _backward_bfs(all_seed_ids, reverse_dep, assumption_index, evidence_index)

        seq += 1
        ev = _build_audit_event(
            seq, "reconstruction", "REC-BFS",
            "backward_bfs",
            {"seed_count": len(all_seed_ids), "seeds": sorted(all_seed_ids)},
            {"root_count": len(root_chains), "roots": sorted(root_chains.keys())},
            prev_hash,
        )
        audit_events.append(ev)
        prev_hash = ev.event_hash

        # ── Phase 3: build hypotheses ──
        hypotheses: list[RootCauseHypothesis] = []
        for root_id, chain in root_chains.items():
            # Determine which signals this root explains
            explained: list[str] = []
            for metric, matched in signal_to_assumptions.items():
                if any(node in matched for node in chain):
                    explained.append(metric)

            missing = _collect_missing_evidence(chain, assumption_index, evidence_index)

            # Verification action
            root_assumption = assumption_index.get(root_id)
            root_name = getattr(root_assumption, "statement", root_id) if root_assumption else root_id
            verification = (
                f"验证假设 [{root_id}] {root_name}：检查证据 "
                + (", ".join(missing[:3]) if missing else "无缺失证据，确认 falsification_condition 是否已触发")
            )

            severity = _estimate_severity(root_id, assumption_index, len(explained))

            hypotheses.append(
                RootCauseHypothesis(
                    id=f"RH-{uuid4().hex[:8].upper()}",
                    root_assumption_id=root_id,
                    causal_chain=chain,
                    explained_signals=explained,
                    missing_evidence_ids=missing,
                    verification_action=verification,
                    dependency_depth=len(chain) - 1,
                    severity=severity,
                )
            )

        # Sort: ERROR first, then by depth (shorter chain = more likely root)
        severity_order = {IssueSeverity.ERROR: 0, IssueSeverity.WARNING: 1, IssueSeverity.INFO: 2}
        hypotheses.sort(key=lambda h: (severity_order.get(h.severity, 2), h.dependency_depth))

        # Phase 4: identify unresolved branches (signal without any matched assumption)
        unresolved = [
            metric for metric, matched in signal_to_assumptions.items() if not matched
        ]

        seq += 1
        ev = _build_audit_event(
            seq, "reconstruction", "REC-HYPOTHESES",
            "build_hypotheses",
            {"root_count": len(root_chains)},
            {
                "hypothesis_count": len(hypotheses),
                "unresolved_branches": unresolved,
            },
            prev_hash,
        )
        audit_events.append(ev)
        prev_hash = ev.event_hash

        # ── Phase 5: compute root hash ──
        import hashlib

        from ..canonical import canonical_json

        if audit_events:
            final_payload = {
                "last_event_hash": audit_events[-1].event_hash,
                "reconstruction_id": reconstruction_id,
                "hypothesis_count": len(hypotheses),
            }
            audit_root = hashlib.sha256(canonical_json(final_payload)).hexdigest()
        else:
            audit_root = None

        return CausalReconstructionReport(
            reconstruction_id=reconstruction_id,
            hypotheses=hypotheses,
            signal_count=len(signals),
            root_candidate_count=len(root_chains),
            unresolved_branches=unresolved,
            algorithm_audit=audit_events,
            algorithm_audit_root_hash=audit_root,
        )
