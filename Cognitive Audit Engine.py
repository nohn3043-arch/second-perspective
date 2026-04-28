import uuid
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Callable

@dataclass
class ResponsibilityAccount:
    organization: str
    role: str
    stage: str
    nonce: str = None

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
        
        allowed_stages = self.config.get("allowed_stages", [])
        if account.stage not in allowed_stages:
            raise ValueError(f"Unsupported stage: {account.stage}")

    def register_plugin(self, plugin: AuditPlugin) -> None:
        self.plugins.append(plugin)

    def audit(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        report = {
            "disclaimer": self.config.get("disclaimer", ""),
            "responsibility_account": self.account.__dict__,
            "analysis": {},
            "custom_fields": self.config.get("custom_fields", {})
        }
        for plugin in self.plugins:
            report["analysis"][plugin.name] = plugin.analyze(decision_context)
        return report
