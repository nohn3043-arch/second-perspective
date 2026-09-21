"""Shared factories for building valid decision-engine fixtures.

All factories align with the StrictModel validators in
``second_perspective.models.schemas``:

- ID prefix rules: Evidence=E* / Criterion=K* / Constraint=C* /
  Assumption=A* / Alternative=S* / decision_id=DEC-*
- datetime fields must carry a timezone offset
- valid_until > observed_at
- criterion max_value > min_value; TARGET_IS_BETTER requires an in-range
  target_value
- SOFT constraints carry penalty in (0, 1]; HARD constraints carry none
- WEIGHTED mode requires >= 1 criterion with weights summing to 1
- reference validation: dependencies / evidence_ids / required_assumptions
  must resolve to real ids inside the same request
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from second_perspective.models.enums import (
    AssumptionSource,
    ConstraintKind,
    ConstraintOperator,
    EvidenceStatus,
    EvaluationMode,
    ScoringRule,
)
from second_perspective.models.schemas import (
    Alternative,
    Assumption,
    Constraint,
    Criterion,
    DecisionRequest,
    Evidence,
    ResponsibilityRef,
)

TZ = timezone.utc


# ── scalar builders ───────────────────────────────────────────────────


@pytest.fixture
def make_responsibility():
    def _make(owner: str = "ops-lead", source: str = "SOP-001") -> ResponsibilityRef:
        return ResponsibilityRef(owner=owner, source=source)

    return _make


@pytest.fixture
def make_evidence():
    def _make(
        eid: str = "E1",
        status: EvidenceStatus = EvidenceStatus.SUPPLIED,
        observed_at: datetime | None = None,
        valid_until: datetime | None = None,
        responsibility: ResponsibilityRef | None = None,
    ) -> Evidence:
        observed_at = observed_at or datetime(2026, 1, 1, tzinfo=TZ)
        valid_until = valid_until or (observed_at + timedelta(days=30))
        return Evidence(
            id=eid,
            statement=f"evidence {eid} holds",
            source="audit-trail",
            status=status,
            observed_at=observed_at,
            valid_until=valid_until,
            responsibility=responsibility
            or ResponsibilityRef(owner="auditor-1", source="SOP-001"),
        )

    return _make


@pytest.fixture
def make_criterion():
    def _make(
        kid: str = "K1",
        rule: ScoringRule = ScoringRule.HIGHER_IS_BETTER,
        min_value: Decimal | int | float | str = 0,
        max_value: Decimal | int | float | str = 100,
        target_value: Decimal | int | float | str | None = None,
        weight: Decimal | int | float | str = 1,
    ) -> Criterion:
        return Criterion(
            id=kid,
            name=f"criterion {kid}",
            metric=f"metric_{kid}",
            weight=Decimal(str(weight)),
            scoring_rule=rule,
            min_value=Decimal(str(min_value)),
            max_value=Decimal(str(max_value)),
            target_value=(None if target_value is None else Decimal(str(target_value))),
            responsibility=ResponsibilityRef(owner="pm-1", source="SOP-002"),
        )

    return _make


@pytest.fixture
def make_constraint():
    def _make(
        cid: str = "C1",
        metric: str = "budget",
        operator: ConstraintOperator = ConstraintOperator.LTE,
        expected: object = 1000,
        kind: ConstraintKind = ConstraintKind.HARD,
        penalty: Decimal | int | float | str | None = None,
    ) -> Constraint:
        return Constraint(
            id=cid,
            name=f"constraint {cid}",
            kind=kind,
            metric=metric,
            operator=operator,
            expected=expected,
            penalty=None if penalty is None else Decimal(str(penalty)),
            responsibility=ResponsibilityRef(owner="finance", source="SOP-003"),
        )

    return _make


@pytest.fixture
def make_assumption():
    def _make(
        aid: str = "A1",
        critical: bool = True,
        dependencies: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        responsibility: ResponsibilityRef | None = None,
        no_responsibility: bool = False,
    ) -> Assumption:
        assert not (responsibility is not None and no_responsibility), (
            "pass either responsibility or no_responsibility, not both"
        )
        return Assumption(
            id=aid,
            statement=f"assumption {aid}",
            source=AssumptionSource.EXPLICIT,
            falsification_condition=f"metric_{aid} below threshold",
            critical=critical,
            dependencies=list(dependencies or []),
            evidence_ids=list(evidence_ids or []),
            responsibility=(
                None
                if no_responsibility
                else responsibility
                or ResponsibilityRef(owner="eng-lead", source="SOP-004")
            ),
        )

    return _make


@pytest.fixture
def make_alternative():
    def _make(
        sid: str = "S1",
        metrics: dict | None = None,
        required_assumptions: list[str] | None = None,
        evidence_ids: list[str] | None = None,
    ) -> Alternative:
        return Alternative(
            id=sid,
            name=f"alternative {sid}",
            description="generated by conftest",
            metrics=_default_metrics() if metrics is None else dict(metrics),
            required_assumptions=list(required_assumptions or []),
            evidence_ids=list(evidence_ids or []),
        )

    return _make


def _default_metrics() -> dict:
    # K1 -> metric_K1, C1 -> budget
    return {"metric_K1": 80, "budget": 800}


# ── DecisionRecord / DecisionResult builders ──────────────────────────


@pytest.fixture
def make_result(make_responsibility):
    """Build a minimal valid DecisionResult (engine-independent)."""

    def _make(
        decision_id: str = "DEC-TEST-0001",
        objective: str = "evaluate market entry options",
        status: str = "HUMAN_APPROVAL_REQUIRED",
        **overrides,
    ) -> object:
        from second_perspective.models.enums import DecisionStatus
        from second_perspective.models.schemas import (
            DecisionResult,
            PolicySnapshot,
        )

        base = dict(
            decision_id=decision_id,
            status=DecisionStatus(status),
            objective=objective,
            evaluation_mode=EvaluationMode.CONSTRAINT_ONLY,
            audit_passed=status == "HUMAN_APPROVAL_REQUIRED",
            issues=[],
            alternatives=[],
            eligible_alternative_ids=[],
            leading_candidate_ids=[],
            failure_branches=[],
            responsibility_map=[],
            unresolved_variables=[],
            policy=PolicySnapshot(
                policy_id="POL-TEST",
                version="0.3.0",
                require_all_alternatives_complete=False,
                require_critical_evidence_quality=False,
                critical_evidence_quality_threshold=Decimal("0.7"),
                sensitivity_delta=Decimal("0.1"),
            ),
            engine_version="0.0.0-test",
            input_fingerprint="a" * 64,
            evaluation_as_of=datetime(2026, 1, 15, tzinfo=TZ),
        )
        base.update(**overrides)
        return DecisionResult(**base)

    return _make


@pytest.fixture
def make_record(make_request, make_result):
    """Build a valid DecisionRecord (unsealed unless caller seals it)."""

    def _make(
        decision_id: str = "DEC-TEST-0001",
        revision: int = 1,
        parent_record_hash: str | None = None,
        result=None,
        request=None,
    ) -> object:
        from second_perspective.models.schemas import DecisionRecord

        return DecisionRecord(
            request=request or make_request(decision_id=decision_id),
            result=result or make_result(decision_id=decision_id),
            revision=revision,
            parent_record_hash=parent_record_hash,
        )

    return _make


# ── full request ──────────────────────────────────────────────────────


@pytest.fixture
def make_request(
    make_responsibility,
    make_evidence,
    make_criterion,
    make_constraint,
    make_assumption,
    make_alternative,
):
    """Build a valid, fully-specified decision request.

    Default composition (constraint_only mode, both alternatives eligible):
      - alternatives S1/S2 with complete metrics
      - criterion K1 (higher_is_better, 0..100)
      - hard constraint C1 budget <= 1000
      - assumptions A1 (critical) referenced by both alternatives
      - evidence E1 supplied, referenced by A1
    """

    def _make(
        evaluation_mode: EvaluationMode = EvaluationMode.CONSTRAINT_ONLY,
        criteria: list[Criterion] | None = None,
        constraints: list[Constraint] | None = None,
        assumptions: list[Assumption] | None = None,
        alternatives: list[Alternative] | None = None,
        evidence: list[Evidence] | None = None,
        decision_id: str | None = "DEC-TEST-0001",
        **overrides,
    ) -> DecisionRequest:
        if evidence is None:
            evidence = [make_evidence("E1")]
        if assumptions is None:
            assumptions = [make_assumption("A1", evidence_ids=["E1"])]
        if criteria is None:
            criteria = [make_criterion("K1")]
        if constraints is None:
            constraints = [make_constraint("C1", metric="budget")]
        if alternatives is None:
            alternatives = [
                make_alternative(
                    "S1",
                    metrics={"metric_K1": 80, "budget": 800},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
                make_alternative(
                    "S2",
                    metrics={"metric_K1": 60, "budget": 500},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
            ]
        base = dict(
            decision_id=decision_id,
            objective="evaluate market entry options",
            decision_owner=make_responsibility(),
            evaluation_as_of=datetime(2026, 1, 15, tzinfo=TZ),
            evaluation_mode=evaluation_mode,
            criteria=criteria,
            constraints=constraints,
            assumptions=assumptions,
            alternatives=alternatives,
            evidence=evidence,
        )
        base.update(**overrides)
        return DecisionRequest(**base)

    return _make
