# Intelligent Decision-Hub v0.4：二阶因果决策框架

## 定位

v0.3 把一次决策从"单次计算"升级为"中枢编排"——基准决策 + 算法审计 + 反事实 + 压力情景 + 认知质询 + 信息补全 + 治理记录。

v0.4 在此基础上系统性地处理 **假设与假设之间的交互**，而不是把每次失效当作独立事件；把迭代重建循环锚定在 **形式化分类的收敛状态** 上（可证明，而非启发式）；把 LLM 放在 **三层权限门** 之后，可证明地阻止其输出成为裁判结论。

因此，v0.4 是一个功能完整的 **二阶因果决策框架核心**——二阶交互层、形式化收敛、LLM 护栏均为生产级。但它还不是完整的多租户企业控制平面。

## 与 v0.3 的关系

v0.4 没有推翻 `IntelligentDecisionHub`，而是在其上增加三个新层：

```text
IntelligentDecisionHub (v0.4)
├── DecisionService
│   ├── IntelligentDecisionEngine
│   ├── StructuralAuditor
│   ├── Counterfactual Analyzer
│   ├── Robustness Analyzer
│   └── Append-only DecisionRepository
├── Interaction Layer (新增 · 二阶因果)
│   ├── InteractionDeclaration
│   ├── InvalidationClosure + 2nd-order joint effect
│   └── Four invariants: I-1 ~ I-4
├── Convergence Layer (新增 · 形式化收敛)
│   ├── ConvergenceChecker (5-state classification)
│   └── Three propositions: P-1 ~ P-3
├── LLM Compliance Layer (新增 · LLM 护栏)
│   ├── LLMGate (T1/T2/T3 三级权限)
│   └── Three invariants: L-1 ~ L-3
├── ReconstructionSessionEngine (升级 · 三层重建)
│   ├── Forward invalidation
│   ├── Backward root-cause tracing
│   └── Delta reconstruction + human gate
├── Scenario Analyzer
├── CognitiveRiskScanner
├── Information Priority Builder
├── HubReport Integrity Sealer
└── Immutable HubReport Repository Interface
```

所有 v0.3 的 API 和决策请求格式保持兼容。当 `interaction_declaration` 不提供时，引擎行为与 v0.3 完全一致。

---

## 一、假设交互层（二阶因果）

v0.3 及之前，假设失效的传播是一阶的：每个假设独立失效，各自影响依赖它的方案。但现实中多个假设同时失效时可能产生 **协同效应**（放大、冗余、抵消等二阶交互）。

v0.4 引入显式声明的假设交互层，由调用方（责任人）声明二阶效应的存在与强度，引擎只做验证和组合。

### 四个不变量

- **I-1 非臆测**：每一条交互强度 Δ 必须由责任人显式声明；引擎从不估计或学习 Δ。
- **I-2 顺序守恒**：交互仅在 **全部** 成员假设同时失效时触发；部分失效不触发二阶效应。
- **I-3 效应有界**：累计交互效应 ≤ `amplification_ceiling × Σ|一阶效应|`；冗余（负向）交互不作下限钳制，允许真实的阻尼效应。
- **I-4 单调性**：扩充失效集合不会"撤销"已经触发的交互（并集语义）。

### 三种交互类型

| 类型 | 语义 | 效应方向 |
|---|---|---|
| `synergy`（协同） | 多假设同时失效时效应放大 | 正向放大 |
| `redundancy`（冗余） | 一个假设的失效可被另一个部分代偿 | 负向阻尼 |
| `amplification`（级联放大） | 失效链沿依赖方向级联扩大 | 正向放大（带上限） |

### 与一阶失效的组合

```text
一阶失效闭包 (invalidation_closure)
       │
       ▼
二阶交互匹配 (interaction_declaration + member check + I-2)
       │
       ▼
交互效应累加 (I-3 上界钳制 + I-4 单调性)
       │
       ▼
联合失效结果：受影响方案 + 修正后影响分 + 交互触发审计轨迹
```

`DecisionRequest` 新增可选字段 `interaction_declaration`（默认 `None`，完全向后兼容）。会话引擎的停止条件检查委托给形式化 `ConvergenceChecker`。

---

## 二、形式化收敛引擎

v0.3 的重建循环用启发式停止条件（"没有变化就停下来"）。v0.4 用三个可检验命题将停止条件分类为 **五个确定状态**，并明确区分"真收敛"和"预算耗尽"。

### 五个收敛状态

| 状态 | 含义 | 是否真收敛 |
|---|---|---|
| `FIXED_POINT` | 候选集与上一轮完全相同（P-2 证明） | ✅ 是 |
| `NO_GAIN` | 没有未解决分支，剩余分支全为 `BLOCKED` | ✅ 是 |
| `BUDGET_EXHAUSTED` | 预算耗尽，尚未到达不动点 | ❌ 不是 |
| `DIVERGED` | 仍在变化，预算未耗尽 | ❌ 不是 |
| `BLOCKED` | 结构性阻塞，需要人工介入 | ❌ 不是 |

### 三个可检验命题

- **P-1 终止性**：迭代次数 ≤ `max_iterations`，且每次迭代产生的新 ΔVar 不超过声明集合 → 循环必终止。
- **P-2 不动点**：当且仅当前后两轮领先候选集合和失效集合完全相同时，`FIXED_POINT` 成立。不动点一旦到达，后续任意轮不再变化（单调性保证）。
- **P-3 效应有界**：累计校正效应的绝对值 ≤ `amplification_ceiling × Σ|初始一阶效应|`，不发散。

`is_true_convergence()` 守卫经典错误：不能把预算耗尽误报为收敛。任何把 `BUDGET_EXHAUSTED` 报告为"收敛"的调用方都违反了 v0.4 的核心契约。

---

## 三、LLM 合规层

v0.4 第一次引入 LLM 增强，但放在 **可证明无裁判权** 的护栏之后。LLM 可以标注、提议、润色，但永远不能翻转假设状态、改变方案排名或产出最终结论。

### 三级权限区

| 层级 | 权限 | 能做什么 | 不能做什么 |
|---|---|---|---|
| **T1 标注**（Annotation） | 最低 | 为已有结论添加摘要、标签、结构化重述 | 不能引入新判断、不能修改状态 |
| **T2 提议**（Proposal） | 中等 | 生成候选 ΔVar 建议、列出可选措辞、草拟问题 | 必须经人工显式批准才能生效 |
| **T3 叙述**（Narrative） | 最高（仍受限制） | 生成报告正文、解释文本、自然语言润色 | 结构权力被剥离，不能接触决策图 |

### 三个不变量

- **L-1 区域隔离**：每个 LLM 调用必须明确声明所属层级；跨层调用立即拒绝。
- **L-2 无裁判权**：任何 LLM 输出在进入决策图之前必须经过 `LLMGate.strip_structural_power()`，移除所有能改变状态、权重、排名的字段。
- **L-3 强度剥离**：LLM 生成的任何"强度""概率""置信度"字段都被丢弃，不允许影响定量计算。

### provenance 追踪

每次 LLM 调用都记录：调用层级、输入哈希、输出哈希、模型名、时长、成功/失败、剥离操作日志。`HubReport` 中所有 LLM 生成的内容都带有 `llm_generated` 标记和 `provenance_ref`，可独立核验。

---

## 四、三层因果重建（升级）

v0.3 的因果重建是一次性的。v0.4 将其升级为 **有界、哈希链、人工门控** 的迭代过程。

每轮运行三个因果算子：

1. **前向失效传播**：`invalidation_closure` 将声明的假设失效向前传播，移除失去假设支撑的方案。
2. **后向根因追溯**：反向 BFS 将偏差信号回溯到根因假设的候选集。
3. **Delta 重建**：对请求副本应用声明的校正变量（`DeltaVar`），重跑确定性评估，判断领先候选集合的收敛性。

### 设计不变量

- **不猜测**：每个假设都是候选，由人决定。引擎从不自动循环。
- **确定性**：每轮完全从声明输入推导。
- **可审计**：每轮与上一轮哈希链接，整个会话形成 `session_root_hash`。
- **有界**：受 `max_iterations` 和 `max_evidence_requests` 限制。
- **人工门**：`advance()` 恰好执行一轮，随后停在 `AWAITING_HUMAN`；只有人工决策（`approve` / 提供证据 / 拒绝）才能进入下一轮。

### DeltaVar 三种路径形式

| 形式 | 示例 | 作用 |
|---|---|---|
| 假设标识 | `"A2"` | 证伪一个假设，沿依赖图传播 |
| 指标权重 | `"criteria.K1.weight"` | 重写某项指标的权重 |
| 方案指标 | `"alternatives.S1.metrics.cost"` | 重写某个方案的某个指标值 |

引擎逐字镜像每条声明的 `DeltaVar`，从不发明校正变量。

---

## 五、核心请求结构（v0.4 增量）

v0.3 的 `HubAnalysisRequest` 新增可选的 `interaction_declaration` 字段：

```json
{
  "decision": {
    "objective": "...",
    "decision_owner": {},
    "criteria": [],
    "constraints": [],
    "assumptions": [],
    "alternatives": [],
    "evidence": []
  },
  "scenarios": [
    {
      "id": "SC1",
      "name": "关键假设失败",
      "failed_assumption_ids": ["A1"]
    }
  ],
  "interaction_declaration": {
    "interactions": [
      {
        "id": "INT-1",
        "type": "synergy",
        "member_assumption_ids": ["A1", "A2"],
        "effect_delta": 0.3,
        "responsibility": "risk_team",
        "declared_at": "2026-09-01T00:00:00Z"
      }
    ],
    "amplification_ceiling": 2.0
  },
  "run_cognitive_audit": true,
  "llm_zone": "annotation"
}
```

---

## 六、完整性与治理（升级）

v0.4 在 v0.3 三层完整性基础上增加：

1. 单次算法执行的事件哈希链（保留）；
2. 同一决策多次评估/审批的 `DecisionRecord` 父哈希链（保留）；
3. 汇总基准决策、情景、认知发现和信息队列的 `HubReport.report_hash`（保留）；
4. **新增**：重建会话的 `session_root_hash` — 每轮重建与上一轮哈希链接，整会话可验证；
5. **新增**：LLM 调用的 provenance 哈希链 — 每次 LLM 调用的输入/输出/剥离操作均记录，且与所属决策事件绑定。

哈希检测内容修改，但没有外部签名、可信时间戳和独立存储时，不能证明整个数据库未被整体重写。生产版本必须接入 KMS/HSM 和不可变事件存储。

---

## 七、测试覆盖

v0.4 测试从 v0.3 的约 280 个增长到 **402 个**（新增 122 个），全部通过：

- `test_interaction.py` — 假设交互层（I-1 ~ I-4 + 三种交互类型）
- `test_convergence.py` — 形式化收敛（5 状态 + P-1 ~ P-3）
- `test_llm_compliance.py` — LLM 合规层（T1/T2/T3 + L-1 ~ L-3 + provenance）
- `test_session.py` — 重建会话（人工门 + 哈希链 + DeltaVar 三形式）
- `test_v04_integration.py` — 端到端集成（基准 + 交互 + 重建 + LLM 标注）

---

## 八、生产边界

v0.4 是功能完整的 **确定性决策框架核心**——二阶因果层、形式化收敛、LLM 护栏均为生产级。它还不是完整的多租户企业控制平面。

**已具备（生产级）**：
- 一阶 + 二阶因果决策内核
- 形式化收敛证明
- LLM 三层权限护栏
- 哈希链审计（决策 + 会话 + LLM provenance）
- PostgreSQL 持久化选项（`SP_DATABASE_DSN`）
- OIDC 身份感知（`SP_OIDC_ISSUER`）
- API key 门控 + 生产环境强制校验

**仍需生产侧补齐（不在框架核心范围内）**：
- 多租户隔离与租户路由
- 完整 RBAC/ABAC 模型
- KMS/HSM 签名与可信时间戳
- 异步情景任务队列
- 指标、追踪、告警
- 策略注册中心与灰度发布
- 限流与幂等
- 备份与迁移
- 领域控制包（行业模板）

---

## 九、明确边界（强化版）

- Hub 不自动批准决策；
- 认知扫描不诊断个人心理；
- 情景只使用用户显式声明的变化；
- 二阶交互的效应强度必须由责任人声明，引擎从不估计或学习；
- `BUDGET_EXHAUSTED` 不是收敛，任何将其报告为收敛的行为违反核心契约；
- LLM 永远不能裁判：T2 提议需人工批准，T3 叙述被剥离结构权力，任何 LLM 输出不能翻转假设状态或方案排名；
- 当前没有概率推断、Monte Carlo 或机器学习预测；
- 默认内存仓库不适合多实例生产；
- 医疗、法律、财务和安全决策仍由对应专业责任人承担。
