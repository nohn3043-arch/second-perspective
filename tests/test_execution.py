"""Execution audit ledger coverage."""

from decimal import Decimal

from second_perspective.audit.execution import build_execution_audit
from second_perspective.audit.ledger import verify_algorithm_audit
from second_perspective.models.enums import (
    AlternativeStatus,
    CounterfactualStatus,
    DecisionStatus,
    EvaluationMode,
)
from second_perspective.models.schemas import (
    AlternativeEvaluation,
    CounterfactualResult,
    FailureBranch,
    PolicySnapshot,
    RobustnessReport,
)


def _eval(sid: str, status: AlternativeStatus) -> AlternativeEvaluation:
    return AlternativeEvaluation(
        alternative_id=sid,
        status=status,
        hard_constraints_passed=status == AlternativeStatus.ELIGIBLE,
        constraint_checks=[],
        total_score=Decimal("1"),
    )


def _make_args(make_request):
    request = make_request()
    return dict(
        request=request,
        input_fingerprint="a" * 64,
        issues=[],
        evaluations=[_eval("S1", AlternativeStatus.ELIGIBLE)],
        failure_branches=[
            FailureBranch(
                assumption_id="A1",
                expression="¬A1 ⇒ ΔD",
                invalidated_assumption_ids=["A1"],
                affected_alternative_ids=["S1"],
                affected_leading_candidate_ids=["S1"],
                candidate_exposure_ratio=Decimal("1"),
                structural_effect="x",
            )
        ],
        counterfactuals=[
            CounterfactualResult(
                trigger_assumption_id="A1",
                status=CounterfactualStatus.LEADER_CHANGED,
                invalidated_assumption_ids=["A1"],
                removed_alternative_ids=["S1"],
                remaining_eligible_alternative_ids=[],
                baseline_leading_candidate_ids=["S1"],
                counterfactual_leading_candidate_ids=[],
                counterfactual_pareto_frontier_ids=[],
                decision_changed=True,
            )
        ],
        robustness=RobustnessReport(
            pareto_frontier_ids=["S1"],
            fragile_criterion_ids=["K1"],
        ),
        leading_candidate_ids=["S1"],
        status=DecisionStatus.HUMAN_APPROVAL_REQUIRED,
        policy=PolicySnapshot(
            policy_id="POL-TEST",
            version="0.3.0",
            require_all_alternatives_complete=True,
            require_critical_evidence_quality=True,
            critical_evidence_quality_threshold=Decimal("0.7"),
            sensitivity_delta=Decimal("0.1"),
        ),
    )


def test_build_execution_audit_rule_order(make_request):
    ledger = build_execution_audit(**_make_args(make_request))
    rule_ids = [e.rule_id for e in ledger.events]
    assert rule_ids == [
        "INPUT_FINGERPRINT",
        "STRUCTURAL_AUDIT",
        "DETERMINISTIC_EVALUATION",
        "FAILURE_BRANCHES",
        "COUNTERFACTUAL_ANALYSIS",
        "ROBUSTNESS_ANALYSIS",
        "LEADING_CANDIDATE_SELECTION",
        "DECISION_STATUS",
    ]


def test_build_execution_audit_chain_verifies(make_request):
    ledger = build_execution_audit(**_make_args(make_request))
    assert ledger.root_hash is not None
    assert verify_algorithm_audit(ledger.events, ledger.root_hash)


def test_stage_counts_reflect_inputs(make_request):
    args = _make_args(make_request)
    args["evaluations"] = [
        _eval("S1", AlternativeStatus.ELIGIBLE),
        _eval("S2", AlternativeStatus.INCOMPLETE),
    ]
    args["counterfactuals"][0] = args["counterfactuals"][0].model_copy(
        update={"decision_changed": False}
    )
    ledger = build_execution_audit(**args)
    eval_event = ledger.events[2]
    assert eval_event.output == {
        "total_evaluated": 2,
        "eligible": 1,
        "incomplete": 1,
    }
    cf_event = ledger.events[4]
    assert cf_event.output["decision_changed_count"] == 0
    status_event = ledger.events[7]
    assert status_event.output == {"status": "HUMAN_APPROVAL_REQUIRED"}


def test_handles_empty_robustness_fields(make_request):
    args = _make_args(make_request)
    args["robustness"] = RobustnessReport(
        pareto_frontier_ids=[], fragile_criterion_ids=[]
    )
    ledger = build_execution_audit(**args)
    assert ledger.events[5].output["pareto_frontier_size"] == 0


def test_weighted_mode_recorded(make_request):
    args = _make_args(make_request)
    args["request"] = make_request(
        evaluation_mode=EvaluationMode.WEIGHTED, criteria=None, constraints=[]
    )
    ledger = build_execution_audit(**args)
    assert ledger.events[2].inputs["evaluation_mode"] == "weighted"
