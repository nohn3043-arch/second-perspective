<p align="center">
  <img src="https://img.shields.io/badge/python--D4AF37?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/hub-v0.3.0-D4AF37?style=flat-square" alt="hub-v0.3.0">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
</p>

<blockquote align="center">
  <em>NOMOS · v0.3.0</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ 关于

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS 是构建于 v0.2 确定性决策基座之上的、可审计的编排层。它在新加坡 IMDA AI Verify 合规评估中取得 <strong>95/100</strong> 分。该引擎将结构化评估、细粒度算法审计、因果反事实重选、声明场景压力测试、结构性认知挑战、信息优先级与人类治理整合于一份报告之中。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
它不臆造缺失的事实、权重、阈值、责任人、证据或概率。它在声明输入下产出领先候选，并始终将最终裁决权保留在算法之外。
</p>

</div>

## ✦ 内置通用审计引擎

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
该智能体引擎内置<strong>通用审计引擎</strong>——而非事后补丁。审计追踪内置于确定性核心之中，因此每一个决策、假设、约束与因果步骤都被记录、哈希链式串联，并可在设计层面独立验证，而非事后嫁接。
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
在新加坡 <strong>IMDA AI Verify</strong> 因果审计评估中，该引擎取得 <strong>95/100</strong> 分。完整合规报告以 <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code> 形式收录于本仓库。
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ v0.3 新增内容

- 面向每一次主要确定性操作的哈希链式审计事件
- 约束与准则计算中显式的操作数与输出
- 传递性假设失效后的真实候选重选
- 用户声明的指标、证据与假设失效压力场景
- 不推断心理状态的确定性认知风险挑战层
- 带排序的信息获取与复核队列
- 一个 `IntelligentDecisionHub` 编排器与一个封缄的 `HubReport`
- 基线运行与场景运行内部的完整审计账本
- 在保留全部 v0.2 端点的同时新增 `POST /v1/hub/analyze`
- v0.3 包、CLI 演示、生成的 OpenAPI 与 CI 覆盖率门槛

详细架构与边界见
[`docs/INTELLIGENT_DECISION_HUB_V0_3.md`](docs/INTELLIGENT_DECISION_HUB_V0_3.md)。
v0.2 基座设计仍见
[`docs/DECISION_FOUNDATION_V0_2.md`](docs/DECISION_FOUNDATION_V0_2.md)。

## ✦ 架构

```text
HubAnalysisRequest
  -> Decision Foundation
       -> structural/evidence audit
       -> hard + soft constraint evaluation
       -> normalized scoring
       -> causal invalidation
       -> counterfactual reselection
       -> Pareto + weight sensitivity
       -> hash-chained algorithm audit
  -> declared scenario stress runs
  -> structural cognitive-risk challenges
  -> information priority queue
  -> append-only DecisionRecord
  -> sealed HubReport
  -> human approval/rejection
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
second-perspective-demo
```

带两个压力场景的 NOMOS：

```bash
intelligent-decision-hub-demo
```

## ✦ Python 用法

```python
from second_perspective import IntelligentDecisionHub
from second_perspective.models import HubAnalysisRequest

request = HubAnalysisRequest.model_validate(
    {
        "decision": decision_payload,
        "scenarios": [
            {
                "id": "SC1",
                "name": "关键假设失效",
                "failed_assumption_ids": ["A1"],
            },
            {
                "id": "SC2",
                "name": "成本冲击",
                "metric_overrides": {"S2": {"capital_required": 6000000}},
            },
        ],
    }
)
report = IntelligentDecisionHub().analyze(request)
```

返回的报告中包含存储的基线决策记录、场景结果、认知发现、信息优先级、算法账本验证状态、策略快照与报告哈希。

## ✦ 运行 API

本地开发可无密钥运行：

```bash
export SP_ENV=development
uvicorn second_perspective.api.main:app --reload
```

生产环境除非配置了密钥，否则将“失败关闭”：

```bash
export SP_ENV=production
export SP_API_KEY="replace-with-a-strong-secret"
uvicorn second_perspective.api.main:app --host 0.0.0.0 --port 8000
```

受保护的客户端发送 `Authorization: Bearer &lt;SP_API_KEY&gt;`。

端点：

- `POST /v1/hub/analyze`
- `GET /v1/hub/reports/{hub_run_id}`
- `POST /v1/decisions/evaluate`
- `GET /v1/decisions/{decision_id}`
- `GET /v1/decisions/{decision_id}/history`
- `POST /v1/decisions/{decision_id}/approval`
- `GET /health`

## ✦ 重新生成 Action/OpenAPI Schema

```bash
SP_PUBLIC_BASE_URL=https://decision.example.com \
python scripts/export_openapi.py
```

## ✦ 兼容性

所有 v0.2 决策请求与端点仍然有效。响应中新增 `counterfactuals`、`algorithm_audit` 与 `algorithm_audit_root_hash`。严格反序列化响应字段的客户端应更新其模型。

## ✦ 生产边界

v0.3 是一个可运行的 NOMOS 应用内核，尚非完整的多租户企业控制平面。默认仓库仍为进程本地内存。生产环境需要持久化事件存储、OIDC 与授权强制、租户隔离、KMS 签名、限流、可观测性、备份、迁移与领域控制包。

认知扫描器挑战结构性风险。它不诊断个人、不读取动机，也不替代法律、医疗、财务或安全专业人员。

## ✦ 项目结构

```
second-perspective/
├── pyproject.toml              # package: nomos-decision-engine v0.3.0
├── src/second_perspective/
│   ├── cli.py / hub_cli.py     # 演示入口
│   ├── service.py / repository.py / canonical.py / version.py
│   ├── api/                    # FastAPI: main.py, security.py
│   ├── audit/                  # auditor, execution, graph, ledger
│   ├── decision/               # causal, counterfactual, engine, evaluator,
│   │                           #   integrity, policy, robustness, selection
│   ├── governance/             # approval
│   ├── hub/                    # orchestrator, cognitive, information, integrity,
│   │                           #   policy, repository, scenario
│   └── models/                 # enums, hub, schemas
├── docs/                       # DECISION_FOUNDATION_V0_2.md, INTELLIGENT_DECISION_HUB_V0_3.md
├── examples/market_entry.json  # 示例决策请求
├── scripts/export_openapi.py
├── tests/                      # test_api / test_engine / test_foundation / test_hub
├── Dockerfile · openapi-action.yaml · BRANCH_MANIFEST.md · .env.example
└── requirements-engine.txt · requirements-engine-dev.txt
```

## ✦ 文档

- [`docs/DECISION_FOUNDATION_V0_2.md`](docs/DECISION_FOUNDATION_V0_2.md) —— 确定性决策基座及其不变量。
- [`docs/INTELLIGENT_DECISION_HUB_V0_3.md`](docs/INTELLIGENT_DECISION_HUB_V0_3.md) —— 从决策基座到决策枢纽：架构、算法审计、场景、治理。
- 通过 `python scripts/export_openapi.py`（设置 `SP_PUBLIC_BASE_URL`）重新生成 OpenAPI Schema。

## ✦ 状态与路线图

- **v0.3.0** —— 智能决策枢纽应用内核：哈希链式审计、候选重选、场景压力、认知风险扫描器、信息队列、封缄的 `HubReport`。
- 尚非多租户企业控制平面（见上方*生产边界*）。
- 下一步：持久化事件存储、OIDC + 授权、租户隔离、KMS 签名、限流、可观测性。

## ✦ 许可与授权

本仓库**非开源**。采用双轨模式：个人非商业研究免费；政府 / 企业需付费取得商业授权。详见 [LICENSE](./LICENSE) —— 许可方与适用法律随用户所在地而定（中国境内 → 上海林铭君华科技有限公司；中国境外 → NOHN AI TECHNOLOGY PTE. LTD.，适用新加坡法律 + SIAC 仲裁）。

---

<p align="center">
  <a href="https://github.com/NOHN-AI">GitHub</a> · <a href="https://www.nohnlins.com">Website</a> · <a href="mailto:lin@secondai.top">lin@secondai.top</a>
</p>
