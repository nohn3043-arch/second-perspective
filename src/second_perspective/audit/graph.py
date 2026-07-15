from __future__ import annotations


def find_dependency_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Return deterministic dependency cycles without executing arbitrary expressions."""
    state: dict[str, int] = {node: 0 for node in graph}
    stack: list[str] = []
    stack_index: dict[str, int] = {}
    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def canonicalize(cycle: list[str]) -> tuple[str, ...]:
        body = cycle[:-1]
        rotations = [tuple(body[i:] + body[:i]) for i in range(len(body))]
        canonical = min(rotations)
        return canonical + (canonical[0],)

    def visit(node: str) -> None:
        state[node] = 1
        stack_index[node] = len(stack)
        stack.append(node)

        for dependency in sorted(graph.get(node, [])):
            if state[dependency] == 0:
                visit(dependency)
            elif state[dependency] == 1:
                start = stack_index[dependency]
                cycle = stack[start:] + [dependency]
                canonical = canonicalize(cycle)
                if canonical not in seen:
                    seen.add(canonical)
                    cycles.append(list(canonical))

        stack.pop()
        stack_index.pop(node, None)
        state[node] = 2

    for node in sorted(graph):
        if state[node] == 0:
            visit(node)

    return cycles
