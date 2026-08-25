#!/usr/bin/env python3
"""
SPL Cognitive Audit Engine — 五算子端到端验证 Demo

用法:
    python demo_audit.py
"""

import sys
import os

# 把项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from importlib import import_module

# 动态导入（文件名有空格，不能正常 import）
engine_mod = import_module("Cognitive Audit Engine")
CognitiveAuditEngine = engine_mod.CognitiveAuditEngine
ResponsibilityAccount = engine_mod.ResponsibilityAccount
AuditConfigLoader = engine_mod.AuditConfigLoader

from plugins import (
    NarrativeStripPlugin,
    ImplicitAssumptionPlugin,
    FragilityLatchPlugin,
    CausalChainSyncPlugin,
    StateAnchorPlugin,
    ReportRenderer,
)


def main():
    # ── 配置 ──
    config = {
        "allowed_stages": ["pre_decision", "in_decision", "post_decision", "review"],
        "disclaimer": "本审计报告由 SPL Cognitive Audit Engine 生成，仅用于结构性审计，不替代人类判断。",
        "custom_fields": {"standard_version": "2026"}
    }

    account = ResponsibilityAccount(
        organization="测试组织",
        role="third_party_auditor",
        stage="review",
    )

    engine = CognitiveAuditEngine(account=account, config=config)
    # 注册官方五算子插件（引擎无 load_core_plugins，改为显式注册）
    for cls in (
        NarrativeStripPlugin,
        ImplicitAssumptionPlugin,
        FragilityLatchPlugin,
        CausalChainSyncPlugin,
        StateAnchorPlugin,
    ):
        engine.register_plugin(cls())

    # ── 测试用例 1: 带叙事粉饰 + 隐假设 + 缺分支响应 ──
    print("=" * 70)
    print("测试 1: 叙事粉饰 + 隐假设 + 无分支响应")
    print("=" * 70)

    decision_context = {
        "decision": "批准项目X上线",
        "assumptions": [
            "用户需求大概稳定",
            "技术方案可能可行",
            "竞争对手不会快速跟进",
        ],
        "outcome": "项目X按时上线",
        "branches": [],  # 无分支响应 → 系统崩塌风险
        "text": (
            "毫无疑问，项目X应该立即批准上线。"
            "显然，用户需求已经充分验证，专家认为技术方案完全可行。"
            "令人振奋的是，市场前景非常广阔，竞争对手大概不会跟进。"
            "我们一直以来都是行业领先者，必须承认这个决定是正确的。"
        ),
    }

    report = engine.audit(decision_context)

    # 最终裁定与证书位于 STATE 插件输出（analysis 层），非报告顶层
    state = report["analysis"]["STATE"]
    verdict = state["verdict"]
    cert = state["certificate"]

    print(f"\n--- 最终裁定 ---")
    print(f"Level: {verdict['level']}")
    print(f"Summary: {verdict['summary']}")
    print(f"HALT items: {verdict['halt_count']}")
    print(f"WARN items: {verdict['warn_count']}")

    print(f"\n--- 审计证书 ---")
    print(f"Audit ID: {cert.get('audit_id', 'N/A')}")
    print(f"Signature: {cert.get('signature', 'N/A')[:32]}...")

    # ── 各插件详情 ──
    analysis = report["analysis"]

    print(f"\n--- NS (叙事剥离) ---")
    ns = analysis.get("NS", {})
    print(f"Pass: {ns.get('pass')}")
    print(f"Violations: {ns.get('violation_count', 0)}")
    if ns.get("logical_core"):
        print(f"Logical Core: {ns['logical_core'][:120]}...")

    print(f"\n--- IAP (隐假设透视) ---")
    iap = analysis.get("IAP", {})
    print(f"Pass: {iap.get('pass')}")
    print(f"Flags: {iap.get('flag_count', 0)}")
    for f in iap.get("flags", []):
        print(f"  [{f.get('severity')}] {f.get('flag_type')}: {f.get('match','')[:50]}")

    print(f"\n--- LCH (脆弱性对冲) ---")
    lch = analysis.get("LCH", {})
    print(f"Pass: {lch.get('pass')}")
    print(f"System Delta D: {lch.get('system_delta_d', 0)}")
    weakest = lch.get("weakest_variable")
    if weakest:
        print(f"Weakest: A{weakest['index']+1} = '{weakest['assumption'][:40]}' → ΔD={weakest['delta_d']}")

    print(f"\n--- CCS (因果同步) ---")
    ccs = analysis.get("CCS", {})
    print(f"Pass: {ccs.get('pass')}")
    for c in ccs.get("checks", []):
        print(f"  [{c.get('severity')}] {c.get('check')}: {c.get('description','')[:80]}")

    print(f"\n--- STATE (责任锚定) ---")
    st = analysis.get("STATE", {})
    resp = st.get("responsibility", {})
    print(f"Anchor: {resp.get('anchor_status')}")
    print(f"Org: {resp.get('organization')} / Role: {resp.get('role')} / Nonce: {resp.get('nonce')}")

    # ── 测试用例 2: 干净的决策（应该 PASS）──
    print("\n" + "=" * 70)
    print("测试 2: 干净的决策（应 PASS）")
    print("=" * 70)

    clean_context = {
        "decision": "部署服务B到生产环境",
        "assumptions": [
            "服务B通过了全部集成测试",
            "回滚脚本在 staging 环境验证通过",
            "监控告警已配置",
        ],
        "outcome": "服务B在生产环境稳定运行",
        "branches": [
            {"assumption": "服务B通过了全部集成测试", "delta_d": "回滚到上一版本"},
            {"assumption": "回滚脚本在 staging 环境验证通过", "delta_d": "手动回滚+排查"},
            {"assumption": "监控告警已配置", "delta_d": "人工巡检直到监控恢复"},
        ],
        "text": "部署服务B到生产环境。前提：集成测试通过、回滚脚本验证、监控已配置。",
    }

    report2 = engine.audit(clean_context)
    verdict2 = report2["analysis"]["STATE"]["verdict"]
    print(f"\nVerdict: {verdict2['level']}")
    print(f"Summary: {verdict2['summary']}")

    print("\n" + "=" * 70)
    if verdict['level'] == 'AUDIT_HALT' and verdict2['level'] in ('AUDIT_PASS', 'AUDIT_WARN'):
        print("✅ 五算子管线验证通过：脏数据被 HALT，干净数据 PASS/WARN（无致命违规）")
    else:
        print("⚠️  验证异常 — 请检查输出")
    print("=" * 70)

    # ── 双语外壳渲染演示（可选：ReportRenderer 独立于五算子管线）──
    print("\n" + "=" * 70)
    print("双语外壳渲染演示（外壳双语 / 证据正文保原文）")
    print("=" * 70)
    renderer = ReportRenderer()
    zh_view = renderer.render(report, lang="zh")
    en_view = renderer.render(report, lang="en")
    print(f"[zh] 标题: {zh_view['title']}")
    print(f"[en] 标题: {en_view['title']}")
    print("\n--- 英文外壳 (en) 前 10 行 ---")
    for line in renderer.render_text(report, lang="en").splitlines()[:10]:
        print(line)
    # 证明证据正文未被翻译（保留原文）
    ns_core = zh_view["审计算子"]["NS"]["result"].get("logical_core", "")
    print(f"\n[证据正文-原文] NS logical_core: {ns_core[:60]}...")


if __name__ == "__main__":
    main()
