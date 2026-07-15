from __future__ import annotations

import hashlib
import hmac

from ..canonical import canonical_json
from ..models.schemas import DecisionRecord, DecisionRequest


def fingerprint_request(request: DecisionRequest) -> str:
    payload = request.model_dump(mode="json", exclude={"decision_id"})
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def record_digest(record: DecisionRecord) -> str:
    payload = record.model_dump(mode="json", exclude={"record_hash"})
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def seal_record(record: DecisionRecord) -> DecisionRecord:
    return record.model_copy(update={"record_hash": record_digest(record)})


def verify_record(record: DecisionRecord) -> bool:
    expected = record_digest(record)
    return hmac.compare_digest(record.record_hash, expected)


def verify_chain(records: list[DecisionRecord]) -> bool:
    previous_hash: str | None = None
    for expected_revision, record in enumerate(records, start=1):
        if record.revision != expected_revision:
            return False
        if record.parent_record_hash != previous_hash:
            return False
        if not verify_record(record):
            return False
        previous_hash = record.record_hash
    return True
