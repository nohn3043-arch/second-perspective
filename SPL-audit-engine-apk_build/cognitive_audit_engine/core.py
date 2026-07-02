"""
认知审计引擎核心模块
"""

import uuid
from dataclasses import dataclass
from typing import Dict, Any, List, Callable, Optional


@dataclass
class ResponsibilityAccount:
    """
    责任账户 - 用于标识审计主体的身份与所处阶段
    
    Attributes:
        organization: 所属组织
        role: 角色
        stage: 所处阶段
        nonce: 随机标识，自动生成
    """
    organization: str
    role: str
    stage: str
    nonce: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.nonce:
            self.nonce = uuid.uuid4().hex[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "organization": self.organization,
            "role": self.role,
            "stage": self.stage,
            "nonce": self.nonce
        }


class AuditPlugin:
    """
    审计插件 - 可扩展的审计规则模块
    
    Attributes:
        name: 插件名称
        analyze: 审计分析函数，接收决策上下文，返回审计结果
    """
    def __init__(self, name: str, analyze_func: Callable[[Dict[str, Any]], Any]):
        self.name = name
        self.analyze = analyze_func
    
    def __repr__(self) -> str:
        return f"AuditPlugin(name='{self.name}')"


class CognitiveAuditEngine:
    """
    认知审计引擎核心类
    
    提供决策审计全流程能力，支持插件化扩展审计规则
    """
    
    def __init__(self, account: ResponsibilityAccount, config: Dict[str, Any]):
        """
        初始化审计引擎
        
        Args:
            account: 责任账户信息
            config: 审计配置
        """
        self.account = account
        self.config = config
        self.plugins: List[AuditPlugin] = []
        
        allowed_stages = self.config.get("allowed_stages", [])
        if allowed_stages and account.stage not in allowed_stages:
            raise ValueError(f"Unsupported stage: {account.stage}. Allowed stages: {allowed_stages}")

    def register_plugin(self, plugin: AuditPlugin) -> None:
        """
        注册审计插件
        
        Args:
            plugin: 审计插件实例
        """
        if not isinstance(plugin, AuditPlugin):
            raise TypeError("plugin must be an instance of AuditPlugin")
        
        # 检查插件名称是否重复
        for existing_plugin in self.plugins:
            if existing_plugin.name == plugin.name:
                raise ValueError(f"Plugin with name '{plugin.name}' already registered")
        
        self.plugins.append(plugin)
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        注销审计插件
        
        Args:
            plugin_name: 要注销的插件名称
            
        Returns:
            是否成功注销
        """
        for i, plugin in enumerate(self.plugins):
            if plugin.name == plugin_name:
                del self.plugins[i]
                return True
        return False
    
    def list_plugins(self) -> List[str]:
        """
        获取所有已注册插件的名称列表
        
        Returns:
            插件名称列表
        """
        return [plugin.name for plugin in self.plugins]

    def audit(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行审计流程
        
        Args:
            decision_context: 决策上下文信息
            
        Returns:
            完整的审计报告
        """
        if not isinstance(decision_context, dict):
            raise TypeError("decision_context must be a dictionary")
        
        report = {
            "disclaimer": self.config.get("disclaimer", ""),
            "responsibility_account": self.account.to_dict(),
            "analysis": {},
            "custom_fields": self.config.get("custom_fields", {})
        }
        
        for plugin in self.plugins:
            try:
                report["analysis"][plugin.name] = plugin.analyze(decision_context)
            except Exception as e:
                report["analysis"][plugin.name] = {
                    "error": f"Audit plugin execution failed",
                    "message": str(e),
                    "plugin_name": plugin.name
                }
        
        return report
