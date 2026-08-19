<p align="center">
  <img src="assets/banner.png" alt="NOMOS banner" style="width:100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-D4AF37?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/hub-v0.3.0-D4AF37?style=flat-square" alt="hub-v0.3.0">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
</p>

<blockquote align="center">
  <em>NOMOS · v0.3.0 — 智能决策中枢</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ 关于

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 是一个内建可审计确定性核心的智能决策中枢。它在新加坡 <strong>IMDA AI Verify</strong> 合规评估中获得 <strong>95/100</strong> 分。该引擎将结构化评估、细粒度算法审计、因果反事实重选、声明式场景压力测试、结构化认知风险挑战、信息优先级排序与人类治理统一为单一报告。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
它从不虚构缺失的事实、权重、阈值、责任方、证据或概率。它仅在声明输入下产出候选方案，并始终将最终裁决置于算法之外。
</p>

<p align="center">
  <img src="assets/overview.png" alt="NOMOS overview" style="width:100%">
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ 内置通用审计引擎

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 搭载 <strong>通用审计引擎</strong>——而非事后补丁。审计追踪内建于确定性核心：每一步决策、假设、约束与因果步骤均被记录、哈希链链接，并设计为可独立验证。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
它在新加坡 <strong>IMDA AI Verify</strong> 因果审计赛道中获得 <strong>95/100</strong> 分。完整合规报告见 <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code>。
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ v0.3 新特性

- 每次确定性操作的哈希链审计事件
- 约束与标准计算的显式操作数与输出
- 传播假设失败后的真实候选重选
- 用户声明的压力场景（假设失败、指标覆盖）
- 不推断心理状态的确定性认知风险挑战层
- 信息优先级排序与审查队列
- `IntelligentDecisionHub` 编排器与密封 `HubReport`
- 基线与场景运行均包含完整审计账本
- 新增 `POST /v1/hub/analyze`，保留所有 v0.2 端点
- v0.3 包、CLI 演示、生成式 OpenAPI 与 CI 覆盖率门禁

架构与边界：[`docs/INTELLIGENT_DECISION_HUB_V0_3.md`](docs/INTELLIGENT_DECISION_HUB_V0_3.md)。
v0.2 基础设计：[`docs/DECISION_FOUNDATION_V0_2.md`](docs/DECISION_FOUNDATION_V0_2.md)。

## ✦ 三重因果重构（有界收敛 + 人网关）

新增于 `hub/session.py`（`ReconstructionSessionEngine`）与 `decision/reconstruction.py`（`reconstruct_with_delta`）：之前的一次性因果重构升级为**有界、哈希链链接、人网关控的迭代过程**。

每轮执行三个因果算子：

1. **前向无效化传播**——`invalidation_closure` 将声明的假设失败向前传播，丢弃失去该假设支持的备选方案。
2. **逆向根因追溯**——现有反向 BFS 将偏差信号追溯至一组根因假设候选集。
3. **Delta 重构**——声明的修正变量（`DeltaVar`）应用于请求副本，重新运行确定性评估器，判断主要候选集的收敛情况。

设计不变量（遵循 NOMOS 核心）：

- **不猜测**——每个假设都是候选，由人决定；引擎从不自动循环。
- **确定性**——每轮仅从声明输入推导。
- **可审计**——每轮通过哈希链链接至上一轮，整个会话形成 `session_root_hash`。
- **有界**——由 `max_iterations` 和 `max_evidence_requests` 限制。
- **人网关**——`advance()` 恰好执行一轮后停在 `AWAITING_HUMAN`；仅人类决策（`approve` / 提供证据 / `reject`）可推进至下一轮。

停止条件：不动点（候选集停止变化）、无增益（无未解决分支且所有假设已确定）、或预算耗尽。

```python
from second_perspective.models import DecisionRequest, DeviationSignal, DeltaVar
from second_perspective.hub.session import ReconstructionSessionEngine

engine = ReconstructionSessionEngine()
session = engine.start(request, signals, max_iterations=5)
session = engine.advance(session)                                   # 第一轮：三重重构
session = engine.advance(session, [                                 # 注入声明的修正
    DeltaVar(path="A2", value=None, reason="...", responsibility="..."),
])
session = engine.human_decision(session, approved=True)             # 人类确认
print(session.session_root_hash)
```

`DeltaVar` 路径有三种形式：`"A2"`（证伪假设，通过依赖图传播）、`"criteria.K1.weight"`（重写标准权重）、或 `"alternatives.S1.metrics.cost"`（重写备选方案指标）。引擎逐字反映每个声明的 `DeltaVar`，从不发明修正。

## ✦ 架构

```text
HubAnalysisRequest
  -> 决策核心
       -> 结构 / 证据审计
       -> 硬约束 + 软约束评估
       -> 归一化评分
       -> 因果无效化
       -> 反事实重选
       -> 帕累托 + 权重敏感性
       -> 哈希链算法审计
  -> 声明式场景压力运行
  -> 结构化认知风险挑战
  -> 信息优先级队列
  -> 仅追加 DecisionRecord
  -> 密封 HubReport
  -> 人工批准 / 拒绝
```

## ✦ 安装与测试

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## ✦ 运行演示

核心决策核：

```bash
nomos-demo
```

NOMOS（智能决策中枢）带两个压力场景：

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
            {"id": "SC1", "name": "关键假设失败", "failed_assumption_ids": ["A1"]},
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

可选 PostgreSQL 持久化：设置 `SP_DATABASE_DSN`（`asyncpg`）；OIDC 身份识别：设置 `SP_OIDC_ISSUER`。

## ✦ 重新生成 OpenAPI 模式

```bash
SP_PUBLIC_BASE_URL=https://decision.example.com \
python scripts/export_openapi.py
```

## ✦ 兼容性

所有 v0.2 决策请求与端点继续有效。响应新增 `counterfactuals`、`algorithm_audit`、`algorithm_audit_root_hash`。严格反序列化响应字段的客户端需更新其模型。

## ✦ 生产边界

v0.3 是功能完整的 NOMOS 应用核心，尚非完整的多租户企业控制平面。默认存储为进程内内存。生产环境需要持久化事件存储、OIDC 与授权强制、租户隔离、KMS 签名、速率限制、可观测性、备份、迁移与领域控制包。

认知扫描器仅挑战结构性风险，不诊断人员、不读取动机，也不替代法律、医疗、财务或安全专业人士。

## ✦ 项目结构

```
nomos/
├── pyproject.toml              # 包: nomos-decision-engine v0.3.0
├── src/second_perspective/
│   ├── cli.py / hub_cli.py     # 演示入口 (nomos-demo / nomos-hub-demo)
│   ├── service.py / repository.py / canonical.py / version.py
│   ├── api/                    # FastAPI: main.py, security.py
│   ├── audit/                  # auditor, execution, graph, ledger
│   ├── decision/               # causal, counterfactual, engine, evaluator,
│   │                           #   integrity, policy, robustness, selection,
│   │                           #   reconstruction (三重重构)
│   ├── governance/             # approval
│   ├── hub/                    # orchestrator, cognitive, information, integrity,
│   │                           #   policy, repository, scenario, session (gate)
│   ├── models/                 # enums, hub, schemas
│   └── persistence/            # asyncpg PostgreSQL 仓库 (SP_DATABASE_DSN)
├── docs/                       # DECISION_FOUNDATION_V0_2.md, INTELLIGENT_DECISION_HUB_V0_3.md
├── examples/market_entry.json  # 示例决策请求
├── scripts/export_openapi.py
├── tests/                      # test_api / test_engine / test_foundation / test_hub / test_session
├── Dockerfile · docker-compose.yml · openapi-action.yaml
├── requirements-engine.txt · requirements-engine-dev.txt
├── IMDA_AI_Verify_Causal_Audit_Report.pdf
└── assets/                     # banner.svg/png, overview.svg/png
```

<p align="center">— ✦ —</p>

## ✦ 生态系统

NOMOS 是 NOHN AI 生态系统的成员——围绕第二人称因果审计与确定性执行构建的一系列项目：

| 项目 | 仓库 | 角色 |
|---|---|---|
| **Second-Perspective (GCAE)** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective) | 全局认知审计引擎——五算子因果审计内核 (IMDA 95/100) |
| **NOMOS** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective) (`Intelligent-Decision-Hub--Nomos` 分支) | 可审计确定性决策中枢 (IMDA 95/100) |
| **SPL-G1** | [nohn3043-arch/SPL-G1](https://github.com/nohn3043-arch/SPL-G1) | 硬件因果审计可信计算单元 (TCU) |
| **SPL-Virtual-World-Base** | [nohn3043-arch/Second-Reality](https://github.com/nohn3043-arch/Second-Reality) | 虚拟世界与元宇宙基础设施（宪法 / 法律 / 桥接） |
| **Story-Engine** | [nohn3043-arch/story-engine](https://github.com/nohn3043-arch/story-engine) | 长篇叙事一致性引擎 |
| **Antares** | [nohn3043-arch/Antares](https://github.com/nohn3043-arch/Antares) | GFSIP v1.0 — 因果审计联邦稳定互操作协议 |
| **Anthropomorphic-Agent-Engine** | [nohn3043-arch/Anthropomorphic-Agent-Engine](https://github.com/nohn3043-arch/Anthropomorphic-Agent-Engine) | 确定性拟人心理学引擎 (SPL Pure Core V8.0) |
| **PAGES** | [nohn3043-arch/pages](https://github.com/nohn3043-arch/pages) | NOHN AI 生态系统官方落地页 |

<p align="center">— ✦ —</p>

## ✦ 许可与授权

本仓库**非开源**。双轨制：个人非商业研究免费；政府/企业需付费商业许可。见 [LICENSE](./LICENSE)——许可方与适用法律取决于用户所在地（中国境内 → 上海灵明峻华科技有限公司，中华人民共和国法律；境外 → NOHN AI TECHNOLOGY PTE. LTD.，新加坡法律 + SIAC 仲裁）。

- **申请许可**：国际/全球 — [ai@nohnlins.com](mailto:ai@nohnlins.com) · 中国 — [lin@secondai.top](mailto:lin@secondai.top)

<p align="center">
  <a href="https://github.com/nohn3043-arch">GitHub</a> · <a href="https://www.nohnlins.com">网站</a> · <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center"><sub>NOHN AI · NOMOS</sub></p>