import uuid
import json
import copy
from dataclasses import dataclass
from typing import Dict, Any, List, Callable, Optional


@dataclass
class ResponsibilityAccount:
    organization: str
    role: str
    stage: str
    nonce: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.nonce:
            self.nonce = uuid.uuid4().hex[:8]


class AuditConfigLoader:
    @staticmethod
    def load_from_dict(config: Dict[str, Any]) -> Dict[str, Any]:
        return config

    @staticmethod
    def load_from_json(path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)


class AuditPlugin:
    def __init__(self, name: str, analyze_func: Callable[[Dict[str, Any]], Any]):
        self.name = name
        self.analyze = analyze_func


class CognitiveAuditEngine:
    def __init__(self, account: ResponsibilityAccount, config: Dict[str, Any]):
        self.account = account
        self.config = config
        self.plugins: List[AuditPlugin] = []

        # 校验责任阶段合法性
        allowed_stages = self.config.get("allowed_stages", [])
        if allowed_stages and account.stage not in allowed_stages:
            raise ValueError(f"Unsupported stage: {account.stage}")

    def register_plugin(self, plugin: AuditPlugin) -> None:
        self.plugins.append(plugin)

    def audit(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        静态诊断阶段：提取上下文、遍历注册插件并生成偏见/脆弱性评估报告。
        """
        report = {
            "disclaimer": self.config.get("disclaimer", ""),
            "responsibility_account": self.account.__dict__,
            "analysis": {},
            "custom_fields": self.config.get("custom_fields", {})
        }
        for plugin in self.plugins:
            report["analysis"][plugin.name] = plugin.analyze(decision_context)
        return report

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
        """
        # 1. 隔离并重构决策上下文
        reconstructed_context = copy.deepcopy(decision_context)
        reconstructed_context.update(delta_vars)

        # 2. 获取原始报告与重构后的二次审计报告
        original_report = self.audit(decision_context)
        reconstructed_report = self.audit(reconstructed_context)

        # 3. 收敛性判定（支持自定义评估器或默认阻断状态检测）
        if convergence_evaluator:
            is_converged = convergence_evaluator(original_report, reconstructed_report)
        else:
            is_converged = self._default_convergence_check(reconstructed_report)

        return {
            "status": "CONVERGED" if is_converged else "DIVERGED",
            "delta_variables": delta_vars,
            "reconstructed_context": reconstructed_context,
            "reconstructed_report": reconstructed_report,
            "is_converged": is_converged
        }

    @staticmethod
    def _default_convergence_check(reconstructed_report: Dict[str, Any]) -> bool:
        """
        默认判定逻辑：检查重构后的分析插件输出中是否已无高风险或中断状态。
        """
        analysis = reconstructed_report.get("analysis", {})
        for plugin_name, result in analysis.items():
            if isinstance(result, dict) and result.get("status") in ["BLOCKED", "HIGH_RISK", "CRITICAL"]:
                return False
        return True
