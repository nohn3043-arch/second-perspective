# GCAE - AI 安全审计助手

## 这是什么

一个手机 App。用户选择 AI 模型、输入问题，App 调用 AI 获取回答后，自动对回答做认知审计——检测因果链缺陷、认知偏差、安全风险。

## 核心流程

```
用户输入问题 → App 调用 AI API → AI 返回回答 → 自动审计 → 展示风险报告
```

## 支持的 AI 模型

- OpenAI (GPT-4o / GPT-4o-mini)
- Anthropic (Claude 3.5)
- DeepSeek
- 自定义 API（兼容 OpenAI 格式的任意接口）

## 审计维度

| 插件 | 检测内容 |
|------|---------|
| 因果链分析 | 决策-假设-因果-后果的完整性和逻辑性 |
| 认知偏差检测 | 确认偏差、锚定偏差、过度自信、从众效应 |
| 安全风险扫描 | 敏感信息泄露、提示注入、危险操作、信息不确定性 |

## 打包 APK

```bash
# 在 WSL 中
cd /mnt/c/Users/q3265/Documents/GitHub/SPL-audit-engine-apk_build
bash build_apk.sh
```

APK 输出到 `bin/` 目录。

## 文件结构

```
├── main.py                    # App 主程序（UI + AI 调用 + 审计）
├── cognitive_audit_engine/    # 审计引擎核心模块
│   ├── __init__.py
│   ├── core.py               # 引擎核心类
│   └── config.py             # 配置加载器
├── buildozer.spec             # APK 打包配置
├── build_apk.sh               # 打包脚本
└── requirements.txt           # Python 依赖
```

## 技术栈

- Python 3 + Kivy 2.3.0（UI 框架）
- Buildozer（打包工具）
- urllib（网络请求，无额外依赖）
- cognitive_audit_engine（内置审计引擎）
