from __future__ import annotations

from .decision.engine import IntelligentDecisionEngine
from .decision.integrity import seal_record
from .governance.approval import apply_approval
from .models.schemas import (
    ApprovalRequest,
    DecisionRecord,
    DecisionRequest,
)
from .repository import DecisionRepository, InMemoryDecisionRepository


class DecisionNotFoundError(LookupError):
    pass


class DecisionService:
    def __init__(
        self,
        engine: IntelligentDecisionEngine | None = None,
        repository: DecisionRepository | None = None,
    ):
        self.engine = engine or IntelligentDecisionEngine()
        self.repository = repository or InMemoryDecisionRepository()

    def evaluate(self, request: DecisionRequest) -> DecisionRecord:
        result = self.engine.evaluate(request)
        normalized_request = request.model_copy(
            update={
                "decision_id": result.decision_id,
                "evaluation_as_of": result.evaluation_as_of,
            }
        )
        previous = self.repository.get(result.decision_id)
        record = DecisionRecord(
            request=normalized_request,
            result=result,
            revision=(previous.revision + 1) if previous else 1,
            parent_record_hash=previous.record_hash if previous else None,
        )
        record = seal_record(record)
        self.repository.put(record)
        return record

    def get(self, decision_id: str) -> DecisionRecord:
        record = self.repository.get(decision_id)
        if record is None:
            raise DecisionNotFoundError(decision_id)
        return record

    def approve(self, decision_id: str, approval: ApprovalRequest) -> DecisionRecord:
        record = self.get(decision_id)
        updated = apply_approval(record, approval)
        updated = updated.model_copy(
            update={
                "revision": record.revision + 1,
                "parent_record_hash": record.record_hash,
                "record_hash": "",
            }
        )
        updated = seal_record(updated)
        self.repository.put(updated)
        return updated

    def history(self, decision_id: str) -> list[DecisionRecord]:
        if self.repository.get(decision_id) is None:
            raise DecisionNotFoundError(decision_id)
        return self.repository.history(decision_id)
