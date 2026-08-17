<p align="center">
  <img src="assets/banner.png" alt="NOMOS 横幅" style="width:100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-D4AF37?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/hub-v0.3.0-D4AF37?style=flat-square" alt="hub-v0.3.0">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
</p>

<blockquote align="center">
  <em>NOMOS · v0.3.0 —— 可审计决策中枢</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ 项目简介

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 是构建在确定性决策内核之上的可审计编排层，在新加坡 <strong>IMDA AI Verify</strong> 合规评测中取得 <strong>95/100</strong> 的因果审计评分。它将结构化评估、细粒度算法审计、因果反事实重选、声明式场景压测、结构化认知挑战、信息优先级排序以及人类治理统一为一份报告。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
引擎绝不编造缺失的事实、权重、阈值、责任方、证据或概率；只在声明输入下产出候选，并始终把最终裁决留在算法之外。
</p>

<p align="center">
  <img src="assets/overview.png" alt="NOMOS 架构总览" style="width:100%">
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ 内置通用审计引擎

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 自带<strong>通用审计引擎</strong>，而非事后补丁。审计轨迹内建于确定性内核：每一次决策、假设、约束与因果步骤都被记录、哈希链接，并可被独立核验。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
在新加坡 <strong>IMDA AI Verify</strong> 因果审计赛道取得 <strong>95/100</strong>，完整合规报告见 <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code>。
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ v0.3 新增内容

- 对每一次重大确定性操作生成哈希链接的审计事件
- 约束与准则计算显式保留操作数与输出
- 假设失效传播后真正的候选重选
- 用户声明的压力场景（假设失效、指标覆盖）
- 不推断任何心智状态的确定性认知风险挑战层
- 信息获取与复核的优先级队列
- `IntelligentDecisionHub` 编排器与封存的 `HubReport`
- 基线运行与场景运行均包含完整审计账本
- 新增 `POST /v1/hub/analyze`，同时保留全部 v0.2 端点
- v0.3 包、CLI 演示、生成的 OpenAPI 与 CI 覆盖率门禁

架构与边界：[`docs/INTELLIGENT_DECISION_HUB_V0_3.md`](docs/INTELLIGENT_DECISION_HUB_V0_3.md)。
v0.2 基础设计：[`docs/DECISION_FOUNDATION_V0_2.md`](docs/DECISION_FOUNDATION_V0_2.md)。

## ✦ 三重因果重构（有界收敛 + 人类闸门）

新增于 `hub/session.py`（`ReconstructionSessionEngine`）与 `decision/reconstruction.py`（`reconstruct_with_delta`）：将原本一次性的因果重构升级为**有界、哈希链接、并由人类闸门控制的迭代过程**。

每一轮执行三重因果算子：

1. **正向失效传播**：通过 `invalidation_closure` 将声明的假设失效向前传播，剔除依赖该假设的备选方案。
2. **逆向根因追溯**：沿用既有反向 BFS，将偏差信号追溯到候选根因假设集。
3. **修正注入重推演**：将人类声明的修正变量（`DeltaVar`）应用到请求副本，重新运行确定性评估器，并判定领先候选集是否收敛。

设计不变量（与 NOMOS 核心一致）：

- **不猜测** —— 每个假设都是候选，由人类裁决；引擎永不自动循环。
- **确定性** —— 每一轮仅由声明的输入推导。
- **可审计** —— 每个轮次哈希链接到上一轮，整条会话形成 `session_root_hash`。
- **有界** —— 以 `max_iterations` 与 `max_evidence_requests` 封顶。
- **人类闸门** —— `advance()` 只执行一轮并停在 `AWAITING_HUMAN`；只有人类决策（approve / 提供证据 / 拒绝）才能推进到下一轮。

收敛判据：定点（候选集不再变化）、无收益（无未决分支且假设全部结清）、预算耗尽。

```python
from second_perspective.models import DecisionRequest, DeviationSignal, DeltaVar
from second_perspective.hub.session import ReconstructionSessionEngine

engine = ReconstructionSessionEngine()
session = engine.start(request, signals, max_iterations=5)
session = engine.advance(session)                                   # 第一轮：三重重构
session = engine.advance(session, [                                 # 注入人类声明的修正
    DeltaVar(path="A2", value=None, reason="...", responsibility="..."),
])
session = engine.human_decision(session, approved=True)             # 人类封存
print(session.session_root_hash)
```

`DeltaVar` 的 path 支持三种形式：`"A2"`（声明某假设失效，经依赖图传播）、`"criteria.K1.weight"`（改写准则权重）、`"alternatives.S1.metrics.cost"`（改写备选指标）。引擎逐字镜像每个声明的 `DeltaVar`，绝不自行编造修正。

## ✦ 架构

```text
HubAnalysisRequest
  -> 决策内核
       -> 结构 / 证据审计
       -> 硬 + 软约束评估
       -> 归一化打分
       -> 因果失效
       -> 反事实重选
       -> 帕累托 + 权重敏感性
       -> 哈希链接的算法审计
  -> 声明式场景压力运行
  -> 结构化认知风险挑战
  -> 信息优先级队列
  -> 只追加决策记录
  -> 封存的 HubReport
  -> 人类批准 / 拒绝
```

## ✦ 安装与测试

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## ✦ 运行演示

核心决策内核：

```bash
nomos-demo
```

NOMOS（智能决策中枢）含两个压力场景：

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

返回的报告包含基线决策记录、场景结果、认知发现、信息优先级、算法账本核验状态、政策快照与报告哈希。

## ✦ 运行 API

本地开发免密钥运行：

```bash
export SP_ENV=development
uvicorn second_perspective.api.main:app --reload
```

生产环境无密钥拒绝启动：

```bash
export SP_ENV=production
export SP_API_KEY="替换为强密钥"
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

可选 PostgreSQL 持久化：设置 `SP_DATABASE_DSN`（`asyncpg`）；支持 OIDC 身份：设置 `SP_OIDC_ISSUER`。

## ✦ 重新生成 OpenAPI 模式

```bash
SP_PUBLIC_BASE_URL=https://decision.example.com \
python scripts/export_openapi.py
```

## ✦ 兼容性

全部 v0.2 决策请求与端点仍然有效。响应新增 `counterfactuals`、`algorithm_audit`、`algorithm_audit_root_hash`。严格反序列化响应字段的客户端需更新其模型。

## ✦ 生产边界

v0.3 是功能完整的 NOMOS 应用内核，尚非完整的多租户企业控制平面。默认存储仍为进程内内存。生产环境需持久化事件存储、OIDC 与授权强制、租户隔离、KMS 签名、限流、可观测性、备份、迁移与领域控制包。

认知扫描仅挑战结构性风险，不诊断个人、不读取动机，亦不替代法律、医疗、金融或安全专业人士。

## ✦ 项目结构

```
nomos/
├── pyproject.toml              # 包名：nomos-decision-engine v0.3.0
├── src/second_perspective/
│   ├── cli.py / hub_cli.py     # 演示入口（nomos-demo / nomos-hub-demo）
│   ├── service.py / repository.py / canonical.py / version.py
│   ├── api/                    # FastAPI: main.py, security.py
│   ├── audit/                  # auditor, execution, graph, ledger
│   ├── decision/               # causal, counterfactual, engine, evaluator,
│   │                           #   integrity, policy, robustness, selection,
│   │                           #   reconstruction（三重重构）
│   ├── governance/             # approval
│   ├── hub/                    # orchestrator, cognitive, information, integrity,
│   │                           #   policy, repository, scenario, session（闸门）
│   ├── models/                 # enums, hub, schemas
│   └── persistence/            # asyncpg PostgreSQL 仓库（SP_DATABASE_DSN）
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

## ✦ 生态

NOMOS 是 NOHN AI 生态成员 —— 围绕第二视角因果审计与确定性执行构建的项目族：

| 项目 | 仓库 | 角色 |
|---|---|---|
| **第二视角（GCAE）** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective) | 全局认知审计引擎 —— 五算子因果审计内核（IMDA 95/100） |
| **NOMOS** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective)（`Intelligent-Decision-Hub--Nomos` 分支） | 可审计确定性决策中枢（IMDA 95/100） |
| **SPL-G1** | [nohn3043-arch/SPL-G1](https://github.com/nohn3043-arch/SPL-G1) | 硬件因果审计可信计算单元（TCU） |
| **SPL-Virtual-World-Base** | [nohn3043-arch/Second-Reality](https://github.com/nohn3043-arch/Second-Reality) | 虚拟世界与元宇宙基础设施（宪法 / 法律 / 桥接） |
| **Story-Engine** | [nohn3043-arch/story-engine](https://github.com/nohn3043-arch/story-engine) | 长篇小说一致性引擎 |
| **Antares** | [nohn3043-arch/Antares](https://github.com/nohn3043-arch/Antares) | GFSIP v1.0 —— 因果审计联邦稳定互操作协议 |
| **Anthropomorphic-Agent-Engine** | [nohn3043-arch/Anthropomorphic-Agent-Engine](https://github.com/nohn3043-arch/Anthropomorphic-Agent-Engine) | 确定性拟人心理引擎（SPL Pure Core V8.0） |
| **PAGES** | [nohn3043-arch/pages](https://github.com/nohn3043-arch/pages) | NOHN AI 生态官方落地页 |

<p align="center">— ✦ —</p>

## ✦ 许可与授权

本仓库**并非开源**。双轨制：个人非商业研究免费；政府 / 企业需购买商业许可。详见 [LICENSE](./LICENSE) —— 许可方与适用法律依用户所在地而定（中国境内 → 上海林铭君华科技有限公司，适用中国法律；境外 → NOHN AI TECHNOLOGY PTE. LTD.，适用新加坡法律与 SIAC 仲裁）。

- **申请许可**：国际 / 全球 —— [ai@nohnlins.com](mailto:ai@nohnlins.com) · 中国 —— [lin@secondai.top](mailto:lin@secondai.top)

<p align="center">
  <a href="https://github.com/nohn3043-arch">GitHub</a> · <a href="https://www.nohnlins.com">网站</a> · <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center"><sub>NOHN AI · NOMOS</sub></p>
