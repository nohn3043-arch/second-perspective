"""
多场景适配器模块
提供不同部署场景下的适配接口
"""

from typing import Dict, Any, Optional
from .core import CognitiveAuditEngine, ResponsibilityAccount, AuditPlugin
from .config import AuditConfigLoader


class HTTPAdapter:
    """
    HTTP服务适配器
    用于将审计引擎封装为HTTP API服务
    """
    
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        初始化HTTP适配器
        
        Args:
            config_path: 配置文件路径
            config: 配置字典（优先级高于config_path）
        """
        if config:
            self.config = AuditConfigLoader.load_from_dict(config)
        elif config_path:
            self.config = AuditConfigLoader.load_from_json(config_path)
        else:
            self.config = AuditConfigLoader.get_default_config()
        
        self.engines: Dict[str, CognitiveAuditEngine] = {}
        self.plugins: Dict[str, AuditPlugin] = {}
    
    def register_plugin(self, plugin: AuditPlugin) -> None:
        """注册全局可用的审计插件"""
        self.plugins[plugin.name] = plugin
    
    def create_engine(self, account_info: Dict[str, Any]) -> str:
        """
        创建审计引擎实例
        
        Args:
            account_info: 责任账户信息
            
        Returns:
            引擎实例ID
        """
        account = ResponsibilityAccount(**account_info)
        engine = CognitiveAuditEngine(account, self.config)
        
        # 注册所有全局插件
        for plugin in self.plugins.values():
            engine.register_plugin(plugin)
        
        engine_id = account.nonce
        self.engines[engine_id] = engine
        
        return engine_id
    
    def audit(self, engine_id: str, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行审计
        
        Args:
            engine_id: 引擎实例ID
            decision_context: 决策上下文
            
        Returns:
            审计报告
        """
        if engine_id not in self.engines:
            raise ValueError(f"Engine not found: {engine_id}")
        
        return self.engines[engine_id].audit(decision_context)
    
    def get_fastapi_app(self, title: str = "Cognitive Audit Engine API", version: str = "1.0.0"):
        """
        获取FastAPI应用实例
        
        Returns:
            FastAPI应用实例
        """
        try:
            from fastapi import FastAPI, HTTPException
            from pydantic import BaseModel
        except ImportError:
            raise ImportError("FastAPI is required for HTTP adapter. Install with 'pip install fastapi uvicorn'")
        
        app = FastAPI(title=title, version=version)
        
        class AccountInfo(BaseModel):
            organization: str
            role: str
            stage: str
            nonce: Optional[str] = None
        
        class AuditRequest(BaseModel):
            engine_id: str
            decision_context: Dict[str, Any]
        
        @app.post("/engine", response_model=Dict[str, str])
        def create_engine(account: AccountInfo):
            try:
                engine_id = self.create_engine(account.dict())
                return {"engine_id": engine_id}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @app.post("/audit", response_model=Dict[str, Any])
        def audit(request: AuditRequest):
            try:
                return self.audit(request.engine_id, request.decision_context)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/plugins", response_model=Dict[str, List[str]])
        def list_plugins():
            return {"plugins": list(self.plugins.keys())}
        
        @app.get("/health")
        def health_check():
            return {"status": "healthy"}
        
        return app
    
    def run_server(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """
        运行HTTP服务
        
        Args:
            host: 监听地址
            port: 监听端口
            **kwargs: 传递给uvicorn.run的参数
        """
        try:
            import uvicorn
        except ImportError:
            raise ImportError("uvicorn is required to run the HTTP server. Install with 'pip install uvicorn'")
        
        app = self.get_fastapi_app()
        uvicorn.run(app, host=host, port=port, **kwargs)


class CLIAdapter:
    """
    命令行适配器
    用于在命令行环境下执行审计
    """
    
    @staticmethod
    def run_audit(config_path: str, account_info: Dict[str, Any], 
                  decision_context_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        运行命令行审计
        
        Args:
            config_path: 配置文件路径
            account_info: 责任账户信息
            decision_context_path: 决策上下文JSON文件路径
            output_path: 输出报告路径，可选
            
        Returns:
            审计报告
        """
        import json
        
        # 加载配置
        config = AuditConfigLoader.load_from_json(config_path)
        
        # 创建责任账户
        account = ResponsibilityAccount(**account_info)
        
        # 创建审计引擎
        engine = CognitiveAuditEngine(account, config)
        
        # 加载决策上下文
        with open(decision_context_path, 'r', encoding='utf-8') as f:
            decision_context = json.load(f)
        
        # 执行审计
        report = engine.audit(decision_context)
        
        # 输出结果
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report


class LibraryAdapter:
    """
    库调用适配器
    用于作为第三方库嵌入到其他Python项目中
    """
    
    @staticmethod
    def create_audit_engine(organization: str, role: str, stage: str, 
                           config: Optional[Dict[str, Any]] = None,
                           plugins: Optional[List[AuditPlugin]] = None) -> CognitiveAuditEngine:
        """
        创建审计引擎实例（简化接口）
        
        Args:
            organization: 所属组织
            role: 角色
            stage: 所处阶段
            config: 配置字典，可选
            plugins: 审计插件列表，可选
            
        Returns:
            审计引擎实例
        """
        if config is None:
            config = AuditConfigLoader.get_default_config()
        
        account = ResponsibilityAccount(
            organization=organization,
            role=role,
            stage=stage
        )
        
        engine = CognitiveAuditEngine(account, config)
        
        if plugins:
            for plugin in plugins:
                engine.register_plugin(plugin)
        
        return engine
