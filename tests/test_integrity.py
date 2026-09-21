"""Decision integrity: fingerprint, record sealing, hash-chain verification."""

import hmac

import pytest

from second_perspective.decision.integrity import (
    fingerprint_request,
    seal_record,
    verify_chain,
    verify_record,
)

HEX64 = "0123456789abcdef" * 4


def _sealed(record):
    return seal_record(record)


class TestFingerprint:
    def test_returns_sha256_hex(self, make_request):
        fp = fingerprint_request(make_request())
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)

    def test_deterministic(self, make_request):
        req = make_request()
        assert fingerprint_request(req) == fingerprint_request(req)

    def test_changes_when_input_changes(self, make_request, make_alternative):
        req1 = make_request()
        req2 = make_request(
            alternatives=[
                make_alternative(
                    "S1",
                    metrics={"metric_K1": 80, "budget": 800},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
                make_alternative(
                    "S2",
                    metrics={"metric_K1": 61, "budget": 500},
                    required_assumptions=["A1"],
                    evidence_ids=["E1"],
                ),
            ],
        )
        assert fingerprint_request(req1) != fingerprint_request(req2)


class TestSealAndVerifyRecord:
    def test_seal_sets_record_hash(self, make_record):
        sealed = _sealed(make_record())
        assert len(sealed.record_hash) == 64

    def test_verify_true_after_seal(self, make_record):
        assert verify_record(_sealed(make_record())) is True

    def test_detects_tampering(self, make_record):
        sealed = _sealed(make_record())
        tampered = sealed.model_copy(update={"revision": 99})
        assert verify_record(tampered) is False

    def test_unsealed_record_verifies_false(self, make_record):
        assert verify_record(make_record()) is False


class TestVerifyChain:
    def test_empty_chain_true(self):
        assert verify_chain([]) is True

    def test_single_sealed_record_true(self, make_record):
        assert verify_chain([_sealed(make_record())]) is True

    def test_two_revisions_true(self, make_record):
        r1 = _sealed(make_record(revision=1))
        r2 = _sealed(make_record(revision=2, parent_record_hash=r1.record_hash))
        assert verify_chain([r1, r2]) is True

    def test_gap_in_revision_fails(self, make_record):
        r1 = _sealed(make_record(revision=1))
        r3 = _sealed(make_record(revision=3, parent_record_hash=r1.record_hash))
        assert verify_chain([r1, r3]) is False

    def test_broken_parent_link_fails(self, make_record):
        r1 = _sealed(make_record(revision=1))
        r2 = _sealed(make_record(revision=2, parent_record_hash=HEX64))
        assert verify_chain([r1, r2]) is False
