<h1 style="color: blue; font-style: italic;">所有的不确定性，灾难，痛苦，都源于我们对因果链的未知</h1>

## 项目概述

**全球认知审计引擎（GCAE，Global Cognitive Audit Engine）** 是全球首个中立、离线、与决策无关的认知偏误审计引擎。它在不修改模型内部代码的前提下，为 AI 系统与企业决策提供独立的第三方安全与合规审计。

该引擎通过对隐含假设、客观不确定性与人类认知偏误的系统性识别，为高风险理性决策提供中立、可追溯的结构化支撑。

### 关键成果

✅ **以 95 分的总分通过 IMDA AI Verify 评估**

### 🔗 在线体验

在浏览器中直接体验完整的五算子因果审计流水线 —— 零安装、零数据上传、完全确定性。

🌐 **在线演示**：[https://nohnlins.com/audit/](https://nohnlins.com/audit/)

| 算子 | 代号 | 说明 |
|----------|------|-------------|
| 叙事剥离 | NS | 剥离修辞、情绪与模糊量词，提取逻辑核心 |
| 内隐假设透视 | IAP | 揭示隐藏假设、特权绕过、循环论证 |
| 脆弱性锁存 | LCH | 计算每个假设的 ΔD 崩塌概率，定位最弱变量 |
| 因果链同步 | CCS | 逆反校验 + 反事实验证 + 黑洞检测 |
| 状态锚定 | STATE | 责任锚定 + SHA-256 审计凭证 |

> 完全在客户端运行。你的决策数据永远不会离开浏览器。

---

## 第一个常元公式

# p♾️Q

其中 **p** 代表原则、规则或约束，**Q** 代表结果、状态或后果。符号 **♾️** 表示不间断、连续、不可绕过的因果连接。

若 **p** 与 **Q** 之间的连续性被切断、遮蔽或悄然篡改，系统便不再运行于治理之下，而是运行于叙事之下。

---

## 常元公式

$$\Phi\{f_s, x, y\} \rightarrow \{True, False\}$$

- **Φ** 指结构性审计谓词
- 验证给定决策结构是否满足理性一致性的最低要求
- 基于系统功能 $f_s$ 与输入条件 $x, y$
- 不生成建议或优化 —— 仅返回审计结果

---

## 核心特性

| 特性 | 说明 |
|---------|-------------|
| 🛡️ **中立审计** | 保持 100% 中立的第三方立场，不与任何 LLM 厂商结盟 |
| 🔒 **完全离线** | 无需联网或进行云端数据传输 |
| 🔐 **隐私优先** | 零用户数据收集，本地闭环数据隔离 |
| 🔍 **偏误检测** | 识别隐藏假设、不确定性与认知盲区 |
| 🔧 **不修改模型** | 兼容所有主流 LLM，无需改动源代码 |
| 📊 **结构化分析** | 提供决策结构验证，不下主观结论 |

---

## 架构

### 主要组件

#### 认知审计引擎（`Cognitive Audit Engine.py`）

```python
@dataclass
class ResponsibilityAccount       # 责任追踪

class AuditConfigLoader:          # 配置管理
    - load_from_dict(config)      # 从字典加载
    - load_from_json(path)        # 从 JSON 文件加载

class AuditPlugin:                # 用于可扩展性的插件系统
    - analyze_func                # 自定义分析函数

class CognitiveAuditEngine:       # 核心审计引擎
    - register_plugin()           # 注册分析插件
    - audit()                     # 对决策上下文执行审计
```

#### LLM 适配器（`llm_adapters/openai_adapter.py`）

```python
class OpenAIAdapter:              # OpenAI API 集成
    - generate_narrative()        # 生成审计报告
```

---

## 第二人称视角语言

### 定义

一种专用于决策验证与风险分解的结构化语言。它不做价值判断，不提供优化建议，也不下最终结论。

### 核心结构

一个完整且有效的决策由三个固定部分组成：

- **决策（D）**：可执行的、定义清晰的、责任明确的判断
- **假设前提（A）**：支撑决策有效性的、可被证伪的前置条件
- **分支响应（ΔD）**：当核心假设失效时的调整方案

### 形式化表达

$$\neg A \Rightarrow \Delta D$$

### 标准表达范式

```
决策: D
核心假设: A1, A2, A3

风险分支逻辑:
¬A1 ⇒ ΔD
¬A2 ⇒ ΔD
¬A3 ⇒ ΔD
```

---

## 安装

### 环境要求

- Python 3.8+
- 核心依赖见 `requirements.txt`
- OpenAI 适配器依赖见 `requirements-openai.txt`

### 配置

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装 OpenAI 适配器（可选）
pip install -r requirements-openai.txt
```

---

## 用法

### 基础审计示例

```python
from "Cognitive Audit Engine" import (
    CognitiveAuditEngine,
    ResponsibilityAccount,
    AuditConfigLoader
)

# 初始化责任账户
account = ResponsibilityAccount(
    name="audit_team",
    role="third_party_auditor"
)

# 加载配置
config = AuditConfigLoader.load_from_json("config.json")

# 创建审计引擎
engine = CognitiveAuditEngine(account=account, config=config)

# 注册自定义插件（可选）
def my_analysisPlugin(data):
    # 自定义分析逻辑
    return {"result": "analysis_complete"}

plugin = AuditPlugin(name="custom_analysis", analyze_func=my_analysisPlugin)
engine.register_plugin(plugin)

# 执行审计
decision_context = {
    "decision": "批准 X 项目",
    "assumptions": ["A1", "A2", "A3"],
    "context": {...}
}

result = engine.audit(decision_context)
print(result)  # 返回: {True, False}
```

### 使用 OpenAI 适配器

```python
from llm_adapters.openai_adapter import OpenAIAdapter

# 初始化适配器
adapter = OpenAIAdapter(
    api_key="your-api-key",
    model="gpt-3.5-turbo",
    temperature=0.0
)

# 生成审计叙述
report = {...}  # 审计结果
narrative = adapter.generate_narrative(report)
```

---

## 应用场景

- 🏢 **企业战略** - 重大投资与战略决策
- 🏛️ **政府政策** - 公共政策研究与影响评估
- 🧠 **智库研究** - 研究与分析支撑
- ⚠️ **风险控制** - 机构风险管理
- 🤖 **AI 系统审计** - LLM 输出验证与偏误检测

---

## 许可与授权

本仓库是**全球认知审计引擎（GCAE）**的技术展示。版权 © 2026 上海林铭君华科技有限公司 与 NOHN AI TECHNOLOGY PTE. LTD. 保留所有权利。

| 用户 | 用途 | 许可要求 |
|---|---|---|
| 个人（自然人） | 非商业学术研究 / 学习 / 个人实验 | 依据 [LICENSE](./LICENSE) 中的“个人免费研究许可”**免费** |
| 政府机构 / 事业单位 / 企业 | 任何用途（含内部部署、产品开发、服务提供） | **需事先取得书面付费授权** |

- **个人研究者**可在 [LICENSE](./LICENSE) 下免费将本作品用于非商业研究，但不得用于任何商业目的，亦不得向任何企业或政府机构提供服务。
- **政府 / 企业用户**在签署《商业授权协议》并支付约定费用前，不得复制、部署、运行、集成或分发本作品。
- **申请授权**：
  - 国际 / 全球：[ai@nohnlins.com](mailto:ai@nohnlins.com)
  - 中国：[ai@tx.nohnlins.com](mailto:ai@tx.nohnlins.com)

许可方、适用法律与争议解决依据用户所在地在 [LICENSE](./LICENSE) 中确定：中国境内用户 → 上海林铭君华科技有限公司（适用中国法律）；中国境外用户 → NOHN AI TECHNOLOGY PTE. LTD.（适用新加坡法律，SIAC 仲裁）。

---

## 重要声明

### 法律声明

> 政府、企业与事业单位未经明确书面授权，禁止使用、复制、部署或衍生本项目。

本文档包含原创受版权保护的作品、理论体系、结构化范式与数学校验模型。所有内容均受版权法充分保护。

### 净室实现

任何一方独立开发出核心功能、架构或决策模型实质相似的产品，除非能提供完整、连续、可追溯的证据证明其独立开发，否则应被推定构成实质性衍生侵权。

---

## 联系方式

机构授权、定制集成与商务咨询：

- 📧 邮箱（国际）：ai@nohnlins.com
- 📧 邮箱（中国）：ai@tx.nohnlins.com

---

## 参考资料

- [IMDA AI Verify 评估报告](./IMDA_AI_Verify_Causal_Audit_Report.pdf)
- [语言标准 2026](./language%20Standard/2026)

---

**免责声明**：本语言体系仅应用于决策过程中的结构性审查与分解。它不参与决策制定，亦不干预最终决策。作者不对任何后续执行结果承担法律责任或运营责任。
