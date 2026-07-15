from enum import StrEnum


class DecisionStatus(StrEnum):
    DRAFT = "DRAFT"
    STRUCTURED = "STRUCTURED"
    EVIDENCE_PENDING = "EVIDENCE_PENDING"
    EVALUATED = "EVALUATED"
    AUDIT_FAILED = "AUDIT_FAILED"
    AUDIT_PASSED = "AUDIT_PASSED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class EvaluationMode(StrEnum):
    CONSTRAINT_ONLY = "constraint_only"
    WEIGHTED = "weighted"


class ConstraintKind(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class ConstraintOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"


class EvidenceStatus(StrEnum):
    SUPPLIED = "supplied"
    MISSING = "missing"
    DISPUTED = "disputed"


class AssumptionSource(StrEnum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"


class AlternativeStatus(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    INCOMPLETE = "incomplete"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ScoringRule(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    TARGET_IS_BETTER = "target_is_better"


class CounterfactualStatus(StrEnum):
    LEADER_STABLE = "leader_stable"
    LEADER_CHANGED = "leader_changed"
    NO_VIABLE_ALTERNATIVE = "no_viable_alternative"


class ScenarioOutcomeStatus(StrEnum):
    EVALUATED = "evaluated"
    BLOCKED = "blocked"
    NO_VIABLE_ALTERNATIVE = "no_viable_alternative"


class InformationPriorityTier(StrEnum):
    BLOCKING = "blocking"
    LEADER_EXPOSED = "leader_exposed"
    STRUCTURAL = "structural"
    REVIEW = "review"
