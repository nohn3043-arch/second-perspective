<p align="center">
  <img src="assets/banner.png" alt="NOMOS banner" style="width:100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-D4AF37?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/hub-v0.3.0-D4AF37?style=flat-square" alt="hub-v0.3.0">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
</p>

<blockquote align="center">
  <em>NOMOS · v0.3.0 — 可审计决策中心</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ 关于

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 是构建于确定性决策基座之上的可审计编排层。它在新加坡 <strong>IMDA AI Verify</strong> 合规评估中获得 <strong>95/100</strong>。引擎将结构化评估、细粒度算法审计、因果反事实重选、声明场景压力测试、结构化认知挑战、信息优先级与人工治理整合进一份报告。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
它不会发明缺失的事实、权重、阈值、责任方、证据或概率。它在声明的输入下产出候选方案，并始终把最终裁决权保留在算法之外。
</p>

<p align="center">
  <img src="assets/overview.png" alt="NOMOS overview" style="width:100%">
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ 内置通用审计引擎

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 内置<strong>通用审计引擎</strong>——不是后装补丁。审计追踪内建于确定性核心：每个决策、假设、约束与因果步骤都被记录、哈希链接，并可从设计上独立验证。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
在新加坡 <strong>IMDA AI Verify</strong> 因果审计评估中获得 <strong>95/100</strong>。完整合规报告收录于本仓库 <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code>。
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ v0.3 新增内容

- 每个主要确定性操作的哈希链审计事件
- 约束与判据计算显式操作数与输出
- 传递假设失效后的真实候选重选
- 用户声明的指标、证据与假设失败压力场景
- 不推断心理状态的确定性认知风险挑战层
- 排序的信息获取与复核队列
- 一个 `IntelligentDecisionHub` 编排器与一个密封 `HubReport`
- 基线运行与场景运行内部均含完整审计账本
- 新增 `POST /v1/hub/analyze`，同时保留全部 v0.2 端点
- v0.3 包、CLI 演示、生成的 OpenAPI 与 CI 覆盖率门禁

详细架构与边界见 [`docs/INTELLIGENT_DECISION_HUB_V0_3.md`](docs/INTELLIGENT_DECISION_HUB_V0_3.md)。
v0.2 基座设计见 [`docs/DECISION_FOUNDATION_V0_2.md`](docs/DECISION_FOUNDATION_V0_2.md)。

## ✦ 架构

```text
HubAnalysisRequest
  -> 决策基座
       -> 结构 / 证据审计
       -> 硬 + 软约束评估
       -> 归一化评分
       -> 因果失效
       -> 反事实重选
       -> Pareto + 权重敏感性
       -> 哈希链算法审计
  -> 声明场景压力运行
  -> 结构化认知风险挑战
  -> 信息优先级队列
  -> 追加式 DecisionRecord
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

核心决策基座：

```bash
nomos-demo
```

带两个压力场景的 NOMOS（智能决策中心）：

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

返回的报告包含基线决策记录、场景结果、认知发现、信息优先级、算法账本校验状态、策略快照与报告哈希。

## ✦ 运行 API

本地开发可无密钥运行：

```bash
export SP_ENV=development
uvicorn second_perspective.api.main:app --reload
```

生产环境无密钥则拒绝启动：

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

可选 PostgreSQL 持久化：设置 `SP_DATABASE_DSN`（`asyncpg`）；OIDC 感知身份：设置 `SP_OIDC_ISSUER`。

## ✦ 重新生成 OpenAPI 模式

```bash
SP_PUBLIC_BASE_URL=https://decision.example.com \
python scripts/export_openapi.py
```

## ✦ 兼容性

全部 v0.2 决策请求与端点仍然有效。响应新增 `counterfactuals`、`algorithm_audit`、`algorithm_audit_root_hash`。严格反序列化响应字段的客户端需更新模型。

## ✦ 生产边界

v0.3 是功能完整的 NOMOS 应用核心，尚非完整的多租户企业控制平面。默认仓库仍为进程内内存。生产需要持久化事件存储、OIDC 与授权强制、租户隔离、KMS 签名、限流、可观测性、备份、迁移与域控制包。

认知扫描器只挑战结构性风险。它不诊断人员、不读取动机，也不替代法律、医疗、金融或安全专业人士。

## ✦ 项目结构

```
nomos/
├── pyproject.toml              # 包：nomos-decision-engine v0.3.0
├── src/second_perspective/
│   ├── cli.py / hub_cli.py     # 演示入口（nomos-demo / nomos-hub-demo）
│   ├── service.py / repository.py / canonical.py / version.py
│   ├── api/                    # FastAPI：main.py, security.py
│   ├── audit/                  # auditor, execution, graph, ledger
│   ├── decision/               # causal, counterfactual, engine, evaluator,
│   │                           #   integrity, policy, robustness, selection
│   ├── governance/             # approval
│   ├── hub/                    # orchestrator, cognitive, information, integrity,
│   │                           #   policy, repository, scenario
│   ├── models/                 # enums, hub, schemas
│   └── persistence/            # asyncpg PostgreSQL 仓库（SP_DATABASE_DSN）
├── docs/                       # DECISION_FOUNDATION_V0_2.md, INTELLIGENT_DECISION_HUB_V0_3.md
├── examples/market_entry.json  # 示例决策请求
├── scripts/export_openapi.py
├── tests/                      # test_api / test_engine / test_foundation / test_hub
├── Dockerfile · docker-compose.yml · openapi-action.yaml
├── requirements-engine.txt · requirements-engine-dev.txt
├── IMDA_AI_Verify_Causal_Audit_Report.pdf
└── assets/                     # banner.svg/png, overview.svg/png
```

<p align="center">— ✦ —</p>

## ✦ 生态

NOMOS 是 NOHN AI 生态的一员——围绕第二视角因果审计与确定性执行构建的项目家族：

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

本仓库**非开源**。双轨模式：个人非商业研究免费；政府 / 企业需付费商业授权。详见 [LICENSE](./LICENSE)——许可人与适用法律按用户所在地确定（中国境内 → 上海霖铭骏华科技有限公司，中国法律；境外 → NOHN AI TECHNOLOGY PTE. LTD.，新加坡法律 + SIAC 仲裁）。

- **申请授权**：国际 / 全球 — [ai@nohnlins.com](mailto:ai@nohnlins.com) · 中国 — [lin@secondai.top](mailto:lin@secondai.top)

<p align="center">
  <a href="https://github.com/nohn3043-arch">GitHub</a> · <a href="https://www.nohnlins.com">官网</a> · <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center"><sub>NOHN AI · NOMOS</sub></p>
