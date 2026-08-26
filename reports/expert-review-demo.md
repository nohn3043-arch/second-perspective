# NOMOS 领域专家复核报告

- 报告生成时间：2026-08-25T16:10:59+00:00
- 引擎版本：0.3.0
- 复核对象：1 条决策记录， 份 Hub 报告

## 1. 结论摘要

| 校验项 | 结果 |
|---|---|
| 决策链完整性（revision 单调 + 父哈希衔接） | PASS |
| 记录哈希自洽（DEC-C784A5B2C5CE） | PASS |
| 算法审计账本校验（DEC-C784A5B2C5CE） | PASS |

## 2. 决策链

| 修订 | 决策 ID | 状态 | 审计通过 | 领先候选 | record_hash |
|---|---|---|---|---|---|
| 1 | DEC-C784A5B2C5CE | HUMAN_APPROVAL_REQUIRED | True | S2 | afd0869e36b01adac8aa63dc6e4f74a99875cefe741eecd950a922d5df05e623 |

## 3. 算法审计事件（证据定位）

每条事件均为 SHA-256 链式哈希，`previous_event_hash` 衔接前序事件。

### DEC-C784A5B2C5CE
`algorithm_audit_root_hash` = `810fbf191e17a15d48575d6a8e787fc3ca967b825d91a0937b3595eeb75e006f`

| 序号 | 阶段 | 规则 | 操作 | event_hash |
|---|---|---|---|---|
| 1 | input | REQUEST_CONTRACT | validate_structured_request | 28080bba8988a6f2e05c695f3a3af7b4ada3222d2381d7183efc93ed7d9efa67 |
| 2 | audit | EVIDENCE_STATE | inspect_evidence | 1e1e63fa00c63e7913ad00e7102ed953ab016a536c8d77365e81370e9ca28538 |
| 3 | audit | ASSUMPTION_DEPENDENCY | inspect_assumption_basis | 99afb297f5f2a9be00d2ac7b88c7e3a71abec5b6dd1cfbc697b36c859acd049a |
| 4 | evaluation | CONSTRAINT_COMPARISON | compare_lte | 693c5b4ed17da3a3f8ad0f8bc125a21e83ce6bc57b247f7564cedf53ec2cbbfc |
| 5 | evaluation | CONSTRAINT_COMPARISON | compare_eq | 598e7e66e69ddebde06bec3c8d8c68b21bda4e55964afcf4db1885b5f326bcf0 |
| 6 | evaluation | CONSTRAINT_COMPARISON | compare_gte | c7dfd9dc7320e90fe8a9ccea5411fa723859247b25eb0edd878279cd0ef23a5e |
| 7 | evaluation | CRITERION_NORMALIZATION | lower_is_better | f10856ef68d6075096c598589088337af43d3c74483e6e15ee38dd86704d911c |
| 8 | evaluation | CRITERION_NORMALIZATION | higher_is_better | acac79a08cf40b3b64abfa4c1c566c2ac7e854956e22d95fa04aaef667de11ca |
| 9 | evaluation | ALTERNATIVE_AGGREGATION | aggregate_alternative_result | 7d8165fb91c63492aed22519fd510b068434f4d09acbf9fc9cbf62751d4e3098 |
| 10 | evaluation | CONSTRAINT_COMPARISON | compare_lte | bdb4803d194a0145e527b197f33258fdb8f58ea100b3a71f22a808897ab3aecd |
| 11 | evaluation | CONSTRAINT_COMPARISON | compare_eq | 235a843582e1b6500e6d1f4ae11ae4685dc0c35ff2e476c0bfcb2faefe1145b1 |
| 12 | evaluation | CONSTRAINT_COMPARISON | compare_gte | 0da29f640785566b0edf229eaf61544a1a8765ef787be8fc10a141ab1f7a527a |
| 13 | evaluation | CRITERION_NORMALIZATION | lower_is_better | e07b06ad05b209cc86bfe44eec74e1ab5a99f475baa965f5280e3a53c8a4565f |
| 14 | evaluation | CRITERION_NORMALIZATION | higher_is_better | e2e305e1d88973d3aba2fae3a7a6f1ac5774bed97fb3d210e4054c4909f58919 |
| 15 | evaluation | ALTERNATIVE_AGGREGATION | aggregate_alternative_result | f01608ba0f13c95150dc9bd529829f495ac82c5ad32e2e0faf107524b8d5d703 |
| 16 | causal | ASSUMPTION_INVALIDATION_CLOSURE | propagate_assumption_failure | 2d6b0cfd842e781576709b72f38dddb58f75bac55a3de54f31809955c7e65f2c |
| 17 | counterfactual | COUNTERFACTUAL_RESELECTION | remove_invalidated_alternatives_and_reselect | b922a51e565552d3e0f03498745eba0bf8e9e4326d880e3cd2d89f81fd3a5ead |
| 18 | robustness | PARETO_FRONTIER | compute_non_dominated_alternatives | 1aa3114538a6b18d20b6526a7f8c7c9a5cc0977a7311ab517e9511a7a2d8adf3 |
| 19 | robustness | WEIGHT_SENSITIVITY | perturb_weight_decrease | 7c1523e1ef99145424c9536fc09559cc055bc557c7d5aab81bf1c6bfd2ef811c |
| 20 | robustness | WEIGHT_SENSITIVITY | perturb_weight_increase | 6412f84ee380c59693614b13b505f53ff9f03e44be8c1413f285e0d1d89070c4 |
| 21 | robustness | WEIGHT_SENSITIVITY | perturb_weight_decrease | b76cb71a7b83f87ff38830ac2fdf6b246d34daa2882a4e93ab05dd6e0f6899d9 |
| 22 | robustness | WEIGHT_SENSITIVITY | perturb_weight_increase | ce0e2d2cb4194ac1db9301a4d0bf6cebffa3889fcbca77711d3d53b5220f7a5a |
| 23 | selection | LEADING_CANDIDATE_SELECTION | select_under_declared_policy | a02fd84762294b94968822058d8818620363fc9bf5df4a0e7f50f4dc2a7ca5c9 |
| 24 | governance | DECISION_STATE_RESOLUTION | resolve_pre_approval_status | 810fbf191e17a15d48575d6a8e787fc3ca967b825d91a0937b3595eeb75e006f |

## 5. 专家复核指引

不要信任本报告的结论，直接对底层哈希复算：

```bash
python - <<'EOF'
from second_perspective.decision.integrity import verify_chain, verify_record
from second_perspective.audit.ledger import verify_algorithm_audit
from second_perspective.hub.integrity import verify_hub_report
# records / hub_report 从你的决策对象反序列化后传入
print('chain:', verify_chain(records))
print('record:', [verify_record(r) for r in records])
print('audit:', [verify_algorithm_audit(r.result.algorithm_audit, r.result.algorithm_audit_root_hash) for r in records])
EOF
```

关联本地运行日志（Layer 1）：日志中 `decision sealed` / `audit event appended` / 
`hub report sealed` 三行所附哈希应与上表逐一对应，核对任一行被篡改都会破坏相应校验。

## 6. 边界声明

- 本报告为本地生成的展示层文件，**不构成签名审计记录**，不能单独作为合规证据。
- 哈希校验只能证明记录未被篡改，**不能证明评估结论正确**；结论正确性属于人类审批者的裁量。
- 复核证据的完整性受本地文件保管方式约束；如需防篡改介质，请接入签名/公证环节。
