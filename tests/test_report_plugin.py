"""Coverage for the optional bilingual report renderer."""

from second_perspective.audit.cognitive.plugins.report import ReportRenderer


def _sample_report():
    return {
        "disclaimer": "demo",
        "responsibility_account": {"organization": "ACME"},
        "custom_fields": {"owner": "ops"},
        "analysis": {
            "NS": {
                "logical_core": "some stripped facts",
                "checks": [{"ok": True}],
            },
            "STATE": {
                "verdict": {
                    "level": "AUDIT_PASS",
                    "summary": "ok",
                    "halt_count": 0,
                    "warn_count": 1,
                    "halt_items": [],
                    "warn_items": ["tip"],
                },
                "certificate": {
                    "audit_id": "AUD-1",
                    "timestamp": "t",
                    "signature": "s",
                    "algorithm": "sha256",
                    "verifiable": True,
                    "note": "",
                },
            },
        },
    }


def test_render_zh_and_en_shells():
    renderer = ReportRenderer()
    zh = renderer.render(_sample_report(), lang="zh")
    assert zh["title"] == "认知审计报告"
    assert zh["责任账户"] == {"组织": "ACME"}
    assert zh["审计算子"]["NS"]["label"] == "叙事剥离"
    assert zh["最终裁定"]["级别"] == "审计通过"
    assert zh["审计证书"]["审计 ID"] == "AUD-1"

    en = renderer.render(_sample_report(), lang="en")
    assert en["title"] == "Cognitive Audit Report"
    assert en["Final Verdict"]["Level"] == "AUDIT PASS"
    assert en["Responsibility Account"] == {"Organization": "ACME"}


def test_render_invalid_lang_falls_back_to_zh():
    renderer = ReportRenderer()
    view = renderer.render(_sample_report(), lang="fr")
    assert view["title"] == "认知审计报告"
    assert view["_meta"]["lang"] == "zh"


def test_render_text_contains_core_sections():
    renderer = ReportRenderer()
    text = renderer.render_text(_sample_report(), lang="zh")
    assert "认知审计报告" in text
    assert "ACME" in text
    assert "叙事剥离" in text
    assert "some stripped facts" in text
