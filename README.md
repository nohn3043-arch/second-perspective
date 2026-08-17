<p align="center">
  <img src="https://img.shields.io/badge/causal-audit-D4AF37?style=flat-square" alt="causal-audit">
  <img src="https://img.shields.io/badge/offline-D4AF37?style=flat-square" alt="offline">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
  <img src="https://img.shields.io/badge/second-perspective-language-D4AF37?style=flat-square" alt="second-perspective-language">
</p>

<blockquote align="center">
  <em>全球认知审计引擎（GCAE）· 第二视角语言</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ 关于

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>全球认知审计引擎（GCAE）</strong>是全球首个中立、离线、与决策无关的认知偏差审计引擎。它为 AI 系统与企业决策提供独立的第三方安全与合规审计，且无需修改内部模型代码。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>核心使命</strong>——一切不确定性、一切灾难、一切苦难，最终都源于我们对因果链的无知。引擎通过系统性识别隐含假设、客观不确定性与人类认知偏差，为高风险理性决策提供中立、可追溯的结构支撑。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
✅ <strong>通过 IMDA AI Verify 评估，总分 95</strong>——完整报告见 <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code>。
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ 在线体验

<div style="max-width:880px;margin:0 auto;padding:0 16px">

在浏览器中直接体验完整的五算子因果审计流水线——零安装、零上传、完全确定性：

🌐 **在线演示**：[https://nohnlins.com/audit/](https://nohnlins.com/audit/)

> 完全在客户端运行。你的决策数据永远不会离开浏览器。

</div>

<p align="center">— ✦ —</p>

## ✦ 五算子

<div style="max-width:880px;margin:0 auto;padding:0 16px">

每个算子以插件形式随附在 `plugins/` 中：

| 算子 | 插件 | 说明 |
|---|---|---|
| 叙事剥离（NS） | `plugins/ns.py` | 剥离修辞、情绪与模糊量词，提取逻辑内核 |
| 内隐假设透视（IAP） | `plugins/iap.py` | 揭示隐藏假设、特权绕过、循环论证 |
| 脆弱性闩锁（LCH） | `plugins/lch.py` | 计算每个假设的 ΔD 崩塌概率，找出最脆弱变量 |
| 因果链同步（CCS） | `plugins/ccs.py` | 逆向校验 + 反事实验证 + 黑洞检测 |
| 状态锚定（STATE） | `plugins/state.py` | 责任锚定 + SHA-256 审计证书 |

</div>

<p align="center">— ✦ —</p>

## ✦ 恒常公式

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>p → Q</strong>——其中 <strong>p</strong> 代表原则、规则或约束，<strong>Q</strong> 代表结果、状态或后果。箭头表示不可割裂、连续、不可绕过的因果连接。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
若 p 与 Q 之间的连续性被切断、遮蔽或悄然改变，系统便不再处于治理之下，而处于叙事之中。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>结构审计谓词</strong>——Φ{f_s, x, y} → {True, False}：依据系统函数 f_s 与输入条件 x、y，核验给定决策结构是否满足理性一致的最低要求。它只产出审计结论，不产出建议或优化。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>第二视角决策式</strong>——有效决策是三分结构：决策（D）· 假设前提（A）· 分支响应（ΔD），即 <strong>¬A ⇒ ΔD</strong>（当核心假设失效时，分支响应触发）。
</p>

</div>

## ✦ 核心特性

| 特性 | 说明 |
|---|---|
| 🛡️ **中立审计** | 100% 中立第三方立场，不与任何 LLM 厂商绑定 |
| 🔒 **完全离线** | 无需联网，无云端数据传输 |
| 🔐 **隐私优先** | 零用户数据采集，本地闭环数据隔离 |
| 🔍 **偏差检测** | 识别隐藏假设、不确定性、认知盲区 |
| 🔧 **不修改模型** | 兼容所有主流 LLM，无需改动源代码 |
| 📊 **结构化分析** | 仅做决策结构核验，不产出主观结论 |

<p align="center">— ✦ —</p>

## ✦ 快速开始

```bash
# 主源：GitHub
git clone https://github.com/nohn3043-arch/second-perspective.git
# 镜像：Gitee（本仓库）
# git clone https://gitee.com/nohn-ecosystem/second-perspective.git
cd second-perspective
pip install -r requirements.txt          # 核心依赖
# 可选：pip install -r requirements-openai.txt   # OpenAI 叙事适配器

# 运行五算子端到端演示
python demo_audit.py
```

<p align="center">— ✦ —</p>

## ✦ 使用

<div style="max-width:880px;margin:0 auto;padding:0 16px">

引擎文件按设计使用空格命名——用 `importlib` 加载：

```python
import importlib.util

spec = importlib.util.spec_from_file_location("ca", "cognitive audit engine.py")
ca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ca)

account = ca.ResponsibilityAccount(
    organization="audit_team",
    role="third_party_auditor",
    stage="review",
)

config = ca.AuditConfigLoader.load_from_dict({
    "allowed_stages": ["pre_decision", "in_decision", "post_decision", "review"],
    "disclaimer": "仅作结构审计——不替代人类判断。",
    "custom_fields": {"standard_version": "2026"},
})

engine = ca.CognitiveAuditEngine(account=account, config=config)
engine.load_core_plugins()               # 注册 NS / IAP / LCH / CCS / STATE

report = engine.audit(decision_context)  # 静态诊断

# 因果重构：注入修正变量并测试收敛
result = engine.reconstruct(decision_context, delta_vars={"assumption_x": False})
```

五算子也可作为插件直接导入：

```python
from plugins import (
    NarrativeStripPlugin,
    ImplicitAssumptionPlugin,
    FragilityLatchPlugin,
    CausalChainSyncPlugin,
    StateAnchorPlugin,
)
```

可选的叙事生成适配器见 [`llm_adapters/openai_adapter.py`](llm_adapters/openai_adapter.py)。

</div>

<p align="center">— ✦ —</p>

## ✦ 项目结构

```
second-perspective/
├── cognitive audit engine.py      # 核心引擎（按设计使用空格命名）
├── demo_audit.py                  # 五算子端到端演示
├── plugins/                       # 五算子作为插件
│   ├── ns.py                      #   叙事剥离
│   ├── iap.py                     #   内隐假设透视
│   ├── lch.py                     #   脆弱性闩锁
│   ├── ccs.py                     #   因果链同步
│   └── state.py                   #   状态锚定
├── llm_adapters/openai_adapter.py # 可选 OpenAI 叙事适配器
├── language Standard/             # 语言标准 2026
├── 全新决策结构语言/              # 决策结构语言规范
├── IMDA_AI_Verify_Causal_Audit_Report.pdf
├── requirements.txt · requirements-openai.txt
└── LICENSE
```

<p align="center">— ✦ —</p>

## ✦ 生态

GCAE 是 NOHN AI 生态的一员——围绕第二视角因果审计与确定性执行构建的项目家族：

| 项目 | 仓库 | 定位 |
|---|---|---|
| **Second-Perspective (GCAE)** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective) | 全局认知审计引擎——五算子因果审计内核（IMDA 95/100） |
| **NOMOS** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective)（`Intelligent-Decision-Hub--Nomos` 分支） | 可审计确定性决策中心（IMDA 95/100） |
| **SPL-G1** | [nohn3043-arch/SPL-G1](https://github.com/nohn3043-arch/SPL-G1) | 硬件因果审计可信计算单元（TCU） |
| **SPL-Virtual-World-Base** | [nohn3043-arch/Second-Reality](https://github.com/nohn3043-arch/Second-Reality) | 虚拟世界与元宇宙基础设施（宪法 / 法律 / 桥梁） |
| **Story-Engine** | [nohn3043-arch/story-engine](https://github.com/nohn3043-arch/story-engine) | 长篇叙事一致性引擎 |
| **Antares** | [nohn3043-arch/Antares](https://github.com/nohn3043-arch/Antares) | GFSIP v1.0——带因果审计的联邦稳定互操作协议 |
| **Anthropomorphic-Agent-Engine** | [nohn3043-arch/Anthropomorphic-Agent-Engine](https://github.com/nohn3043-arch/Anthropomorphic-Agent-Engine) | 确定性拟人心理引擎（SPL Pure Core V8.0） |
| **PAGES** | [nohn3043-arch/pages](https://github.com/nohn3043-arch/pages) | NOHN AI 生态官方落地页 |

<p align="center">— ✦ —</p>

## ✦ 许可与授权

本仓库是<strong>全球认知审计引擎（GCAE）</strong>的技术展示。本仓库**非开源**。双轨模式：个人非商业研究免费；政府 / 企业需付费商业授权。详见 [LICENSE](./LICENSE)。

| 用户 | 用途 | 许可要求 |
|---|---|---|
| 个人（自然人） | 非商业学术研究 / 学习 / 个人实验 | [LICENSE](./LICENSE)「个人免费研究许可」下**免费** |
| 政府机关 / 公共机构 / 企业 | 任何用途（含内部部署、产品开发、服务提供） | **须事先签署付费商业授权** |

- **个人研究者**可免费用于非商业研究，但不得用于任何商业用途，也不得向任何企业或政府机构提供服务。
- **政府 / 企业用户**在签署商业授权协议并支付约定费用前，不得复制、部署、运行、集成或分发本工作。
- **申请授权**：国际 / 全球 — [ai@nohnlins.com](mailto:ai@nohnlins.com) · 中国 — [lin@secondai.top](mailto:lin@secondai.top)

许可人、适用法律与争议解决依 [LICENSE](./LICENSE) 按用户所在地确定：中国境内用户 → 上海霖铭骏华科技有限公司（中国法律）；境外用户 → NOHN AI TECHNOLOGY PTE. LTD.（新加坡法律，SIAC 仲裁）。

### 净室声明

任何独立开发出与本工作核心功能、架构或决策模型实质相似产品的当事方，除非能提供完整、连续、可追溯的独立开发证据，否则应被推定为构成实质性衍生侵权。

**免责声明**：本语言系统仅用于决策过程中的结构性审查与拆解。它不参与决策制定，也不干预最终决定。作者对任何后续执行结果不承担法律责任或运营责任。

<p align="center">
  <a href="https://github.com/nohn3043-arch">GitHub</a>
  &nbsp;·&nbsp;
  <a href="https://www.nohnlins.com/">nohnlins.com</a>
  &nbsp;·&nbsp;
  <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center"><sub>NOHN AI · SECOND-PERSPECTIVE</sub></p>
