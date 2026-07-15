from __future__ import annotations

from ..models.schemas import DecisionRequest


def invalidation_closure(
    request: DecisionRequest,
    failed_assumption_id: str,
) -> tuple[list[str], list[str]]:
    """Return assumptions and alternatives invalidated by one failed assumption.

    Dependencies point from an assumption to assumptions it depends on. If a
    dependency fails, every assumption that transitively depends on it loses
    its declared validity basis.
    """

    invalidated = {failed_assumption_id}
    changed = True
    while changed:
        changed = False
        for assumption in request.assumptions:
            if assumption.id in invalidated:
                continue
            if invalidated.intersection(assumption.dependencies):
                invalidated.add(assumption.id)
                changed = True

    affected_alternatives = sorted(
        alternative.id
        for alternative in request.alternatives
        if invalidated.intersection(alternative.required_assumptions)
    )
    return sorted(invalidated), affected_alternatives
