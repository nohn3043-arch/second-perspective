"""Forward invalidation closure coverage."""

from second_perspective.decision.causal import invalidation_closure


def test_unknown_trigger_returns_empty(make_request):
    invalidated, affected = invalidation_closure(make_request(), "A-NOPE")
    assert invalidated == [] and affected == []


def test_trigger_invalidates_itself(make_request, make_assumption):
    request = make_request(assumptions=[make_assumption("A1", evidence_ids=["E1"])])
    invalidated, affected = invalidation_closure(request, "A1")
    assert invalidated == ["A1"]


def test_forward_propagation_via_dependencies(
    make_request, make_assumption, make_alternative
):
    # A2 declares dependency on A1 -> failing A1 invalidates A2
    request = make_request(
        assumptions=[
            make_assumption("A1", evidence_ids=["E1"]),
            make_assumption("A2", dependencies=["A1"], evidence_ids=["E1"]),
        ],
        alternatives=[
            make_alternative(
                "S1",
                required_assumptions=["A1"],
                evidence_ids=["E1"],
                metrics={"metric_K1": 80, "budget": 800},
            ),
            make_alternative(
                "S2",
                required_assumptions=["A2"],
                evidence_ids=["E1"],
                metrics={"metric_K1": 60, "budget": 500},
            ),
        ],
    )
    invalidated, affected = invalidation_closure(request, "A1")
    assert invalidated == ["A1", "A2"]
    assert affected == ["S1", "S2"]


def test_transitive_closure(make_request, make_assumption):
    # A1 <- A2 <- A3 chain
    request = make_request(
        assumptions=[
            make_assumption("A1", evidence_ids=["E1"]),
            make_assumption("A2", dependencies=["A1"], evidence_ids=["E1"]),
            make_assumption("A3", dependencies=["A2"], evidence_ids=["E1"]),
        ],
    )
    invalidated, _ = invalidation_closure(request, "A1")
    assert invalidated == ["A1", "A2", "A3"]


def test_unrelated_assumption_unaffected(make_request, make_assumption):
    request = make_request(
        assumptions=[
            make_assumption("A1", evidence_ids=["E1"]),
            make_assumption("A9", evidence_ids=["E1"]),
        ],
    )
    invalidated, _ = invalidation_closure(request, "A1")
    assert invalidated == ["A1"]


def test_no_guessing_without_dependencies(make_request, make_assumption):
    # A2 has no dependencies -> failing A1 must not touch it
    request = make_request(
        assumptions=[
            make_assumption("A1", evidence_ids=["E1"]),
            make_assumption("A2", evidence_ids=["E1"]),
        ],
    )
    invalidated, _ = invalidation_closure(request, "A1")
    assert invalidated == ["A1"]
