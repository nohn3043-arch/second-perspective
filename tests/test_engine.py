"""End-to-end engine coverage: status transitions, audit trail, requirements."""

from decimal import Decimal

import pytest

from second_perspective.decision.engine import IntelligentDecisionEngine
from second_perspective.decision.policy import DecisionPolicy
from second_perspective.models.enums import (
    AlternativeStatus,
    DecisionStatus,
    EvaluationMode,
)
from second_perspective.models.schemas import Alternative


class TestEngineEvaluate:
    def test_valid_request_passes(self, make_request):
        result = IntelligentDecisionEngine().evaluate(make_request())
        assert result.status == DecisionStatus.HUMAN_APPROVAL_REQUIRED
        assert result.audit_passed is True
        assert result.eligible_alternative_ids == ["S1", "S2"]
        assert result.leading_candidate_ids == ["S1", "S2"]
        assert len(result.input_fingerprint) == 64
        assert result.algorithm_audit_root_hash is not None
        assert len(result.algorithm_audit) > 0
        assert result.objective == "evaluate market entry options"
        assert result.evaluation_as_of.tzinfo is not None

    def test_generates_decision_id_when_missing(self, make_request):
        result = IntelligentDecisionEngine().evaluate(make_request(decision_id=None))
        assert result.decision_id.startswith("DEC-")

    def test_blocking_issue_yields_evidence_pending(
        self, make_request, make_assumption
    ):
        request = make_request(
            assumptions=[
                make_assumption("A1", evidence_ids=["E1"], no_responsibility=True),
            ],
        )
        result = IntelligentDecisionEngine().evaluate(request)
        assert result.status == DecisionStatus.EVIDENCE_PENDING
        assert result.audit_passed is False
        codes = {issue.code for issue in result.issues}
        assert "CRITICAL_ASSUMPTION_NO_OWNER" in codes

    def test_missing_metric_yields_evidence_pending(self, make_request):
        request = make_request(
            alternatives=[
                Alternative(
                    id="S1",
                    name="a",
                    metrics={"budget": 100},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
            ],
        )
        result = IntelligentDecisionEngine().evaluate(request)
        assert result.status == DecisionStatus.EVIDENCE_PENDING
        codes = {issue.code for issue in result.issues}
        assert "MISSING_METRIC" in codes
        assert any(
            "alternatives.S1.metrics.metric_K1" in u
            for u in result.unresolved_variables
        )

    def test_no_eligible_yields_audit_failed(self, make_request, make_constraint):
        request = make_request(
            constraints=[
                make_constraint("C1", metric="budget", operator="lte", expected=1),
            ],
        )
        result = IntelligentDecisionEngine().evaluate(request)
        assert result.status == DecisionStatus.AUDIT_FAILED
        assert result.audit_passed is False
        assert result.eligible_alternative_ids == []

    def test_weighted_mode_scores(self, make_request, make_criterion, make_constraint):
        request = make_request(
            evaluation_mode=EvaluationMode.WEIGHTED,
            criteria=[
                make_criterion("K1", weight="0.5"),
                make_criterion("K2", weight="0.5"),
            ],
            constraints=[
                make_constraint("C1", metric="budget", operator="lte", expected=1000)
            ],
            alternatives=[
                Alternative(
                    id="S1",
                    name="a",
                    metrics={"metric_K1": 80, "metric_K2": 90, "budget": 800},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
                Alternative(
                    id="S2",
                    name="b",
                    metrics={"metric_K1": 60, "metric_K2": 50, "budget": 500},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
            ],
        )
        result = IntelligentDecisionEngine().evaluate(request)
        assert result.status == DecisionStatus.HUMAN_APPROVAL_REQUIRED
        assert result.evaluation_mode == EvaluationMode.WEIGHTED
        assert result.leading_candidate_ids == ["S1"]
        eval_s1 = next(e for e in result.alternatives if e.alternative_id == "S1")
        # normalized(80)=0.8*0.5 + normalized(90)=0.9*0.5 = 0.85
        assert eval_s1.total_score == Decimal("0.85")

    def test_failure_branches_built_for_critical_assumptions(self, make_request):
        result = IntelligentDecisionEngine().evaluate(make_request())
        assert len(result.failure_branches) == 1
        branch = result.failure_branches[0]
        assert branch.assumption_id == "A1"
        assert branch.affected_alternative_ids == ["S1", "S2"]

    def test_trace_contains_all_stages(self, make_request):
        result = IntelligentDecisionEngine().evaluate(make_request())
        stages = {entry.stage for entry in result.trace}
        assert {
            "audit",
            "evaluation",
            "counterfactual",
            "robustness",
            "governance",
        } <= stages

    def test_deterministic_fingerprint(self, make_request):
        req = make_request()
        a = IntelligentDecisionEngine().evaluate(req)
        b = IntelligentDecisionEngine().evaluate(req)
        assert a.input_fingerprint == b.input_fingerprint

    def test_custom_policy_used(self, make_request):
        policy = DecisionPolicy(
            require_all_alternatives_complete=False,
            sensitivity_delta=Decimal("0.05"),
        )
        result = IntelligentDecisionEngine(policy=policy).evaluate(make_request())
        assert result.policy.sensitivity_delta == Decimal("0.05")
