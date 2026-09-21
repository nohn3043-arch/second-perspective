"""hub_cli entry-point coverage — build example decision + hub demo printout."""

import pytest


def test_build_example_decision_is_valid_decision_request():
    from second_perspective.hub_cli import _build_example_decision
    from second_perspective.models.schemas import DecisionRequest

    decision = _build_example_decision()
    assert isinstance(decision, DecisionRequest)
    assert decision.objective
    assert len(decision.alternatives) >= 2
    assert len(decision.assumptions) >= 1
    # the fixtures pass the model's own validation rules on construction


def test_quality_helper_ranks_scoring():
    from decimal import Decimal

    from second_perspective.hub_cli import _quality

    q = _quality(Decimal("0.95"), "owner-1")
    assert q.reliability == Decimal("0.95")
    assert q.relevance == Decimal("0.95")
    assert q.assessed_by.owner == "owner-1"


def test_run_hub_demo_prints_full_report(monkeypatch, capsys):
    """End-to-end hub demo: build decision, run hub, print report sections."""
    import second_perspective.hub_cli as hub_cli

    monkeypatch.setattr(
        "sys.argv",
        ["sp-hub-cli"],
    )
    hub_cli.main()
    out = capsys.readouterr().out
    assert "Hub Run ID:" in out
    assert "Report hash:" in out
    assert "Approval:" in out or "--- Scenarios" in out


def test_main_version_flag(monkeypatch, capsys):
    import second_perspective.hub_cli as hub_cli
    from second_perspective.version import VERSION

    monkeypatch.setattr("sys.argv", ["sp-hub-cli", "--version"])
    hub_cli.main()
    assert capsys.readouterr().out.strip() == VERSION
