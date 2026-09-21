"""export_expert_report coverage."""

from pathlib import Path

import pytest

from second_perspective.decision.integrity import seal_record
from second_perspective.report import export_expert_report


@pytest.fixture
def sealed_record(make_record):
    def _make(**overrides):
        return seal_record(make_record(**overrides))

    return _make


def test_export_writes_markdown_file(tmp_path, sealed_record):
    out = export_expert_report(
        records=[sealed_record()],
        out_dir=tmp_path,
    )
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "# NOMOS" in text
    assert "DEC-TEST-0001" in text
    assert out.suffix == ".md"


def test_export_accepts_custom_out_path(tmp_path, sealed_record):
    target = tmp_path / "custom" / "report.md"
    out = export_expert_report(
        records=[sealed_record()],
        out_path=target,
    )
    assert out == target
    assert target.exists()
    assert "DEC-TEST-0001" in target.read_text(encoding="utf-8")


def test_export_includes_hub_report_section(tmp_path, sealed_record):
    from second_perspective.hub.integrity import seal_hub_report
    from second_perspective.hub.policy import HubPolicy
    from second_perspective.models.hub import HubReport

    record = sealed_record()
    report = HubReport(
        hub_run_id="HUB-TEST-0001",
        hub_version="0.3.0",
        decision_record=record,
        hub_policy=HubPolicy().snapshot(),
        algorithm_audit_verified=True,
    )
    report = seal_hub_report(report)
    out = export_expert_report(records=[record], hub_report=report, out_dir=tmp_path)
    text = out.read_text(encoding="utf-8")
    assert "HUB-TEST-0001" in text
    assert "Hub" in text


def test_export_empty_records_raises(tmp_path):
    with pytest.raises(ValueError, match="at least one decision record"):
        export_expert_report(records=[], out_dir=tmp_path)


def test_export_flagged_when_tampered(tmp_path, sealed_record):
    record = sealed_record()
    record = record.model_copy(update={"revision": 42})
    out = export_expert_report(records=[record], out_dir=tmp_path)
    text = out.read_text(encoding="utf-8")
    assert "FAIL" in text


def test_export_hub_report_verification_flag(tmp_path, sealed_record):
    from second_perspective.hub.policy import HubPolicy
    from second_perspective.models.hub import HubReport

    record = sealed_record()
    report = HubReport(
        hub_run_id="HUB-TEST-0002",
        hub_version="0.3.0",
        decision_record=record,
        hub_policy=HubPolicy().snapshot(),
        algorithm_audit_verified=True,
    )  # unsealed -> verify fails
    out = export_expert_report(records=[record], hub_report=report, out_dir=tmp_path)
    text = out.read_text(encoding="utf-8")
    assert "FAIL" in text
