"""Forward invalidation propagation — cascading assumption failure.

When an assumption fails, `invalidation_closure` propagates that failure
forward through the declared dependency graph.  If A1 depends on A2 and A2
fails, then A1 is also invalidated because its declared support is gone.

Design invariants:
  - Deterministic: the closure follows only declared edges.
  - No guessing: if an assumption has no declared dependencies and is not
    the trigger, it is not affected.
  - Audit trail: each propagation step is a first-class operation.
"""

from __future__ import annotations

from ..models.schemas import DecisionRequest


def invalidation_closure(
    request: DecisionRequest,
    trigger_assumption_id: str,
) -> tuple[list[str], list[str]]:
    """Return (invalidated_ids, affected_alternative_ids).

    *invalidated_ids* — all assumptions transitively invalidated when
    *trigger_assumption_id* fails, including the trigger itself.

    *affected_alternative_ids* — alternatives whose required_assumptions
    overlap with the invalidated set.
    """
    assumption_index = {a.id: a for a in request.assumptions}
    if trigger_assumption_id not in assumption_index:
        return [], []

    # BFS forward through the dependency graph
    invalidated: set[str] = set()
    frontier = {trigger_assumption_id}

    while frontier:
        current = frontier.pop()
        if current in invalidated:
            continue
        invalidated.add(current)
        # Find all assumptions that depend on `current`
        for a_id, assumption in assumption_index.items():
            if a_id not in invalidated and current in assumption.dependencies:
                frontier.add(a_id)

    # Affected alternatives
    affected = [
        alt.id
        for alt in request.alternatives
        if set(alt.required_assumptions) & invalidated
    ]

    return sorted(invalidated), sorted(affected)