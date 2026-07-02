"""
工具函数模块
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib


def generate_report_hash(report: Dict[str, Any]) -> str:
    """
    生成审计报告的哈希值，用于防篡改校验
    
    Args:
        report: 审计报告字典
        
    Returns:
        SHA256哈希值
    """
    # 生成有序的JSON字符串，确保相同内容生成相同哈希
    report_str = json.dumps(report, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(report_str.encode('utf-8')).hexdigest()


def save_report_to_file(report: Dict[str, Any], file_path: str, add_hash: bool = True) -> None:
    """
    保存审计报告到文件
    
    Args:
        report: 审计报告字典
        file_path: 输出文件路径
        add_hash: 是否添加哈希校验值
    """
    output_report = report.copy()
    
    if add_hash:
        output_report["report_hash"] = generate_report_hash(report)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(output_report, f, ensure_ascii=False, indent=2)


def load_report_from_file(file_path: str, verify_hash: bool = True) -> Dict[str, Any]:
    """
    从文件加载审计报告
    
    Args:
        file_path: 报告文件路径
        verify_hash: 是否验证哈希值
        
    Returns:
        审计报告字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    if verify_hash:
        if "report_hash" not in report:
            raise ValueError("Report does not contain hash for verification")
        
        stored_hash = report.pop("report_hash")
        calculated_hash = generate_report_hash(report)
        
        if stored_hash != calculated_hash:
            raise ValueError("Report hash verification failed. The report may have been tampered with.")
        
        # 恢复哈希字段
        report["report_hash"] = stored_hash
    
    return report


def validate_decision_context(context: Dict[str, Any], required_fields: Optional[List[str]] = None) -> bool:
    """
    验证决策上下文的完整性
    
    Args:
        context: 决策上下文
        required_fields: 必填字段列表
        
    Returns:
        是否验证通过
    """
    if required_fields is None:
        required_fields = ["decision_id", "timestamp", "decision_content", "decision_maker"]
    
    for field in required_fields:
        if field not in context:
            raise ValueError(f"Missing required field in decision context: {field}")
    
    return True


def get_version() -> str:
    """
    获取当前组件版本
    
    Returns:
        版本号字符串
    """
    from . import __version__
    return __version__
