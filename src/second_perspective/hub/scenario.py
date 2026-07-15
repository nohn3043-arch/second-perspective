from __future__ import annotations

import hashlib

from ..canonical import canonical_json
from ..audit.ledger import AlgorithmAuditLedger, verify_algorithm_audit
from ..decision.causal import invalidation_closure
from ..decision.engine import IntelligentDecisionEngine
from ..decision.selection import select_leading_candidates
from ..models.enums import AlternativeStatus, DecisionStatus, ScenarioOutcomeStatus
from ..models.hub import ScenarioDefinition, ScenarioResult
from ..models.schemas import DecisionRequest, DecisionResult


def analyze_scenarios(
    *,
    engine: IntelligentDecisionEngine,
    request: DecisionRequest,
    baseline: DecisionResult,
    scenarios: list[ScenarioDefinition],
) -> list[ScenarioResult]:
    return [
        _analyze_scenario(
            engine=engine,
            request=request,
            baseline=baseline,
            scenario=scenario,
        )
        for scenario in scenarios
    ]


def _analyze_scenario(
    *,
    engine: IntelligentDecisionEngine,
    request: DecisionRequest,
    baseline: DecisionResult,
    scenario: ScenarioDefinition,
) -> ScenarioResult:
    alternatives = []
    for alternative in request.alternatives:
        overrides = scenario.metric_overrides.get(alternative.id, {})
        alternatives.append(
            alternative.model_copy(
                update={"metrics": {**alternative.metrics, **overrides}},
                deep=True,
            )
        )

    evidence = [
        item.model_copy(
            update={
                "status": scenario.evidence_status_overrides.get(item.id, item.status)
            },
            deep=True,
        )
        for item in request.evidence
    ]
    scenario_request = request.model_copy(
        update={"alternatives": alternatives, "evidence": evidence},
        deep=True,
    )
    evaluated = engine.evaluate(scenario_request)

    invalidated_assumptions: set[str] = set()
    removed_alternatives: set[str] = set()
    for assumption_id in scenario.failed_assumption_ids:
        invalidated, affected = invalidation_closure(scenario_request, assumption_id)
        invalidated_assumptions.update(invalidated)
        removed_alternatives.update(affected)

    remaining = [
        evaluation
        for evaluation in evaluated.alternatives
        if evaluation.alternative_id not in removed_alternatives
    ]
    eligible_ids = sorted(
        item.alternative_id
        for item in remaining
        if item.status == AlternativeStatus.ELIGIBLE
    )
    leading_ids = select_leading_candidates(scenario_request, remaining)

    if evaluated.status == DecisionStatus.EVIDENCE_PENDING:
        outcome = ScenarioOutcomeStatus.BLOCKED
    elif not eligible_ids:
        outcome = ScenarioOutcomeStatus.NO_VIABLE_ALTERNATIVE
    else:
        outcome = ScenarioOutcomeStatus.EVALUATED

    scenario_payload = {
        "effective_request_fingerprint": evaluated.input_fingerprint,
        "scenario": scenario.model_dump(mode="json"),
    }
    scenario_fingerprint = hashlib.sha256(canonical_json(scenario_payload)).hexdigest()
    baseline_leaders = sorted(baseline.leading_candidate_ids)
    ledger = AlgorithmAuditLedger(evaluated.algorithm_audit)
    ledger.append(
        stage="scenario",
        rule_id="DECLARED_SCENARIO_APPLICATION",
        operation="apply_overrides_failures_and_reselect",
        inputs={
            "scenario_id": scenario.id,
            "metric_overrides": scenario.metric_overrides,
            "evidence_status_overrides": scenario.evidence_status_overrides,
            "failed_assumption_ids": scenario.failed_assumption_ids,
        },
        output={
            "outcome_status": outcome,
            "invalidated_assumption_ids": sorted(invalidated_assumptions),
            "removed_alternative_ids": sorted(removed_alternatives),
            "leading_candidate_ids": leading_ids,
            "scenario_fingerprint": scenario_fingerprint,
        },
        references=[scenario.id, *sorted(removed_alternatives), *leading_ids],
    )
    scenario_events = ledger.events
    scenario_root_hash = ledger.root_hash
    return ScenarioResult(
        scenario_id=scenario.id,
        name=scenario.name,
        outcome_status=outcome,
        engine_status=evaluated.status,
        failed_assumption_ids=sorted(set(scenario.failed_assumption_ids)),
        invalidated_assumption_ids=sorted(invalidated_assumptions),
        removed_alternative_ids=sorted(removed_alternatives),
        eligible_alternative_ids=eligible_ids,
        leading_candidate_ids=leading_ids,
        baseline_leading_candidate_ids=baseline_leaders,
        decision_changed=set(leading_ids) != set(baseline_leaders),
        alternative_scores={
            item.alternative_id: item.total_score
            for item in remaining
        },
        issues=evaluated.issues,
        scenario_fingerprint=scenario_fingerprint,
        algorithm_audit=scenario_events,
        algorithm_audit_root_hash=scenario_root_hash,
        algorithm_audit_verified=verify_algorithm_audit(
            scenario_events,
            scenario_root_hash,
        ),
    )
