import os
import json
from typing import Dict, Any

import openai


class OpenAIAdapter:
    """Simple OpenAI adapter for generating a human-readable audit narrative.

    Requires environment variable `OPENAI_API_KEY` to be set, or pass `api_key`
    when constructing.

    数据出境合规警示：
        默认请求境外 OpenAI 端点，调用即涉及数据出境。境内部署应通过 `api_base`
        指向境内端点（如 DeepSeek、通义千问），并对输入做脱敏处理；若无需
        LLM 摘要，请保持关闭以规避出境风险。
    """

    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo",
                 temperature: float = 0.0, api_base: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set (or api_key not provided)")
        openai.api_key = self.api_key
        if api_base:
            openai.api_base = api_base
        self.model = model
        self.temperature = temperature

    def generate_narrative(self, report: Dict[str, Any]) -> str:
        prompt = (
            "你是审计报告撰写助手。把下面的结构化审计报告转为简明、条理清晰的中文审计摘要，包含：概述、关键发现、风险评级、建议行动项（按优先级）。\n\n"
            f"结构化报告（JSON）：\n{json.dumps(report, ensure_ascii=False, indent=2)}\n\n"
            "请以 Markdown 格式输出，语言为中文。"
        )

        resp = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业审计顾问，输出要结构化且可操作。"},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=800,
        )

        return resp["choices"][0]["message"]["content"]
