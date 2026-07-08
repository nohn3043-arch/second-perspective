import os
import json
from pprint import pprint
import importlib.util
from pathlib import Path

from llm_adapters.openai_adapter import OpenAIAdapter


# 动态加载有空格的模块文件 `Cognitive Audit Engine.py`
BASE_DIR = Path(__file__).resolve().parents[1]
ENGINE_PATH = BASE_DIR / "Cognitive Audit Engine.py"
spec = importlib.util.spec_from_file_location("cog_engine", str(ENGINE_PATH))
cog_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cog_engine)


def sample_plugin(decision_context):
    # 简单示例：基于输入判断数据是否包含 PII
    text = decision_context.get("text", "")
    findings = {}
    if "身份证" in text or "身份证号" in text:
        findings["pii"] = {"present": True, "detail": "发现可能的身份证相关字段"}
    else:
        findings["pii"] = {"present": False}
    return findings


def main():
    # 假定已设置 OPENAI_API_KEY
    adapter = OpenAIAdapter()

    account = cog_engine.ResponsibilityAccount(organization="Acme", role="Auditor", stage="pre-deploy")
    config = cog_engine.AuditConfigLoader.load_from_dict({
        "allowed_stages": ["pre-deploy", "post-deploy"],
        "disclaimer": "这是自动生成的初步审计意见。",
    })

    engine = cog_engine.CognitiveAuditEngine(account, config)
    engine.register_plugin(cog_engine.AuditPlugin("PII Check", sample_plugin))

    decision_context = {"text": "用户提供了身份证号: 123456789"}
    report = engine.audit(decision_context)

    narrative = adapter.generate_narrative(report)

    print("--- 结构化报告 ---")
    pprint(report)
    print("--- 模型生成的摘要 ---")
    print(narrative)


if __name__ == "__main__":
    main()
