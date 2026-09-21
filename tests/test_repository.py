"""InMemoryDecisionRepository coverage — put/get/history + tamper detection."""

import pytest

from second_perspective.decision.integrity import seal_record
from second_perspective.repository import InMemoryDecisionRepository


def _sealed(make_record, **overrides):
    return seal_record(make_record(**overrides))


def test_put_and_get_roundtrip(make_record):
    repo = InMemoryDecisionRepository()
    record = _sealed(make_record)
    repo.put(record)
    got = repo.get(record.result.decision_id)
    assert got is not None
    assert got.record_hash == record.record_hash
    assert got.revision == 1


def test_get_unknown_returns_none(make_record):
    repo = InMemoryDecisionRepository()
    assert repo.get("DEC-NOPE-000") is None


def test_history_empty_for_unknown(make_record):
    repo = InMemoryDecisionRepository()
    assert repo.history("DEC-NOPE-000") == []


def test_put_requires_valid_record_hash(make_record):
    repo = InMemoryDecisionRepository()
    record = make_record()  # unsealed record_hash == ""
    with pytest.raises(ValueError, match="record_hash does not match"):
        repo.put(record)


def test_revision_must_be_sequential(make_record):
    repo = InMemoryDecisionRepository()
    repo.put(_sealed(make_record, revision=1))
    with pytest.raises(ValueError, match="revision must be 2"):
        repo.put(_sealed(make_record, revision=3, parent_record_hash="b" * 64))


def test_parent_hash_must_match_latest(make_record):
    repo = InMemoryDecisionRepository()
    repo.put(_sealed(make_record, revision=1))
    with pytest.raises(ValueError, match="parent_record_hash does not match"):
        repo.put(
            _sealed(
                make_record,
                revision=2,
                parent_record_hash="f" * 64,
            )
        )


def test_put_chain_multiple_revisions(make_record):
    repo = InMemoryDecisionRepository()
    r1 = _sealed(make_record, revision=1)
    repo.put(r1)
    r2 = _sealed(make_record, revision=2, parent_record_hash=r1.record_hash)
    repo.put(r2)
    assert repo.get(r1.result.decision_id).revision == 2
    assert [r.revision for r in repo.history(r1.result.decision_id)] == [1, 2]


def test_get_detects_tampering(make_record):
    repo = InMemoryDecisionRepository()
    repo.put(_sealed(make_record))
    chain = repo._records["DEC-TEST-0001"]
    # tamper: flip a field inside the stored record without re-sealing
    tampered = chain[-1].model_copy(update={"revision": 99})
    chain[-1] = tampered
    with pytest.raises(ValueError, match="integrity verification failed"):
        repo.get("DEC-TEST-0001")


def test_get_returns_deep_copy(make_record):
    repo = InMemoryDecisionRepository()
    repo.put(_sealed(make_record))
    got = repo.get("DEC-TEST-0001")
    got.result.leading_candidate_ids.append("S9")
    again = repo.get("DEC-TEST-0001")
    assert "S9" not in again.result.leading_candidate_ids
