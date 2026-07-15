from __future__ import annotations

from threading import RLock
from typing import Protocol

from .decision.integrity import verify_chain, verify_record
from .models.schemas import DecisionRecord


class DecisionRepository(Protocol):
    def put(self, record: DecisionRecord) -> None: ...

    def get(self, decision_id: str) -> DecisionRecord | None: ...

    def history(self, decision_id: str) -> list[DecisionRecord]: ...


class InMemoryDecisionRepository:
    """Append-only development repository. Replace with durable event storage."""

    def __init__(self):
        self._records: dict[str, list[DecisionRecord]] = {}
        self._lock = RLock()

    def put(self, record: DecisionRecord) -> None:
        with self._lock:
            if not verify_record(record):
                raise ValueError("record_hash does not match the decision record payload")
            decision_id = record.result.decision_id
            history = self._records.setdefault(decision_id, [])
            expected_revision = len(history) + 1
            if record.revision != expected_revision:
                raise ValueError(
                    f"revision must be {expected_revision} for {decision_id}; "
                    f"received {record.revision}"
                )
            if history and record.parent_record_hash != history[-1].record_hash:
                raise ValueError("parent_record_hash does not match the latest revision")
            history.append(record.model_copy(deep=True))

    def get(self, decision_id: str) -> DecisionRecord | None:
        with self._lock:
            history = self._records.get(decision_id, [])
            if history and not verify_chain(history):
                raise ValueError(f"integrity verification failed for {decision_id}")
            return history[-1].model_copy(deep=True) if history else None

    def history(self, decision_id: str) -> list[DecisionRecord]:
        with self._lock:
            history = self._records.get(decision_id, [])
            if not verify_chain(history):
                raise ValueError(f"integrity verification failed for {decision_id}")
            return [record.model_copy(deep=True) for record in history]
