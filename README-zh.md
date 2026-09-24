<p align="center">
  <img src="https://img.shields.io/badge/causal-audit-D4AF37?style=flat-square" alt="causal-audit">
  <img src="https://img.shields.io/badge/offline-D4AF37?style=flat-square" alt="offline">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
  <img src="https://img.shields.io/badge/second-perspective-language-D4AF37?style=flat-square" alt="second-perspective-language">
</p>

<blockquote align="center">
  <em>全球认知审计引擎（GCAE）· 第二视角语言</em>
</blockquote>

<p align="center">
[English](README.md) | 简体中文
</p>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ 关于

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>全球认知审计引擎（GCAE）</strong>是全球首个中立、核心离线、决策无关的认知偏差审计引擎。它为 AI 系统与企业决策提供独立第三方安全与合规审计，无需修改内部模型代码。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>核心使命</strong> —— 所有不确定、所有灾难、所有苦难，最终都源于我们对因果链的无知。引擎通过系统性识别内隐假设、客观不确定性与人类认知偏差，为高风险理性决策提供中立、可追溯的结构性支撑。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
✅ <strong>通过 IMDA AI Verify 评估，总分 95</strong> —— 完整报告见 <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code>。
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ 在线演示

<div style="max-width:880px;margin:0 auto;padding:0 16px">

直接在浏览器中体验完整的五算子因果审计流水线 —— 零安装、零上传、完全确定性：

🌐 **在线演示**：[https://nohnlins.com/audit/](https://nohnlins.com/audit/)

> 完全在客户端运行。你的决策数据永远不会离开浏览器。

</div>

<p align="center">— ✦ —</p>

## ✦ 五大算子

<div style="max-width:880px;margin:0 auto;padding:0 16px">

每个算子均以 `plugins/` 下的插件形式提供：

| 算子 | 插件 | 说明 |
|---|---|---|
| 叙事剥离（NS） | `plugins/ns.py` | 剥离修辞、情感与模糊量词；提取逻辑核心 |
| 内隐假设透视（IAP） | `plugins/iap.py` | 揭示隐藏假设、特权绕过与循环论证 |
| 脆弱性锁存（LCH） | `plugins/lch.py` | 计算每个假设的 ΔD 崩塌概率；定位最脆弱变量 |
| 因果链同步（CCS） | `plugins/ccs.py` | 反向验证 + 反事实校验 + 黑洞检测 |
| 状态锚定（STATE） | `plugins/state.py` | 责任锚定 + SHA-256 审计证书 |

</div>

<p align="center">— ✦ —</p>

## ✦ 不变式公式

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>p → Q</strong> —— 其中 <strong>p</strong> 代表原则、规则或约束，<strong>Q</strong> 代表结果、状态或后果。箭头表示不可分割、连续、不可绕过的因果连接。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
如果 p 与 Q 之间的连续性被切断、遮蔽或被悄然改变，系统就不再处于治理之下 —— 它处于叙事之下。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>结构性审计谓词</strong> —— Φ{f_s, x, y} → {True, False}：基于系统函数 f_s 与输入条件 x、y，验证给定决策结构是否满足理性一致性的最低要求。它只产出审计结论，不产出建议或优化。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>第二视角决策公式</strong> —— 一个有效决策是三部分结构：决策（D）· 假设前提（A）· 分支响应（ΔD），即 <strong>非A → ΔD</strong>（当核心假设失效时，分支响应触发）。
</p>

</div>

## ✦ 核心特性

| 特性 | 说明 |
|---|---|
| 🛡️ **中立审计** | 100% 中立第三方立场，不绑定任何 LLM 厂商 |
| 🔒 **核心离线** | 核心审计离线且确定；LLM 增强为可选（默认关闭；开启需国内端点） |
| 🔐 **隐私优先** | 零用户数据收集，本地闭环数据隔离 |
| 🔍 **偏差检测** | 识别隐藏假设、不确定性与认知盲区 |
| 🔧 **无需修改模型** | 兼容所有主流 LLM；无需修改源代码 |
| 📊 **结构化分析** | 仅做决策结构验证；不输出主观结论 |

<p align="center">— ✦ —</p>

## ✦ 快速开始

```bash
# 主仓库：GitHub
git clone https://github.com/nohn3043-arch/second-perspective.git
# 镜像：Gitee
# git clone https://gitee.com/nohn-ecosystem/second-perspective.git
cd second-perspective
pip install -r requirements.txt          # 核心依赖
# 可选：pip install -r requirements-openai.txt   # OpenAI 叙述适配器

# 运行五算子端到端演示
python demo_audit.py
```

<p align="center">— ✦ —</p>

## ✦ 使用方法

<div style="max-width:880px;margin:0 auto;padding:0 16px">

引擎文件按设计使用空格分隔命名 —— 用 `importlib` 加载：

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
    "disclaimer": "Structural audit only — does not replace human judgment.",
    "custom_fields": {"standard_version": "2026"},
})

engine = ca.CognitiveAuditEngine(account=account, config=config)
engine.load_core_plugins()               # 注册 NS / IAP / LCH / CCS / STATE

report = engine.audit(decision_context)  # 静态诊断

# 因果重建：注入修正变量并测试收敛
result = engine.reconstruct(decision_context, delta_vars={"assumption_x": False})
```

五个算子也可以直接作为插件导入：

```python
from plugins import (
    NarrativeStripPlugin,
    ImplicitAssumptionPlugin,
    FragilityLatchPlugin,
    CausalChainSyncPlugin,
    StateAnchorPlugin,
)
```

可选的叙述生成适配器位于 [`llm_adapters/openai_adapter.py`](llm_adapters/openai_adapter.py)。

</div>

<p align="center">— ✦ —</p>

## ✦ 项目结构

```
second-perspective/
├── cognitive audit engine.py      # 核心引擎（空格分隔命名为设计有意为之）
├── demo_audit.py                  # 五算子端到端演示
├── plugins/                       # 五大算子插件
│   ├── ns.py                      #   叙事剥离
│   ├── iap.py                     #   内隐假设透视
│   ├── lch.py                     #   脆弱性锁存
│   ├── ccs.py                     #   因果链同步
│   └── state.py                   #   状态锚定
├── llm_adapters/openai_adapter.py # 可选 OpenAI 叙述适配器
├── language Standard/             # 语言标准 2026
├── 全新决策结构语言/              # 决策结构语言规范
├── IMDA_AI_Verify_Causal_Audit_Report.pdf
├── requirements.txt · requirements-openai.txt
└── LICENSE
```

<p align="center">— ✦ —</p>

## ✦ 生态

GCAE 是 NOHN AI 生态的一员 —— 围绕第二视角因果审计与确定性执行构建的项目家族：

| 项目 | 仓库 | 定位 |
|---|---|---|
| **Second-Perspective (GCAE)** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective) | 全球认知审计引擎 —— 五算子因果审计核心（IMDA 95/100） |
| **NOMOS** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective)（`Intelligent-Decision-Hub--Nomos` 分支） | 可审计确定性决策中心（IMDA 95/100） |
| **SPL-G1** | [nohn3043-arch/SPL-G1](https://github.com/nohn3043-arch/SPL-G1) | 硬件因果审计可信计算单元（TCU） |
| **SPL-Virtual-World-Base** | [nohn3043-arch/Second-Reality](https://github.com/nohn3043-arch/Second-Reality) | 虚拟世界与元宇宙基础设施（宪法 / 法律 / 桥梁） |
| **Story-Engine** | [nohn3043-arch/story-engine](https://github.com/nohn3043-arch/story-engine) | 长篇叙事一致性引擎 |
| **Antares** | [nohn3043-arch/Antares](https://github.com/nohn3043-arch/Antares) | GFSIP v1.0 —— 带因果审计的联邦稳定互操作协议 |
| **Anthropomorphic-Agent-Engine** | [nohn3043-arch/Anthropomorphic-Agent-Engine](https://github.com/nohn3043-arch/Anthropomorphic-Agent-Engine) | 确定性拟人心理学引擎（SPL Pure Core V8.0） |
| **PAGES** | [nohn3043-arch/pages](https://github.com/nohn3043-arch/pages) | NOHN AI 生态官方落地页 |

<p align="center">— ✦ —</p>

## ✦ 许可与授权

本仓库是 <strong>全球认知审计引擎（GCAE）</strong>的技术展示。本仓库 <strong>不是开源软件</strong>。双轨模式：个人非商业研究免费；政府 / 企业使用需付费商业许可。详见 [LICENSE](./LICENSE)。

| 用户 | 用途 | 许可要求 |
|---|---|---|
| 个人（自然人） | 非商业学术研究 / 学习 / 个人实验 | **免费**，依据 [LICENSE](./LICENSE) 中「个人免费研究许可」 |
| 政府机构 / 事业单位 / 企业 | 任何用途（含内部部署、产品开发、服务提供） | **必须事先签署付费商业许可** |

- **个人研究者** 可免费用于非商业研究，但不得用于任何商业目的，也不得向任何企业或政府机构提供服务。
- **政府 / 企业用户** 在签署商业许可协议并支付约定费用前，不得复制、部署、运行、集成或分发本作品。
- **许可申请**：国际 / 全球 — [ai@nohnlins.com](mailto:ai@nohnlins.com) · 中国 — [lin@secondai.top](mailto:lin@secondai.top)

许可方、适用法律与争议解决依用户所在地按 [LICENSE](./LICENSE) 执行：中国境内 → 上海林明钧华科技有限公司（适用中国法律）；中国境外 → NOHN AI TECHNOLOGY PTE. LTD.（适用新加坡法律，SIAC 仲裁）。

- **上海合规说明**：[COMPLIANCE_SHANGHAI](./docs/COMPLIANCE_SHANGHAI.md)
- **数据出境**：LLM 增强默认关闭；开启需国内端点 + 输入脱敏 + 用户同意，必要时依法进行数据出境安全评估。

### 洁净室声明

任何独立开发出与本作品核心功能、架构或决策模型实质相似产品的主体，均推定为构成实质性衍生侵权，除非能提供完整、连续、可追溯的独立开发证据。

**免责声明**：本语言体系仅用于决策过程中的结构性审查与拆解，不参与决策制定，也不干预最终决策。作者对任何后续执行结果不承担法律或运营责任。

<p align="center">
  <a href="https://github.com/nohn3043-arch">GitHub</a>
  &nbsp;·&nbsp;
  <a href="https://www.nohnlins.com/">nohnlins.com</a>
  &nbsp;·&nbsp;
  <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center"><sub>NOHN AI · SECOND-PERSPECTIVE</sub></p>
