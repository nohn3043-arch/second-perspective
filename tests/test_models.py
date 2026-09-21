"""Model-level validator coverage for second_perspective.models.schemas."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

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
OWNER = ResponsibilityRef(owner="ops", source="SOP-1")


class TestEvidenceValidators:
    def test_rejects_bad_id_prefix(self):
        with pytest.raises(ValidationError):
            Evidence(
                id="e1",
                statement="s",
                source="src",
                responsibility=OWNER,
            )

    def test_rejects_naive_datetime(self):
        with pytest.raises(ValidationError):
            Evidence(
                id="E1",
                statement="s",
                source="src",
                observed_at=datetime(2026, 1, 1),
                responsibility=OWNER,
            )

    def test_rejects_valid_until_before_observed(self):
        with pytest.raises(ValidationError):
            Evidence(
                id="E1",
                statement="s",
                source="src",
                observed_at=datetime(2026, 2, 1, tzinfo=TZ),
                valid_until=datetime(2026, 1, 1, tzinfo=TZ),
                responsibility=OWNER,
            )

    def test_accepts_valid_timeline(self):
        ev = Evidence(
            id="E1",
            statement="s",
            source="src",
            observed_at=datetime(2026, 1, 1, tzinfo=TZ),
            valid_until=datetime(2026, 2, 1, tzinfo=TZ),
            responsibility=OWNER,
        )
        assert ev.status == EvidenceStatus.SUPPLIED


class TestCriterionValidators:
    def _crit(self, **kw):
        base = dict(
            id="K1",
            name="n",
            metric="m",
            weight=Decimal("1"),
            scoring_rule=ScoringRule.HIGHER_IS_BETTER,
            min_value=Decimal("0"),
            max_value=Decimal("100"),
            responsibility=OWNER,
        )
        base.update(kw)
        return Criterion(**base)

    def test_rejects_max_not_greater_than_min(self):
        with pytest.raises(ValidationError):
            self._crit(min_value=Decimal("100"), max_value=Decimal("100"))

    def test_target_rule_requires_target(self):
        with pytest.raises(ValidationError):
            self._crit(scoring_rule=ScoringRule.TARGET_IS_BETTER)

    def test_target_outside_range_rejected(self):
        with pytest.raises(ValidationError):
            self._crit(
                scoring_rule=ScoringRule.TARGET_IS_BETTER,
                target_value=Decimal("150"),
            )

    def test_valid_target_accepted(self):
        c = self._crit(
            scoring_rule=ScoringRule.TARGET_IS_BETTER,
            target_value=Decimal("50"),
        )
        assert c.target_value == Decimal("50")


class TestConstraintValidators:
    def _con(self, **kw):
        base = dict(
            id="C1",
            name="n",
            kind=ConstraintKind.HARD,
            metric="m",
            operator=ConstraintOperator.LTE,
            expected=100,
            responsibility=OWNER,
        )
        base.update(kw)
        return Constraint(**base)

    def test_soft_requires_penalty(self):
        with pytest.raises(ValidationError):
            self._con(kind=ConstraintKind.SOFT)

    def test_hard_forbids_penalty(self):
        with pytest.raises(ValidationError):
            self._con(kind=ConstraintKind.HARD, penalty=Decimal("0.1"))

    def test_valid_soft_constraint(self):
        c = self._con(kind=ConstraintKind.SOFT, penalty=Decimal("0.1"))
        assert c.penalty == Decimal("0.1")


class TestDecisionRequestValidators:
    def _alt(self, sid="S1", **kw):
        base = dict(id=sid, name="n", metrics={"m": 1})
        base.update(kw)
        return Alternative(**base)

    def _req(self, **kw):
        base = dict(
            objective="obj",
            decision_owner=OWNER,
            evaluation_as_of=datetime(2026, 1, 1, tzinfo=TZ),
            alternatives=[self._alt()],
        )
        base.update(kw)
        return DecisionRequest(**base)

    def test_happy_path(self):
        req = self._req(
            decision_id="DEC-TEST-1",
            assumptions=[
                Assumption(
                    id="A1",
                    statement="s",
                    source=AssumptionSource.EXPLICIT,
                    falsification_condition="fc",
                    responsibility=OWNER,
                )
            ],
            alternatives=[self._alt(required_assumptions=["A1"])],
        )
        assert req.decision_id == "DEC-TEST-1"

    def test_duplicate_assumption_ids_rejected(self):
        with pytest.raises(ValidationError):
            self._req(
                assumptions=[
                    Assumption(
                        id="A1",
                        statement="s",
                        source=AssumptionSource.EXPLICIT,
                        falsification_condition="fc",
                        responsibility=OWNER,
                    ),
                    Assumption(
                        id="A1",
                        statement="t",
                        source=AssumptionSource.INFERRED,
                        falsification_condition="fc",
                        responsibility=OWNER,
                    ),
                ]
            )

    def test_unknown_dependency_rejected(self):
        with pytest.raises(ValidationError):
            self._req(
                assumptions=[
                    Assumption(
                        id="A1",
                        statement="s",
                        source=AssumptionSource.EXPLICIT,
                        falsification_condition="fc",
                        dependencies=["A9"],
                        responsibility=OWNER,
                    ),
                ]
            )

    def test_unknown_alternative_assumption_rejected(self):
        with pytest.raises(ValidationError):
            self._req(
                assumptions=[
                    Assumption(
                        id="A1",
                        statement="s",
                        source=AssumptionSource.EXPLICIT,
                        falsification_condition="fc",
                        responsibility=OWNER,
                    ),
                ],
                alternatives=[self._alt(required_assumptions=["A9"])],
            )

    def test_naive_evaluation_as_of_rejected(self):
        with pytest.raises(ValidationError):
            self._req(evaluation_as_of=datetime(2026, 1, 1))

    def test_weighted_requires_criteria(self):
        with pytest.raises(ValidationError):
            self._req(evaluation_mode=EvaluationMode.WEIGHTED)

    def test_weighted_requires_weights_sum_to_one(self):
        with pytest.raises(ValidationError):
            self._req(
                evaluation_mode=EvaluationMode.WEIGHTED,
                criteria=[
                    Criterion(
                        id="K1",
                        name="n",
                        metric="m",
                        weight=Decimal("0.6"),
                        scoring_rule=ScoringRule.HIGHER_IS_BETTER,
                        min_value=Decimal("0"),
                        max_value=Decimal("100"),
                        responsibility=OWNER,
                    )
                ],
            )

    def test_weighted_accepts_sum_to_one(self):
        req = self._req(
            evaluation_mode=EvaluationMode.WEIGHTED,
            criteria=[
                Criterion(
                    id="K1",
                    name="n",
                    metric="m",
                    weight=Decimal("0.4"),
                    scoring_rule=ScoringRule.HIGHER_IS_BETTER,
                    min_value=Decimal("0"),
                    max_value=Decimal("100"),
                    responsibility=OWNER,
                ),
                Criterion(
                    id="K2",
                    name="n2",
                    metric="m2",
                    weight=Decimal("0.6"),
                    scoring_rule=ScoringRule.HIGHER_IS_BETTER,
                    min_value=Decimal("0"),
                    max_value=Decimal("100"),
                    responsibility=OWNER,
                ),
            ],
        )
        assert len(req.criteria) == 2
