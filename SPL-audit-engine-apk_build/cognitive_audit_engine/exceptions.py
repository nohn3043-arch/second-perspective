"""
认知审计引擎自定义异常类
"""


class CognitiveAuditError(Exception):
    """认知审计引擎基础异常类"""
    pass


class ConfigError(CognitiveAuditError):
    """配置相关异常"""
    pass


class PluginError(CognitiveAuditError):
    """插件相关异常"""
    pass


class AuditExecutionError(CognitiveAuditError):
    """审计执行过程异常"""
    pass


class ResponsibilityAccountError(CognitiveAuditError):
    """责任账户相关异常"""
    pass


class StageNotAllowedError(CognitiveAuditError):
    """阶段不允许异常"""
    pass
