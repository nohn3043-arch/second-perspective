"""
审计配置加载模块
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path


class AuditConfigLoader:
    """
    审计配置加载器
    支持从字典、JSON文件、环境变量等多种来源加载配置
    """
    
    @staticmethod
    def load_from_dict(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        从字典加载配置
        
        Args:
            config: 配置字典
            
        Returns:
            验证后的配置字典
        """
        # 配置验证
        required_fields = ["allowed_stages"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")
        
        if not isinstance(config["allowed_stages"], list):
            raise TypeError("allowed_stages must be a list")
        
        return config

    @staticmethod
    def load_from_json(path: str) -> Dict[str, Any]:
        """
        从JSON文件加载配置
        
        Args:
            path: JSON文件路径
            
        Returns:
            验证后的配置字典
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        if file_path.suffix.lower() != ".json":
            raise ValueError("Config file must be a JSON file")
        
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return AuditConfigLoader.load_from_dict(config)
    
    @staticmethod
    def load_from_env(prefix: str = "CAE_") -> Dict[str, Any]:
        """
        从环境变量加载配置
        
        Args:
            prefix: 环境变量前缀，默认为"CAE_"
            
        Returns:
            配置字典
        """
        import os
        
        config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                
                # 尝试解析JSON格式的值
                try:
                    config[config_key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    config[config_key] = value
        
        # 特殊字段类型转换
        if "allowed_stages" in config and isinstance(config["allowed_stages"], str):
            config["allowed_stages"] = [s.strip() for s in config["allowed_stages"].split(",")]
        
        return config
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "allowed_stages": [
                "development",
                "testing",
                "staging",
                "production"
            ],
            "disclaimer": "This audit report is for reference only. All decisions remain the responsibility of the account holder.",
            "custom_fields": {},
            "strict_mode": False,
            "log_level": "INFO"
        }
