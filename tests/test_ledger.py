"""Hash-chained algorithm audit ledger coverage."""

import pytest

from second_perspective.audit.ledger import (
    AlgorithmAuditLedger,
    verify_algorithm_audit,
)


class TestLedgerAppend:
    def test_append_builds_chain(self):
        ledger = AlgorithmAuditLedger()
        e1 = ledger.append(
            stage="evaluate", rule_id="R1", operation="op", inputs={"x": 1}, output=2
        )
        e2 = ledger.append(stage="evaluate", rule_id="R2", operation="op2")
        assert e1.sequence == 1 and e2.sequence == 2
        assert e1.previous_event_hash is None
        assert e2.previous_event_hash == e1.event_hash
        assert len(e1.event_hash) == 64

    def test_root_hash_is_last_event(self):
        ledger = AlgorithmAuditLedger()
        e1 = ledger.append(stage="s", rule_id="r", operation="o")
        e2 = ledger.append(stage="s", rule_id="r2", operation="o")
        assert ledger.root_hash == e2.event_hash

    def test_verify_true(self):
        ledger = AlgorithmAuditLedger()
        ledger.append(stage="s", rule_id="r", operation="o")
        ledger.append(stage="s", rule_id="r2", operation="o")
        assert verify_algorithm_audit(ledger.events, ledger.root_hash) is True

    def test_verify_tampered_output_fails(self):
        ledger = AlgorithmAuditLedger()
        ledger.append(stage="s", rule_id="r", operation="o", output=1)
        events = ledger.events
        tampered = events[0].model_copy(update={"output": 999})
        assert verify_algorithm_audit([tampered]) is False

    def test_verify_sequence_gap_fails(self):
        ledger = AlgorithmAuditLedger()
        e1 = ledger.append(stage="s", rule_id="r", operation="o")
        e2 = ledger.append(stage="s", rule_id="r2", operation="o")
        broken = e2.model_copy(update={"sequence": 3})
        assert verify_algorithm_audit([e1, broken]) is False

    def test_verify_empty_fails(self):
        assert verify_algorithm_audit([]) is False

    def test_ledger_rejects_invalid_initial_events(self):
        e = AlgorithmAuditLedger()
        e.append(stage="s", rule_id="r", operation="o")
        events = e.events
        tampered = events[0].model_copy(update={"operation": "hacked"})
        with pytest.raises(ValueError):
            AlgorithmAuditLedger([tampered])

    def test_events_return_copy(self):
        ledger = AlgorithmAuditLedger()
        ledger.append(stage="s", rule_id="r", operation="o")
        first = ledger.events
        first[0].operation = "mutated"
        assert ledger.events[0].operation == "o"
