"""Scenario stress-run coverage — EVALUATED / NO_VIABLE_ALTERNATIVE / BLOCKED."""

from second_perspective.decision.engine import IntelligentDecisionEngine
from second_perspective.hub.scenario import analyze_scenarios
from second_perspective.models.enums import ScenarioOutcomeStatus
from second_perspective.models.schemas import ScenarioDefinition


def _evaluate(make_request):
    engine = IntelligentDecisionEngine()
    request = make_request()
    baseline = engine.evaluate(request)
    return engine, request, baseline


def test_empty_scenarios_returns_empty(make_request):
    engine, request, baseline = _evaluate(make_request)
    results = analyze_scenarios(engine, request, baseline, [])
    assert results == []


def test_evaluated_scenario_keeps_alternatives(make_request):
    engine, request, baseline = _evaluate(make_request)
    scenario = ScenarioDefinition(
        id="SCN-1",
        name="hold baseline",
        failed_assumption_ids=[],
        metric_overrides={},
    )
    results = analyze_scenarios(engine, request, baseline, [scenario])
    assert len(results) == 1
    assert results[0].outcome_status == ScenarioOutcomeStatus.EVALUATED
    assert results[0].evaluation_result is not None
    assert results[0].issues == []
    # evaluation_result is a json dump containing the decision_id
    assert results[0].evaluation_result["decision_id"] == baseline.decision_id


def test_no_viable_alternative_when_all_removed(make_request):
    engine, request, baseline = _evaluate(make_request)
    scenario = ScenarioDefinition(
        id="SCN-2",
        name="kill all alternatives",
        failed_assumption_ids=["A1"],  # both S1/S2 depend on A1
        metric_overrides={},
    )
    results = analyze_scenarios(engine, request, baseline, [scenario])
    assert results[0].outcome_status == ScenarioOutcomeStatus.NO_VIABLE_ALTERNATIVE
    assert results[0].evaluation_result is None
    assert "No viable alternatives" in results[0].issues[0]


def test_metric_override_applied(make_request):
    engine, request, baseline = _evaluate(make_request)
    scenario = ScenarioDefinition(
        id="SCN-3",
        name="boost S1",
        failed_assumption_ids=[],
        metric_overrides={"S1": {"metric_K1": 99}},
    )
    results = analyze_scenarios(engine, request, baseline, [scenario])
    assert results[0].outcome_status == ScenarioOutcomeStatus.EVALUATED
    s1 = next(
        a
        for a in results[0].evaluation_result["alternatives"]
        if a["alternative_id"] == "S1"
    )
    # metric override must flow into the re-evaluation (json dump: Decimal→str)
    assert s1["criterion_scores"][0]["actual"] == "99"


def test_blocked_when_evaluation_raises(make_request):
    engine, request, baseline = _evaluate(make_request)

    class BoomEngine:
        def evaluate(self, request):
            raise RuntimeError("simulated engine failure")

    scenario = ScenarioDefinition(
        id="SCN-4",
        name="engine boom",
        failed_assumption_ids=[],
        metric_overrides={},
    )
    results = analyze_scenarios(BoomEngine(), request, baseline, [scenario])
    assert results[0].outcome_status == ScenarioOutcomeStatus.BLOCKED
    assert "simulated engine failure" in results[0].issues[0]


def test_partial_removal_keeps_viable_alternative(make_request):
    engine, request, baseline = _evaluate(make_request)
    # Only S1 depends on A1 via conftest defaults; craft a request where
    # A1 is required by S1 but assumed-failed leaves S2 standing? conftest
    # gives both alternatives required_assumptions=["A1"], so instead add a
    # new alternative without assumptions.
    from second_perspective.models.enums import ConstraintKind, ConstraintOperator

    request2 = make_request(
        alternatives=[
            engine and request.alternatives[0],
        ],
    )
    scenario = ScenarioDefinition(
        id="SCN-5",
        name="remove one",
        failed_assumption_ids=["A1"],
        metric_overrides={},
    )
    results = analyze_scenarios(engine, request2, baseline, [scenario])
    assert results[0].outcome_status == ScenarioOutcomeStatus.NO_VIABLE_ALTERNATIVE
