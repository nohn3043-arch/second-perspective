<p align="center">
  <img src="assets/banner.png" alt="NOMOS 横幅" style="width:100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-D4AF37?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/framework-v0.4.0-D4AF37?style=flat-square" alt="framework-v0.4.0">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
</p>

<p align="center">
[English](README.md) | 简体中文
</p>

<blockquote align="center">
  <em>NOMOS · v0.4.0 —— 带 LLM 护栏的二阶因果决策框架</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ 关于

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 是一个 <strong>二阶因果决策框架</strong>，内置可审计的确定性核心与显式 LLM 护栏。在新加坡 <strong>IMDA AI Verify</strong> 合规评估中获得 <strong>95/100</strong> 分。引擎将结构化评估、细粒度算法审计、声明式假设交互（二阶因果组合）、形式化有界三层重建（含确定性收敛证明）、反事实重选、声明场景压力测试、结构化认知挑战、信息优先级排序与人工治理统一为一份哈希链式报告。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
它从不编造缺失的事实、权重、阈值、责任方、证据、概率 <em>或交互强度</em>。二阶效应（协同、冗余、放大）必须由 <strong>责任方显式声明</strong> —— 引擎从不估计或学习它们。LLM 被限制在三级权限区域（标注 / 提案 / 叙述），永远不能自行翻转状态、裁决或修改权重。它在已声明输入下产生候选方案，最终裁决始终保留在算法之外。
</p>

<p align="center">
  <img src="assets/overview.png" alt="NOMOS 总览" style="width:100%">
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ 内置通用审计引擎

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 搭载一个 <strong>通用审计引擎</strong> —— 而非事后补丁。审计轨迹内建于确定性核心：每个决策、假设、约束与因果步骤都被记录、哈希链接，并按设计可独立验证。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
在新加坡 <strong>IMDA AI Verify</strong> 因果审计赛道获得 <strong>95/100</strong> 分。完整合规报告作为 <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code> 随附。
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ 企业集成

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 不是现有 ERP/CRM/风控/合规/投决/HR/项目审批系统的替代品。它是嵌入其后的 <strong>确定性决策内核</strong>：每个上游系统提交带显式声明交互与责任方的结构化请求；NOMOS 返回候选集、反事实、哈希链审计轨迹与形式化收敛状态；最终裁决始终由人签名后再回流到下游审计、审批与报告流中。
</p>

```text
企业管理系统（ERP/CRM/风控/合规/投决/HR/项目审批）
        │
        │  提交结构化决策请求 + 已声明的交互 + 责任人
        ▼
   ┌─────────────────┐
   │  NOMOS v0.4     │  ← 确定性决策内核（本仓库）
   │  - 一阶失效     │     输出：候选集 + 反事实 + 审计链 + 收敛状态
   │  - 二阶交互     │
   │  - 三层重建     │     不输出最终结论——结论由人签
   │  - LLM 护栏     │
   └─────────────────┘
        │
        ▼
   审计留痕 / 审批流 / 合规报告 / LLM 辅助叙述（T3）
```

</div>

<p align="center">— ✦ —</p>

## ✦ v0.4 新特性 —— 二阶因果框架

<div style="max-width:880px;margin:0 auto;padding:0 16px">

v0.4 是首个系统地推理 <strong>假设与假设之间的交互</strong>（而非将失效视为独立事件）的版本，将迭代重建循环锚定到 <strong>形式化分类的收敛状态</strong>（已证明，非启发式），并将 LLM 置于 <strong>三级权限闸门</strong> 之后，可证明地防止 LLM 输出成为裁决。

- **假设交互层**（`interaction/`）—— 已声明的二阶效应（协同 / 冗余 / 放大），含四条不变式：
  - **I-1 非推测性** —— 每个交互强度 Δ 均由责任方声明；引擎从不估计或学习 Δ。
  - **I-2 阶数守恒** —— 交互仅在 *所有* 成员假设同时失效时触发；部分失效不触发二阶效应。
  - **I-3 效应有界** —— 累积交互效应 ≤ `amplification_ceiling × Σ|一阶|`；冗余（负向）交互不作下限钳制，允许真实阻尼。
  - **I-4 单调性** —— 扩大失效集合永远不会「取消触发」已触发的交互（并集语义）。
- **形式化收敛引擎**（`convergence/`）—— 用五态分类（`FIXED_POINT` / `NO_GAIN` / `BUDGET_EXHAUSTED` / `DIVERGED` / `BLOCKED`）取代启发式停止检查，由三条可验证命题（P-1 终止性、P-2 不动点、P-3 效应有界）支撑。`is_true_convergence` 防范将预算耗尽误分类为收敛的经典 bug。
- **LLM 合规层**（`llm_compliance/`）—— 三级权限（T1 标注 / T2 提案 / T3 叙述）、三条不变式（区域隔离、不裁决、强度剥离），以及带出处追踪的 `LLMGate`，在每个 LLM 响应触及决策图前剥除其结构权力。
- **核心集成** —— `DecisionRequest` 新增可选 `interaction_declaration` 字段（默认 `None`，完全向后兼容）；`invalidation_closure_with_interaction()` 将一阶闭包与二阶联合效应组合；会话引擎将停止条件检查委托给形式化 `ConvergenceChecker`。
- **向后兼容保留** —— 不提供 `interaction_declaration` 时，引擎行为与 v0.3 完全一致。未移除或重命名任何现有 API。GCAE 审计引擎未改动。

测试：402 项通过（新增 122 项），0 失败。完整变更日志：[`CHANGELOG.md`](./CHANGELOG.md)。
架构文档：[`docs/INTELLIGENT_DECISION_HUB_V0_4.md`](docs/INTELLIGENT_DECISION_HUB_V0_4.md)（新增）· v0.3 归档：[`docs/INTELLIGENT_DECISION_HUB_V0_3.md`](docs/INTELLIGENT_DECISION_HUB_V0_3.md)。

### v0.3 新特性

- 每个主要确定性操作的哈希链审计事件
- 约束与准则计算的显式操作数和输出
- 传递假设失效后的真实候选重选
- 用户声明的压力场景（失效假设、指标覆盖）
- 不推断任何心理状态的确定性认知风险挑战层
- 优先级化的信息获取与评审队列
- `IntelligentDecisionHub` 编排器与密封的 `HubReport`
- 基线与场景运行中的完整审计账本
- 新增 `POST /v1/hub/analyze`，同时保留全部 v0.2 端点

</div>

## ✦ 三层因果重建（有界收敛 + 人工闸门）

<div style="max-width:880px;margin:0 auto;padding:0 16px">

新增于 `hub/session.py`（`ReconstructionSessionEngine`）与 `decision/reconstruction.py`（`reconstruct_with_delta`）：原先一次性的因果重建升级为 **有界、哈希链式、人工闸门的迭代过程**。

每轮运行三个因果算子：

1. **前向失效传播** —— `invalidation_closure` 将已声明的假设失效向前传播，丢弃失去该假设支撑的备选方案。
2. **反向根因追踪** —— 现有的反向 BFS 将偏差信号追溯到根因假设候选集。
3. **Δ 重建** —— 将已声明的修正变量（`DeltaVar`）应用于请求副本，重新运行确定性评估器，并判断领先候选集的收敛性。

设计不变式（与 NOMOS 核心一致）：

- **不猜测** —— 每个假设都是候选；由人决定。引擎从不自动循环。
- **确定性** —— 每轮完全派生自已声明的输入。
- **可审计** —— 每轮与上一轮哈希链接；整个会话形成 `session_root_hash`。
- **有界** —— 受 `max_iterations` 与 `max_evidence_requests` 限制。
- **人工闸门** —— `advance()` 恰好执行一轮后停在 `AWAITING_HUMAN`；仅人工决策（`approve` / 提供证据 / 拒绝）可进入下一轮。

停止条件由 `ConvergenceChecker` **形式化分类** 为五种状态：
- **真收敛**：`FIXED_POINT`（候选集与上一轮相同 —— P-2 证明）或 `NO_GAIN`（无未解决分支）。
- **非收敛**：`BUDGET_EXHAUSTED`（预算耗尽但未达不动点 —— 明确 *不是* 收敛，不得如此报告）、`DIVERGED`（预算尚有但仍在变化）、`BLOCKED`（遇到结构性障碍，需要人工介入）。

```python
from second_perspective.models import DecisionRequest, DeviationSignal, DeltaVar
from second_perspective.hub.session import ReconstructionSessionEngine

engine = ReconstructionSessionEngine()
session = engine.start(request, signals, max_iterations=5)
session = engine.advance(session)                                   # 第 1 轮：三层重建
session = engine.advance(session, [                                 # 注入已声明的修正
    DeltaVar(path="A2", value=None, reason="...", responsibility="..."),
])
session = engine.human_decision(session, approved=True)             # 人工签章
print(session.session_root_hash)
```

`DeltaVar` 的路径可取三种形式：`"A2"`（证伪一个假设，通过依赖图传播）、`"criteria.K1.weight"`（改写准则权重）、`"alternatives.S1.metrics.cost"`（改写备选方案指标）。引擎逐字镜像每个已声明的 `DeltaVar`，从不编造修正。

</div>

## ✦ 架构

```text
HubAnalysisRequest（+ 可选 InteractionDeclaration）
  -> 决策核心
       -> 结构 / 证据审计
       -> 硬 + 软约束评估
       -> 归一化评分
       -> 因果失效（一阶）
       -> 假设交互层（二阶：合取 / 析取）
            -> I-1 非推测 · I-2 阶数守恒 · I-3 效应有界 · I-4 单调
       -> 三层重建（前向 / 后向 / Δ）
            -> 形式化收敛检查器（P-1/P-2/P-3 → 五态分类）
       -> 反事实重选
       -> Pareto + 权重敏感度
       -> 哈希链算法审计
  -> LLM 闸门（T1 标注 / T2 提案 / T3 叙述；带出处追踪、状态剥离）
  -> 声明场景压力运行
  -> 结构化认知风险挑战
  -> 信息优先级队列
  -> 仅追加 DecisionRecord
  -> 密封 HubReport（session_root_hash）
  -> 人工批准 / 拒绝（最终裁决始终在算法之外）
```

## ✦ 安装与测试

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## ✦ 运行演示

**核心决策内核**：

```bash
nomos-demo
```

打印人类可读的决策摘要。用 `--decision <file>` 运行 `examples/` 中的任意决策 JSON（如 `nomos-demo --decision examples/baidu_org.json`），`--json` 输出完整机器可读结果：

```bash
nomos-demo --decision examples/baidu_org.json --json
```

**NOMOS（智能决策中心）**，含两个压力场景：

```bash
nomos-hub-demo
```

## ✦ Python 用法

```python
from second_perspective import IntelligentDecisionHub
from second_perspective.models import HubAnalysisRequest

request = HubAnalysisRequest.model_validate(
    {
        "decision": decision_payload,
        "scenarios": [
            {"id": "SC1", "name": "关键假设失效", "failed_assumption_ids": ["A1"]},
            {"id": "SC2", "name": "成本冲击", "metric_overrides": {"S2": {"capital_required": 6000000}}},
        ],
    }
)
report = IntelligentDecisionHub().analyze(request)
```

返回的报告包含基线决策记录、场景结果、认知发现、信息优先级、算法账本验证状态、策略快照与报告哈希。

## ✦ 运行 API

本地开发无密钥运行：

```bash
export SP_ENV=development
uvicorn second_perspective.api.main:app --reload
```

生产环境无密钥拒绝启动：

```bash
export SP_ENV=production
export SP_API_KEY="replace-with-a-strong-secret"
uvicorn second_perspective.api.main:app --host 0.0.0.0 --port 8000
```

受保护客户端发送 `Authorization: Bearer <SP_API_KEY>`。

端点：

- `GET /health`
- `GET /v1/auth/me`
- `POST /v1/hub/analyze`
- `GET /v1/hub/reports/{hub_run_id}`
- `POST /v1/decisions/evaluate`
- `GET /v1/decisions/{decision_id}`
- `GET /v1/decisions/{decision_id}/history`
- `POST /v1/decisions/{decision_id}/approval`

可选 PostgreSQL 持久化：设置 `SP_DATABASE_DSN`（需 `asyncpg`）；OIDC 感知身份：设置 `SP_OIDC_ISSUER`。

## ✦ 重新生成 OpenAPI Schema

```bash
SP_PUBLIC_BASE_URL=https://decision.example.com \
python scripts/export_openapi.py
```

## ✦ 兼容性

所有 v0.2 决策请求与端点保持有效。响应新增 `counterfactuals`、`algorithm_audit`、`algorithm_audit_root_hash`。严格反序列化响应字段的客户端需更新模型。

## ✦ 生产边界

v0.4 是一个功能完整的 *确定性决策框架* 核心 —— 二阶因果层、形式化收敛与 LLM 护栏均为生产级。它还不是完整的多租户企业控制平面：默认存储仍为进程内内存。生产部署需要持久化事件存储、OIDC 与授权强制执行、租户隔离、KMS 签名、限流、可观测性、备份、迁移与领域控制包。

硬性边界（不变式，非未来工作）：
- 引擎从不估计缺失的交互强度、权重、概率或责任方。
- **LLM 永不裁决**：T2 提案需要显式人工批准；T3 叙述从决策图中剥离；任何 LLM 输出都不能翻转假设状态或备选方案排名。
- `BUDGET_EXHAUSTED` 被报告为 *非收敛*；客户端不得将其误标为收敛。
- 认知扫描器仅挑战结构性风险。它不诊断人、不读取动机，也不替代法律、医疗、金融或安全专业人士。

## ✦ 项目结构

```
nomos/
├── pyproject.toml              # 包名：nomos-decision-engine v0.4.0
├── CHANGELOG.md                # 版本化变更日志
├── src/second_perspective/
│   ├── cli.py / hub_cli.py     # 演示入口（nomos-demo / nomos-hub-demo）
│   ├── service.py / repository.py / canonical.py / version.py
│   ├── api/                    # FastAPI：main.py, security.py
│   ├── audit/                  # 审计器、执行、图、账本
│   ├── convergence/            # 检查器（五态分类）、命题（P-1/P-2/P-3）、枚举
│   ├── decision/               # 因果、反事实、引擎、评估器、
│   │                           #   完整性、策略、鲁棒性、选择、
│   │                           #   重建（三层）
│   ├── governance/             # 批准
│   ├── hub/                    # 编排器、认知、信息、完整性、
│   │                           #   策略、仓库、场景、会话（闸门）
│   ├── interaction/            # 引擎（I-1..I-4）、模型、校验器、类型
│   ├── llm_compliance/         # 闸门（T1/T2/T3）、不变式（L-1..L-3）、出处、类型
│   ├── models/                 # 枚举、hub、schemas
│   └── persistence/            # asyncpg PostgreSQL 仓库（SP_DATABASE_DSN）
├── docs/                       # DECISION_FOUNDATION_V0_2.md,
│                               #   INTELLIGENT_DECISION_HUB_V0_3.md,
│                               #   INTELLIGENT_DECISION_HUB_V0_4.md
├── examples/market_entry.json  # 示例决策请求
├── scripts/export_openapi.py
├── tests/                      # test_api / test_engine / test_hub /
│                               #   test_interaction / test_convergence /
│                               #   test_llm_compliance / test_v04_integration
├── Dockerfile · docker-compose.yml · openapi-action.yaml
├── requirements-engine.txt · requirements-engine-dev.txt
├── IMDA_AI_Verify_Causal_Audit_Report.pdf
└── assets/                     # banner.svg/png, overview.svg/png
```

<p align="center">— ✦ —</p>

## ✦ 生态

NOMOS 是 NOHN AI 生态的一员 —— 围绕第二视角因果审计与确定性执行构建的项目家族：

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

本仓库 **不是开源软件**。双轨模式：个人非商业研究免费；政府 / 企业使用需付费商业许可。参见 [LICENSE](./LICENSE) —— 许可方与适用法律取决于用户所在地（中国境内 → 上海林明钧华科技有限公司，适用中国法律；境外 → NOHN AI TECHNOLOGY PTE. LTD.，适用新加坡法律 + SIAC 仲裁）。

- **申请许可**：国际 / 全球 — [ai@nohnlins.com](mailto:ai@nohnlins.com) · 中国 — [lin@secondai.top](mailto:lin@secondai.top)

合规文档：

**中国（PRC）**：
- [上海合规说明](./docs/COMPLIANCE_SHANGHAI.md)
- [隐私政策（中文）](./docs/PRIVACY_POLICY_CN.md)
- [数据处理协议（中文）](./docs/DATA_PROCESSING_AGREEMENT_CN.md)

**国际 / 全球**：
- [欧盟 AI 法案合规说明](./docs/COMPLIANCE_EU_AI_ACT.md)
- [隐私政策（国际 · GDPR）](./docs/PRIVACY_POLICY_INTL.md)
- [数据处理协议（国际 · GDPR）](./docs/DATA_PROCESSING_AGREEMENT_INTL.md)
- [隐私政策（新加坡 · PDPA）](./docs/PRIVACY_POLICY_SG_PDPA.md)

框架对齐（非约束性参考）：
- [NIST AI RMF 1.0 映射](./docs/COMPLIANCE_NIST_AI_RMF.md)
- [ISO/IEC 42001:2023 对齐](./docs/COMPLIANCE_ISO_42001.md)

<p align="center">
  <a href="https://github.com/nohn3043-arch">GitHub</a> · <a href="https://www.nohnlins.com">官网</a> · <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center"><sub>NOHN AI · NOMOS</sub></p>
