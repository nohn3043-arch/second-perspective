"""
第二视角认知审计引擎 (Cognitive Audit Engine)

设计定位：在「第二视角因果与剧情推演」框架下，对决策进行静态诊断与因果重构推演。
核心能力：
  1. 责任闭环锚定 —— 将审计绑定到具体的组织/角色/决策阶段，并附防重放 nonce。
  2. 静态诊断 —— 通过可插拔的分析插件，提取偏见、脆弱性等风险信号。
  3. 因果重构推演 —— 注入修正变量 (delta_vars) 重构逻辑链，并评估系统收敛至目标稳态。

本模块不含任何主观/概率化推测，仅做决定论因果处理。
"""

import uuid
import json
import copy
from dataclasses import dataclass
from typing import Dict, Any, List, Callable, Optional, Protocol


# ==================== LLM 协议与默认实现 ====================

class LLMProvider(Protocol):
    """大模型接口协议：实现此协议的任何类都可注入引擎。"""
    def generate(self, prompt: str, **kwargs) -> str: ...


class OpenAIProvider:
    """使用 urllib 调用 OpenAI 兼容接口的 LLM 实现（零外部依赖）。

    Args:
        api_key:   API 密钥。
        model:     模型名称，如 "gpt-4o"、"deepseek-chat"。
        base_url:  API 基础地址，默认 "https://api.openai.com/v1"。
        timeout:   请求超时（秒）。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 120,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str, **kwargs) -> str:
        import urllib.request
        import urllib.error

        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)

        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            return f"[LLM Error] HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
        except Exception as e:
            return f"[LLM Error] {e}"


@dataclass
class ResponsibilityAccount:
    """责任节点数据类：用于把一次审计绑定到最小决策单元（具体责任节点）。

    Attributes:
        organization: 责任所属组织。
        role:        责任角色（如决策者 / 复核者）。
        stage:       决策阶段（须在 config 的 allowed_stages 内才合法）。
        nonce:       防重放随机串；未显式提供时自动生成，用于审计去重与追溯。
    """
    organization: str
    role: str
    stage: str
    nonce: Optional[str] = None

    def __post_init__(self) -> None:
        # 未提供 nonce 时自动生成 8 位十六进制随机串，保证审计记录唯一可追溯
        if not self.nonce:
            self.nonce = uuid.uuid4().hex[:8]


class AuditConfigLoader:
    """审计配置加载器：从字典或 JSON 文件载入审计运行参数（免责声明、允许阶段、自定义字段等）。"""
    @staticmethod
    def load_from_dict(config: Dict[str, Any]) -> Dict[str, Any]:
        # 配置已是字典时直接透传（保留扩展点：可在此做校验/默认值补全）
        return config

    @staticmethod
    def load_from_json(path: str) -> Dict[str, Any]:
        # 从 JSON 文件读取配置；以 utf-8 解析以支持中文等字符
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)


class AuditPlugin:
    """审计插件：将一个具名分析函数封装为可注册的审计单元。

    Args:
        name:         插件名称，作为报告中的分析键。
        analyze_func: 分析函数，接收 decision_context 并返回任意分析结果（通常为含 status 的字典）。
    """

    def __init__(self, name: str, analyze_func: Callable[[Dict[str, Any]], Any]):
        self.name = name
        self.analyze = analyze_func


class CognitiveAuditEngine:
    """认知审计引擎核心：负责责任锚定、静态诊断与因果重构推演。

    Args:
        account: 责任账户（组织/角色/阶段），用于责任闭环锚定。
        config:  审计配置（免责声明、allowed_stages、custom_fields 等）。
    """

    def __init__(self, account: ResponsibilityAccount, config: Dict[str, Any]):
        self.account = account
        self.config = config
        self.plugins: List[AuditPlugin] = []
        self.llm_provider: Optional[LLMProvider] = None

        # 校验责任阶段合法性：若配置限定了 allowed_stages，阶段不在其中则拒绝初始化
        allowed_stages = self.config.get("allowed_stages", [])
        if allowed_stages and account.stage not in allowed_stages:
            raise ValueError(f"Unsupported stage: {account.stage}")

    def set_llm_provider(self, provider: LLMProvider) -> None:
        """注入大模型接口，启用 LLM 增强语义分析。"""
        self.llm_provider = provider

    def register_plugin(self, plugin: AuditPlugin) -> None:
        # 注册一个审计插件，供后续 audit / reconstruct 调用
        self.plugins.append(plugin)

    def audit(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        静态诊断阶段：提取上下文、遍历注册插件并生成偏见/脆弱性评估报告。

        Args:
            decision_context: 决策上下文（待审计的输入数据）。
        Returns:
            报告字典：含免责声明、责任账户、各插件分析结果、自定义字段。
        """
        report = {
            "disclaimer": self.config.get("disclaimer", ""),          # 免责声明（来自配置）
            "responsibility_account": self.account.__dict__,          # 责任账户快照，用于追溯
            "analysis": {},                                            # 各插件分析结果容器
            "custom_fields": self.config.get("custom_fields", {})      # 配置中的自定义字段透传
        }
        # 遍历所有已注册插件，逐一分析并写入报告
        for plugin in self.plugins:
            report["analysis"][plugin.name] = plugin.analyze(decision_context)

        # LLM 增强语义分析（若已注入 provider）
        if self.llm_provider is not None:
            llm_analysis = self._llm_enhanced_audit(decision_context)
            if llm_analysis:
                report["analysis"]["llm_enhanced"] = llm_analysis

        return report

    def _llm_enhanced_audit(self, decision_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用 LLM 对决策上下文进行语义级偏见/风险分析，返回结构化审计结果。"""
        prompt = (
            "你是一个认知审计专家。请对以下决策上下文进行语义级分析，"
            "识别潜在的认知偏见、逻辑漏洞和脆弱性信号。\n\n"
            f"决策上下文：\n{json.dumps(decision_context, ensure_ascii=False, indent=2)}\n\n"
            "请以 JSON 格式返回分析结果，包含以下字段：\n"
            "- bias_flags: 检测到的偏见列表（每条含 type, evidence, severity）\n"
            "- logic_gaps: 逻辑漏洞列表（每条含 description, impact）\n"
            "- risk_signals: 风险信号列表（每条含 signal, level）\n"
            "- overall_assessment: 总体评估文本"
        )
        try:
            raw = self.llm_provider.generate(prompt, temperature=0.3, max_tokens=4096)
            # 尝试从返回中提取 JSON 块
            result = json.loads(raw)
            if isinstance(result, dict):
                return result
            # 兜底：如果返回的不是 JSON 字典，包装为文本分析
            return {"llm_raw_analysis": raw}
        except Exception:
            return None

    def reconstruct(
        self, 
        decision_context: Dict[str, Any], 
        delta_vars: Dict[str, Any],
        convergence_evaluator: Optional[Callable[[Dict[str, Any], Dict[str, Any]], bool]] = None
    ) -> Dict[str, Any]:
        """
        因果重构推演算子：
        1. 注入修正变量 (delta_vars) 重构逻辑链条
        2. 进行二次反事实校验与审计
        3. 评估系统是否收敛至目标稳态

        Args:
            decision_context:       原始决策上下文。
            delta_vars:             修正变量（注入以重构逻辑链）。
            convergence_evaluator:  可选自定义收敛评估器，签名为 (original_report, reconstructed_report) -> bool。
        Returns:
            推演结果字典：含收敛状态、修正变量、重构上下文及重构报告。
        """
        # 1. 隔离并重构决策上下文：深拷贝避免污染原始输入，再叠加修正变量
        reconstructed_context = copy.deepcopy(decision_context)
        reconstructed_context.update(delta_vars)

        # 2. 获取原始报告与重构后的二次审计报告（对同一组插件做反事实对比）
        original_report = self.audit(decision_context)
        reconstructed_report = self.audit(reconstructed_context)

        # 3. LLM 收敛性语义评估（若已注入 provider）
        llm_convergence = None
        if self.llm_provider is not None:
            llm_convergence = self._llm_convergence_assess(
                original_report, reconstructed_report, delta_vars
            )

        # 3. 收敛性判定：优先使用自定义评估器，否则退回默认阻断状态检测
        if convergence_evaluator:
            is_converged = convergence_evaluator(original_report, reconstructed_report)
        else:
            is_converged = self._default_convergence_check(reconstructed_report)

        return {
            "status": "CONVERGED" if is_converged else "DIVERGED",  # 收敛/发散状态
            "delta_variables": delta_vars,                          # 实际注入的修正变量
            "reconstructed_context": reconstructed_context,          # 重构后的上下文
            "reconstructed_report": reconstructed_report,            # 重构后的审计报告
            "is_converged": is_converged,                           # 布尔收敛标志
            "llm_convergence": llm_convergence,                     # LLM 语义收敛评估（若有）
        }

    def _llm_convergence_assess(
        self,
        original_report: Dict[str, Any],
        reconstructed_report: Dict[str, Any],
        delta_vars: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """使用 LLM 对重构前后的审计报告进行语义级收敛性评估。"""
        prompt = (
            "你是一个因果收敛评估专家。请比较以下两份审计报告（原始 vs 重构后），"
            "判断注入修正变量后系统是否已收敛至目标稳态。\n\n"
            f"修正变量：{json.dumps(delta_vars, ensure_ascii=False)}\n\n"
            f"原始报告：\n{json.dumps(original_report, ensure_ascii=False, indent=2)}\n\n"
            f"重构后报告：\n{json.dumps(reconstructed_report, ensure_ascii=False, indent=2)}\n\n"
            "请以 JSON 格式返回评估结果，包含以下字段：\n"
            "- converged: true/false\n"
            "- reasoning: 评估依据\n"
            "- residual_risks: 残余风险列表（若有）"
        )
        try:
            raw = self.llm_provider.generate(prompt, temperature=0.3, max_tokens=4096)
            return json.loads(raw)
        except Exception:
            return None

    @staticmethod
    def _default_convergence_check(reconstructed_report: Dict[str, Any]) -> bool:
        """
        默认判定逻辑：检查重构后的分析插件输出中是否已无高风险或中断状态。
        只要任一插件结果状态为 BLOCKED / HIGH_RISK / CRITICAL，即判定未收敛。
        """
        analysis = reconstructed_report.get("analysis", {})
        for plugin_name, result in analysis.items():
            # 仅对含 status 字段的字典型结果做判定，避免非预期结构引发异常
            if isinstance(result, dict) and result.get("status") in ["BLOCKED", "HIGH_RISK", "CRITICAL"]:
                return False
        return True
