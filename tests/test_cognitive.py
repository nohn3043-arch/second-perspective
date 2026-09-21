"""Cognitive audit coverage — engine, plugins, adapter, scanner."""

import os

import pytest

from second_perspective.audit.cognitive import (
    AuditConfigLoader,
    AuditPlugin,
    CognitiveAuditEngine,
    CORE_PLUGINS,
    ResponsibilityAccount,
)
from second_perspective.audit.cognitive.adapter import (
    build_gcae_context,
    run_gcae_audit,
)
from second_perspective.hub.cognitive import CognitiveRiskScanner
from second_perspective.hub.policy import HubPolicy


def _engine(stage: str = "post_decision", **config_overrides):
    config = {
        "allowed_stages": ["pre_decision", "in_decision", "post_decision", "review"],
        "disclaimer": "structural diagnostic only",
        "custom_fields": {"scanner": "test"},
    }
    config.update(config_overrides)
    account = ResponsibilityAccount(
        organization="NOHN AI",
        role="decision_owner",
        stage=stage,
        nonce="deadbeef",
    )
    return CognitiveAuditEngine(account=account, config=config)


def test_engine_runs_core_plugins(make_request, make_result):
    engine = _engine()
    for plugin_cls in CORE_PLUGINS:
        engine.register_plugin(plugin_cls())
    report = engine.audit(
        build_gcae_context(make_request(), make_result()),
        save_log=False,
    )
    assert report["analysis"]["NS"]["pass"] in (True, False)
    analysis = report["analysis"]
    for name in ("NS", "IAP", "LCH", "CCS", "STATE"):
        assert name in analysis
    assert report["disclaimer"] == "structural diagnostic only"
    assert report["custom_fields"]["scanner"] == "test"


def test_engine_state_always_last_no_matter_registration_order():
    engine = _engine()

    class MarkerPlugin(AuditPlugin):
        def __init__(self):
            super().__init__(
                "MARKER",
                lambda ctx: {"position_ok": True},
            )

    # Register STATE first deliberately; engine must move it last.
    engine.register_plugin(CORE_PLUGINS[-1]())  # StateAnchorPlugin
    engine.register_plugin(MarkerPlugin())
    report = engine.audit({"decision": "x"}, save_log=False)
    keys = list(report["analysis"].keys())
    assert keys[-1] == "STATE"
    assert "MARKER" in keys


def test_engine_rejects_unsupported_stage():
    with pytest.raises(ValueError, match="Unsupported stage"):
        _engine(stage="bogus_stage")


def test_engine_registers_custom_plugin():
    engine = _engine()

    def analyzer(ctx):
        return {"status": "PASS", "note": "hello"}

    engine.register_plugin(AuditPlugin("CUSTOM", analyzer))
    report = engine.audit({"decision": "x"}, save_log=False)
    assert report["analysis"]["CUSTOM"] == {"status": "PASS", "note": "hello"}


def test_engine_custom_llm_provider():
    engine = _engine()

    class FakeProvider:
        def generate(self, prompt, **kwargs):
            return '{"converged": true, "reasoning": "ok"}'

    engine.set_llm_provider(FakeProvider())
    report = engine.audit({"decision": "x"}, save_log=False)
    assert report["analysis"]["llm_enhanced"]["converged"] is True


def test_engine_save_log_writes_file(tmp_path, make_request, make_result):
    engine = _engine()
    for plugin_cls in CORE_PLUGINS:
        engine.register_plugin(plugin_cls())
    report = engine.audit(
        build_gcae_context(make_request(), make_result()),
        save_log=True,
        log_dir=str(tmp_path),
    )
    assert "log_path" in report
    assert os.path.exists(report["log_path"])


def test_audit_config_loader_dict_passthrough():
    cfg = {"a": 1}
    assert AuditConfigLoader.load_from_dict(cfg) is cfg


def test_audit_config_loader_json(tmp_path):
    import json

    path = tmp_path / "config.json"
    path.write_text(json.dumps({"disclaimer": "x"}), encoding="utf-8")
    loaded = AuditConfigLoader.load_from_json(str(path))
    assert loaded == {"disclaimer": "x"}


def test_responsibility_account_autogenerates_nonce():
    acct = ResponsibilityAccount(organization="o", role="r", stage="post_decision")
    assert acct.nonce and len(acct.nonce) == 8
    acct2 = ResponsibilityAccount(
        organization="o", role="r", stage="post_decision", nonce="fixed"
    )
    assert acct2.nonce == "fixed"


def test_engine_reconstruct_with_convergence_evaluator():
    engine = _engine()
    for plugin_cls in CORE_PLUGINS:
        engine.register_plugin(plugin_cls())
    result = engine.reconstruct(
        {"decision": "x", "assumptions": []},
        {"decision": "y"},
        convergence_evaluator=lambda orig, rec: True,
    )
    assert result["status"] == "CONVERGED"
    assert result["is_converged"] is True
    assert result["delta_variables"] == {"decision": "y"}


def test_engine_reconstruct_default_diverge():
    engine = _engine()

    class BlockingPlugin(AuditPlugin):
        def __init__(self):
            super().__init__("BLOCK", lambda ctx: {"status": "HIGH_RISK"})

    engine.register_plugin(BlockingPlugin())
    result = engine.reconstruct({"decision": "x"}, {"decision": "y"})
    assert result["is_converged"] is False
    assert result["status"] == "DIVERGED"


def test_build_gcae_context_structure(make_request, make_result):
    ctx = build_gcae_context(make_request(), make_result())
    assert ctx["decision"] == "evaluate market entry options"
    assert ctx["assumptions"] == ["assumption A1"]
    assert ctx["branches"][0]["assumption_id"] == "A1"
    assert "Leading candidate" in ctx["outcome"] or "Decision status" in ctx["outcome"]
    assert ctx["text"].startswith("evaluate market entry options")


def test_run_gcae_audit_returns_typed_report(make_request, make_result):
    report, raw = run_gcae_audit(make_request(), make_result(), HubPolicy())
    assert report.total_findings == len(report.findings)
    assert report.scanner_version == "GCAE-1.0.0"
    assert raw["analysis"]["STATE"]["pass"] in (True, False)


def test_cognitive_risk_scanner_scan(make_request, make_result):
    scanner = CognitiveRiskScanner(HubPolicy())
    report = scanner.scan(make_request(), make_result())
    assert report.scanner_version == "GCAE-1.0.0"


def test_engine_audit_missing_analysis_is_handled():
    engine = _engine()
    report = engine.audit({"decision": "x"}, save_log=False)
    # no plugins registered -> analysis empty but STATE absent
    assert report["analysis"] == {}
