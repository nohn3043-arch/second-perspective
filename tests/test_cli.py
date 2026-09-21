"""CLI entry point coverage (sp-cli / python -m second_perspective.cli)."""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _example_path(name: str = "market_entry.json") -> Path:
    return REPO_ROOT / "examples" / name


@pytest.mark.skipif(
    not _example_path().exists(), reason="examples/market_entry.json not present"
)
def test_run_demo_default_example(capsys):
    from second_perspective.cli import _run_demo

    _run_demo([])
    out = capsys.readouterr().out
    assert "Decision ID:" in out


@pytest.mark.skipif(
    not _example_path().exists(), reason="examples/market_entry.json not present"
)
def test_run_demo_json_output(capsys):
    import json

    from second_perspective.cli import _run_demo

    _run_demo(["--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["decision_id"]
    from second_perspective.models.enums import DecisionStatus

    assert data["status"] in {s.value for s in DecisionStatus}


@pytest.mark.skipif(
    not _example_path().exists(), reason="examples/market_entry.json not present"
)
def test_run_demo_custom_decision(tmp_path, capsys):
    from second_perspective.cli import _run_demo

    src = _example_path()
    custom = tmp_path / "custom.json"
    custom.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    _run_demo(["--decision", str(custom)])
    assert "Decision ID:" in capsys.readouterr().out


def test_run_demo_version_flag(capsys):
    from second_perspective.cli import _run_demo, VERSION

    _run_demo(["--version"])
    assert capsys.readouterr().out.strip() == VERSION


def test_run_demo_unknown_argument():
    from second_perspective.cli import _run_demo

    with pytest.raises(SystemExit, match="Unknown argument"):
        _run_demo(["--bogus"])


def test_example_path_missing_raises():
    from second_perspective.cli import _example_path

    with pytest.raises(SystemExit, match="Example not found"):
        _example_path("definitely-not-here.json")


def test_load_decision_valid_example():
    from second_perspective.cli import _load_decision

    if not _example_path().exists():
        pytest.skip("examples/market_entry.json not present")
    request = _load_decision(_example_path())
    assert request.objective
    assert len(request.alternatives) >= 2


def test_load_decision_invalid_json(tmp_path):
    from second_perspective.cli import _load_decision

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(Exception):
        _load_decision(bad)


def test_report_subcommand_writes_file(tmp_path, capsys, make_request, monkeypatch):
    from second_perspective.cli import _run_report
    import second_perspective.cli as cli_mod

    # Point --decision at a serialized request so the report path avoids disk deps.
    req_path = tmp_path / "req.json"
    req_path.write_text(make_request().model_dump_json(), encoding="utf-8")
    out = tmp_path / "out.md"

    monkeypatch.chdir(tmp_path)
    _run_report(["--decision", str(req_path), "--out", str(out)])
    assert out.exists()
    assert "NOMOS" in out.read_text(encoding="utf-8") or out.stat().st_size > 0


def test_report_subcommand_version_flag(capsys):
    from second_perspective.cli import _run_report, VERSION

    _run_report(["--version"])
    assert capsys.readouterr().out.strip() == VERSION


def test_report_unknown_argument():
    from second_perspective.cli import _run_report

    with pytest.raises(SystemExit, match="Unknown argument"):
        _run_report(["--nope"])


def test_main_invokes_report(monkeypatch, capsys):
    import second_perspective.cli as cli_mod

    calls = {}

    def fake_report(args):
        calls["args"] = args

    monkeypatch.setattr(cli_mod, "_run_report", fake_report)
    monkeypatch.setattr("sys.argv", ["sp-cli", "report", "--foo"])
    cli_mod.main()
    assert calls.get("args") == ["--foo"]


def test_main_invokes_demo(monkeypatch, capsys):
    import second_perspective.cli as cli_mod

    calls = {}

    def fake_demo(args):
        calls["args"] = args

    monkeypatch.setattr(cli_mod, "_run_demo", fake_demo)
    monkeypatch.setattr("sys.argv", ["sp-cli", "--version"])
    cli_mod.main()
    assert calls.get("args") == ["--version"]


def test_cli_module_runs_as_entrypoint_if_importable():
    # The package's entry point lives in pyproject; just sanity-check module import.
    spec = importlib.util.find_spec("second_perspective.cli")
    assert spec is not None
