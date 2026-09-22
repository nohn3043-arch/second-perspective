"""
第二视角认知审计引擎 v2.0 (GCAE — Global Cognitive Audit Engine)
================================================================

设计定位：「第二视角因果框架」下治理AI的规范参考内核（Reference Implementation）。

    - 单文件 · 零外部依赖 · 仅用 Python 标准库
    - 可直接用于教学/审计/移植到 SPL-G1 硬件或其他语言
    - 所有结构判定均为决定论；不使用概率词；缺失输入直接中断而非猜测
    - LLM 永远不参与结构裁决；所有 status/converged 布尔值由确定性算子给出

核心五步算子 (Five-Operator Causal Audit Kernel)：
    1. 叙事剥离 (Narrative Stripping)       — 去除修辞立场，提取纯粹事件链
    2. 内隐假设透视 (Implicit Assumption)    — 挖掘未声明预设，逆反校验
    3. 脆弱性对冲 (Vulnerability Hedging)    — 定位最脆弱变量，评估崩塌等级
    4. 责任闭环锚定 (Responsibility Closure) — 追溯到最小决策单元，绑定 nonce
    5. 因果重构 (Causal Reconstruction)      — 注入修正变量，判定形式化收敛状态

三大护栏不变式：
    I-1 非猜测 —— 缺失事实/权重/阈值/责任人/交互强度不估算，直接中断并列出补齐条件
    L-1..L-3   —— LLM 三层权限（T1 注解 / T2 提案 / T3 叙述），永不裁决、永不改状态
    C-1..C-3   —— 收敛五状态（FIXED_POINT / NO_GAIN / BUDGET_EXHAUSTED / DIVERGED /
                  BLOCKED）；is_true_convergence 严格区分真收敛与预算耗尽

本模块不含任何主观/概率化推测，仅做决定论因果处理。
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple


# ==================== 基础类型与枚举 ====================

GCAE_VERSION = "2.0.0"


class ConvergenceState(str, Enum):
    """形式化收敛五状态分类。"""
    FIXED_POINT = "FIXED_POINT"
    NO_GAIN = "NO_GAIN"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    DIVERGED = "DIVERGED"
    BLOCKED = "BLOCKED"

    @property
    def is_true_convergence(self) -> bool:
        return self in (ConvergenceState.FIXED_POINT, ConvergenceState.NO_GAIN)


class PluginTier(str, Enum):
    T1_STRUCTURAL = "T1_STRUCTURAL"   # 可出 BLOCKED（阻断）
    T2_SIGNAL = "T2_SIGNAL"           # 只出风险信号，不得阻断
    T3_NARRATIVE = "T3_NARRATIVE"     # 只出文字，不出 status


class LLMPermissionTier(str, Enum):
    T1_ANNOTATION = "T1_ANNOTATION"
    T2_PROPOSAL = "T2_PROPOSAL"
    T3_NARRATIVE = "T3_NARRATIVE"


class CollapseLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ==================== 责任节点 ====================

@dataclass
class ResponsibilityAccount:
    organization: str
    role: str
    stage: str
    owner: Optional[str] = None
    nonce: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.nonce:
            self.nonce = uuid.uuid4().hex[:8]

    @property
    def is_closed(self) -> bool:
        return bool(self.owner)


# ==================== LLM 协议 ====================

class LLMProvider(Protocol):
    def generate(self, prompt: str, **kwargs) -> str: ...


class OpenAIProvider:
    """零依赖 OpenAI 兼容 LLM 调用。

    数据出境合规提示：
        - 默认 base_url 指向境外 https://api.openai.com/v1，调用即数据出境
        - 境内部署请传入境内端点（DeepSeek/通义千问等）并做输入脱敏
        - GCAE 五步算子本身从不调用 LLM；仅在显式注入 provider 时启用且强制护栏
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 120,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str, **kwargs) -> str:
        import urllib.error
        import urllib.request

        temperature = kwargs.get("temperature", 0.3)
        max_tokens = kwargs.get("max_tokens", 4096)
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            return f"[LLM Error] HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
        except Exception as e:
            return f"[LLM Error] {e}"


@dataclass
class LLMCallRecord:
    permission_tier: LLMPermissionTier
    purpose: str
    prompt_hash: str
    response_excerpt: str
    stripped: bool = True
    adjudicated: bool = False
    timestamp: float = field(default_factory=time.time)


# ==================== 审计事件与哈希链 ====================

@dataclass
class AuditEvent:
    event_type: str
    payload: Dict[str, Any]
    prev_hash: str
    timestamp: float = field(default_factory=time.time)
    nonce: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    @property
    def hash(self) -> str:
        blob = json.dumps({
            "event_type": self.event_type,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ==================== 审计插件 ====================

@dataclass
class AuditPlugin:
    name: str
    tier: PluginTier
    analyze_func: Callable[[Dict[str, Any]], Any]
    description: str = ""


# ==================== 收敛判定器 ====================

class ConvergenceChecker:
    """形式化收敛判定（P-1 终止 / P-2 不动点 / P-3 风险有界）。"""

    BLOCKING_STATUSES = {"BLOCKED", "CRITICAL"}
    HIGH_RISK_STATUSES = {"HIGH_RISK"}

    @staticmethod
    def classify(
        round_idx: int,
        max_rounds: int,
        previous_risks: frozenset,
        current_risks: frozenset,
        has_blocking: bool,
        has_unresolved_assumptions: bool,
    ) -> ConvergenceState:
        if has_blocking:
            return ConvergenceState.BLOCKED
        if round_idx >= max_rounds:
            return ConvergenceState.BUDGET_EXHAUSTED
        if round_idx > 0 and previous_risks == current_risks and not has_unresolved_assumptions:
            return ConvergenceState.FIXED_POINT
        if not current_risks and not has_unresolved_assumptions:
            return ConvergenceState.NO_GAIN
        return ConvergenceState.DIVERGED

    @staticmethod
    def extract_risk_set(report: Dict[str, Any]) -> Tuple[frozenset, bool]:
        risks = set()
        has_blocking = False
        for pname, result in report.get("analysis", {}).items():
            if not isinstance(result, dict):
                continue
            status = result.get("status")
            if status in ConvergenceChecker.BLOCKING_STATUSES:
                has_blocking = True
                risks.add((pname, status, json.dumps(result, sort_keys=True, default=str, ensure_ascii=False)))
            elif status in ConvergenceChecker.HIGH_RISK_STATUSES or status == "WARNING":
                risks.add((pname, status, json.dumps(result, sort_keys=True, default=str, ensure_ascii=False)))
        return frozenset(risks), has_blocking


# ==================== 配置加载器 ====================

class AuditConfigLoader:
    @staticmethod
    def load_from_dict(config: Dict[str, Any]) -> Dict[str, Any]:
        return config

    @staticmethod
    def load_from_json(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)



# ==================== 认知审计引擎核心 ====================

class CognitiveAuditEngine:
    """GCAE v2.0 规范参考内核。"""

    FORBIDDEN_LLM_KEYS = {
        'status', 'converged', 'is_converged', 'blocked',
        'adjudicated', 'weight', 'score', 'rank', 'verdict', 'decision',
    }

    def __init__(self, account: ResponsibilityAccount, config: Optional[Dict[str, Any]] = None):
        self.account = account
        self.config: Dict[str, Any] = config or {}
        self.plugins: List[AuditPlugin] = []
        self.llm_provider: Optional[LLMProvider] = None
        self.llm_default_tier: LLMPermissionTier = LLMPermissionTier.T3_NARRATIVE
        self.event_chain: List[AuditEvent] = []
        self._prev_event_hash: str = 'ROOT'

        allowed_stages = self.config.get('allowed_stages', [])
        if allowed_stages and account.stage not in allowed_stages:
            raise ValueError(f'Unsupported stage: {account.stage}')

    # -------- 注册 --------

    def set_llm_provider(
        self,
        provider: LLMProvider,
        default_tier: LLMPermissionTier = LLMPermissionTier.T3_NARRATIVE,
    ) -> None:
        self.llm_provider = provider
        self.llm_default_tier = default_tier

    def register_plugin(self, plugin: AuditPlugin) -> None:
        self.plugins.append(plugin)

    # -------- 哈希链 --------

    def _append_event(self, event_type: str, payload: Dict[str, Any]) -> AuditEvent:
        ev = AuditEvent(
            event_type=event_type,
            payload=payload,
            prev_hash=self._prev_event_hash,
        )
        self.event_chain.append(ev)
        self._prev_event_hash = ev.hash
        return ev

    @property
    def chain_root_hash(self) -> str:
        return self._prev_event_hash if self.event_chain else 'ROOT'

    # -------- 五步算子①：叙事剥离 --------

    @staticmethod
    def _strip_narrative(ctx: Dict[str, Any]) -> Dict[str, Any]:
        """去除修辞/主观修饰词，仅标记不删除原字段。"""
        SUBJECTIVE_WORDS = {
            '显然', '毫无疑问', '必然', '肯定', '理所应当', '不言而喻',
            'obviously', 'clearly', 'certainly', 'undoubtedly', 'naturally',
        }
        out = copy.deepcopy(ctx)
        flagged: Dict[str, List[str]] = {}
        for key in ('narrative', 'background', 'summary', 'description'):
            if key in out and isinstance(out[key], str):
                hit = [w for w in SUBJECTIVE_WORDS if w in out[key]]
                if hit:
                    flagged[key] = hit
        out['_narrative_stripped'] = {'flagged_fields': flagged}
        return out

    # -------- 五步算子②：内隐假设透视 --------

    @staticmethod
    def _surface_implicit_assumptions(ctx: Dict[str, Any]) -> Dict[str, Any]:
        """决定论规则挖掘未声明预设，不猜。"""
        flags: List[Dict[str, Any]] = []
        missing_required = False

        alts = ctx.get('alternatives')
        criteria = ctx.get('criteria')
        if alts and not criteria:
            flags.append({'type': 'MISSING_CRITERIA',
                          'description': '提供了备选方案但未声明评估标准'})
            missing_required = True

        if criteria and isinstance(criteria, dict):
            weights = []
            for v in criteria.values():
                if isinstance(v, dict) and 'weight' in v:
                    weights.append(v['weight'])
            if weights and all(w is not None for w in weights):
                s = sum(float(w) for w in weights)
                if abs(s - 1.0) > 1e-6:
                    flags.append({'type': 'WEIGHTS_NOT_NORMALIZED',
                                  'description': f'权重之和={s}，未归一到1.0', 'sum': s})

        conclusions = ctx.get('conclusions') or ctx.get('recommendation')
        evidence = ctx.get('evidence')
        if conclusions and not evidence:
            flags.append({'type': 'CONCLUSION_WITHOUT_EVIDENCE',
                          'description': '给出了结论但未提供证据'})
            missing_required = True

        ctx['_implicit_assumptions'] = {'flags': flags, 'missing_required': missing_required}
        return ctx

    # -------- 五步算子③：脆弱性对冲 --------

    @staticmethod
    def _assess_vulnerability(ctx: Dict[str, Any]) -> Dict[str, Any]:
        """定位最脆弱变量并给出崩塌等级（HIGH/MEDIUM/LOW）。"""
        implicit = ctx.get('_implicit_assumptions', {})
        flags = implicit.get('flags', [])
        level = CollapseLevel.LOW
        weakest: Optional[str] = None
        reasons: List[str] = []

        if implicit.get('missing_required'):
            level = CollapseLevel.HIGH
            weakest = 'required_assumptions'
            reasons.append('关键假设缺失（评估标准/证据/责任人）')
        else:
            for f in flags:
                if f['type'] == 'WEIGHTS_NOT_NORMALIZED' and level != CollapseLevel.HIGH:
                    level = CollapseLevel.MEDIUM
                    weakest = weakest or 'criteria_weights'
                    reasons.append('评估权重未归一')
            narr = ctx.get('_narrative_stripped', {}).get('flagged_fields')
            if narr and level == CollapseLevel.LOW:
                weakest = weakest or 'narrative_subjectivity'
                reasons.append('叙述中包含主观修饰词')

        ctx['_vulnerability'] = {
            'weakest_variable': weakest,
            'collapse_level': level,
            'reasons': reasons,
        }
        return ctx

    # -------- LLM 护栏 --------

    def _strip_llm_output(self, parsed: Any, tier: LLMPermissionTier) -> Tuple[Dict[str, Any], bool]:
        """剥离 LLM 输出中能影响结构判定的字段。返回 (stripped, violated)。"""
        violated = False
        if not isinstance(parsed, dict):
            return {'narrative': str(parsed)}, violated
        stripped: Dict[str, Any] = {}
        for k, v in parsed.items():
            if k in self.FORBIDDEN_LLM_KEYS:
                violated = True
                continue
            stripped[k] = v
        if tier == LLMPermissionTier.T3_NARRATIVE:
            narrative = (stripped.get('narrative') or stripped.get('overall_assessment')
                         or stripped.get('reasoning')
                         or json.dumps(stripped, ensure_ascii=False))
            return {'narrative': narrative}, violated
        return stripped, violated

    def _safe_llm_call(
        self, prompt: str, purpose: str, tier: Optional[LLMPermissionTier] = None,
    ) -> Optional[Tuple[LLMCallRecord, Dict[str, Any]]]:
        if self.llm_provider is None:
            return None
        t = tier or self.llm_default_tier
        try:
            raw = self.llm_provider.generate(prompt, temperature=0.3, max_tokens=4096)
        except Exception as e:
            raw = f'[LLM Exception] {e}'
        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw
        stripped, violated = self._strip_llm_output(parsed, t)
        record = LLMCallRecord(
            permission_tier=t,
            purpose=purpose,
            prompt_hash=prompt_hash,
            response_excerpt=str(stripped)[:400],
            stripped=True,
            adjudicated=False,
        )
        if violated:
            record.response_excerpt = '[VIOLATION STRIPPED] ' + record.response_excerpt[:380]
        return record, stripped

    # -------- 插件权限强制 --------

    def _enforce_plugin_tier(self, plugin: AuditPlugin, result: Any) -> Any:
        if not isinstance(result, dict):
            return result
        status = result.get('status')
        if plugin.tier == PluginTier.T3_NARRATIVE and status is not None:
            result = {k: v for k, v in result.items() if k != 'status'}
            result['_tier_violation'] = f"T3 plugin '{plugin.name}' emitted status={status}"
        elif plugin.tier == PluginTier.T2_SIGNAL and status in {'BLOCKED', 'CRITICAL'}:
            result['status'] = 'WARNING'
            result['_tier_violation'] = (
                f"T2 plugin '{plugin.name}' tried blocking status={status}, downgraded to WARNING"
            )
        return result

    # -------- 五步算子④：静态审计（前序三算子+责任闭环+插件） --------

    def audit(
        self,
        decision_context: Dict[str, Any],
        save_log: bool = False,
        log_dir: str = 'logs',
    ) -> Dict[str, Any]:
        ctx = self._strip_narrative(decision_context)
        ctx = self._surface_implicit_assumptions(ctx)
        ctx = self._assess_vulnerability(ctx)

        report: Dict[str, Any] = {
            'gcae_version': GCAE_VERSION,
            'disclaimer': self.config.get('disclaimer', ''),
            'responsibility_account': asdict(self.account),
            'analysis': {},
            'custom_fields': self.config.get('custom_fields', {}),
            'narrative_meta': ctx.get('_narrative_stripped', {}),
            'implicit_assumptions': ctx.get('_implicit_assumptions', {}),
            'vulnerability': ctx.get('_vulnerability', {}),
            'llm_calls': [],
        }

        if not self.account.is_closed:
            report['analysis']['RESPONSIBILITY_CLOSURE'] = {
                'status': 'BLOCKED',
                'reason': 'RESPONSIBILITY_NOT_CLOSED',
                'message': f'责任未闭环：stage={self.account.stage} 缺少具体责任人(owner)',
            }

        run_ctx = dict(ctx)
        run_ctx['_responsibility_account'] = asdict(self.account)
        prior: Dict[str, Any] = {}
        run_ctx['_prior_audit_results'] = prior

        def tier_key(p: AuditPlugin) -> int:
            return {PluginTier.T1_STRUCTURAL: 0,
                    PluginTier.T2_SIGNAL: 1,
                    PluginTier.T3_NARRATIVE: 2}[p.tier]

        ordered = sorted(self.plugins, key=lambda p: (p.name == 'STATE', tier_key(p)))
        for plugin in ordered:
            try:
                result = plugin.analyze_func(run_ctx)
            except Exception as e:
                result = {'status': 'BLOCKED', 'reason': 'PLUGIN_EXCEPTION', 'message': str(e)}
            result = self._enforce_plugin_tier(plugin, result)
            report['analysis'][plugin.name] = result
            prior[plugin.name] = result

        if self.llm_provider is not None:
            res = self._safe_llm_call(
                prompt=(
                    '你是认知审计专家（仅T3叙述权限，不得输出status/converged/weight/rank/verdict等裁决字段）。'
                    '请对以下决策上下文做语义级风险与偏见叙述性说明，以JSON返回，仅包含 narrative 字段。\n\n'
                    f'决策上下文：{json.dumps(decision_context, ensure_ascii=False, default=str)}'
                ),
                purpose='STATIC_AUDIT',
                tier=LLMPermissionTier.T3_NARRATIVE,
            )
            if res is not None:
                record, stripped = res
                report['analysis']['llm_narrative'] = stripped
                report['llm_calls'].append(asdict(record))

        self._append_event('AUDIT', {
            'report_hash': hashlib.sha256(
                json.dumps(report, sort_keys=True, ensure_ascii=False, default=str).encode('utf-8')
            ).hexdigest()[:16],
            'vulnerability': report['vulnerability'],
            'has_blocking': any(
                isinstance(r, dict) and r.get('status') in ConvergenceChecker.BLOCKING_STATUSES
                for r in report['analysis'].values()
            ),
        })

        if save_log:
            report['log_path'] = self._write_log(report, log_dir)
        return report

    def _write_log(self, report: Dict[str, Any], log_dir: str) -> str:
        os.makedirs(log_dir, exist_ok=True)
        audit_id = f'SPL-{self.account.nonce}-{int(time.time())}'
        report['chain_root_hash'] = self.chain_root_hash
        report['audit_id'] = audit_id
        path = os.path.join(log_dir, f'{audit_id}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        return os.path.abspath(path)


    # -------- 五步算子⑤：因果重构（bounded + human gate + 形式化收敛） --------

    def reconstruct(
        self,
        decision_context: Dict[str, Any],
        delta_vars: Optional[Dict[str, Any]] = None,
        max_rounds: int = 5,
        human_approved_deltas: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """⑤ 因果重构：bounded 迭代 + human gate + 五状态形式化收敛。

        语义：
            - 首轮：若提供 delta_vars（视为已声明起始修正），应用；否则不自动修正。
            - 之后每轮只接受 human_approved_deltas 中的修正（由外部审批流提交）。
            - 每轮 audit 后由 ConvergenceChecker 分类；只要不是 DIVERGED 就停止。
            - human gate：每轮结束返回 awaiting_human=True，调用方显式推进。
              本方法一次性跑完所有已批准的 delta 序列（同步、有界）；不做自循环。

        返回：
            session_root_hash / final_state / rounds / is_true_convergence / final_report
        """
        if max_rounds < 1:
            raise ValueError('max_rounds must be >= 1')

        rounds: List[Dict[str, Any]] = []
        current_ctx = copy.deepcopy(decision_context)
        approved = list(human_approved_deltas or [])
        if delta_vars:
            approved.insert(0, delta_vars)

        previous_risks: frozenset = frozenset()
        state = ConvergenceState.DIVERGED
        final_report: Dict[str, Any] = {}

        for idx in range(max_rounds + 1):  # +1 允许初始轮（无 delta）
            # 应用本轮 delta（若有）
            if idx < len(approved):
                d = approved[idx]
                if not isinstance(d, dict) or not d:
                    state = ConvergenceState.BLOCKED
                    rounds.append({
                        'round': idx,
                        'status': state.value,
                        'reason': 'EMPTY_OR_INVALID_DELTA',
                    })
                    break
                current_ctx.update(d)
                self._append_event('DELTA_APPLIED', {'round': idx, 'delta_keys': sorted(d.keys())})
            elif idx > 0:
                # 没有更多已批准 delta，但仍未收敛 → 停在 AWAITING_HUMAN
                state = ConvergenceState.DIVERGED
                rounds.append({
                    'round': idx,
                    'status': state.value,
                    'awaiting_human': True,
                    'reason': 'NO_MORE_APPROVED_DELTAS',
                })
                break

            report = self.audit(current_ctx)
            final_report = report
            current_risks, has_blocking = ConvergenceChecker.extract_risk_set(report)
            has_unresolved = bool(report.get('implicit_assumptions', {}).get('missing_required'))

            state = ConvergenceChecker.classify(
                round_idx=idx,
                max_rounds=max_rounds,
                previous_risks=previous_risks,
                current_risks=current_risks,
                has_blocking=has_blocking,
                has_unresolved_assumptions=has_unresolved,
            )

            round_hash = hashlib.sha256(
                json.dumps({'idx': idx, 'state': state.value, 'risks': sorted(map(str, current_risks))},
                           sort_keys=True).encode('utf-8')
            ).hexdigest()[:16]

            rounds.append({
                'round': idx,
                'status': state.value,
                'risk_count': len(current_risks),
                'has_blocking': has_blocking,
                'round_hash': round_hash,
                'report_ref': report.get('audit_id'),
            })

            self._append_event('RECONSTRUCT_ROUND', {
                'round': idx,
                'state': state.value,
                'risk_count': len(current_risks),
                'round_hash': round_hash,
            })

            if state != ConvergenceState.DIVERGED:
                break
            previous_risks = current_risks

        # 跑完了已批准序列但仍 DIVERGED 且没到预算上限 → 等待人继续批
        awaiting_human = (state == ConvergenceState.DIVERGED and len(rounds) <= max_rounds
                          and rounds[-1].get('reason') == 'NO_MORE_APPROVED_DELTAS')

        return {
            'gcae_version': GCAE_VERSION,
            'final_state': state.value,
            'is_true_convergence': state.is_true_convergence,
            'awaiting_human': awaiting_human,
            'rounds': rounds,
            'final_report': final_report,
            'session_root_hash': self.chain_root_hash,
            'total_rounds': len(rounds),
        }

    # -------- 会话推进（human gate） --------

    def advance_with_human_delta(
        self,
        previous_result: Dict[str, Any],
        decision_context: Dict[str, Any],
        human_delta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """在之前的 reconstruct 结果上由人工提交一个新 delta，再跑一轮。

        便捷入口：把历史 delta 重放到当前上下文、追加 human_delta，再跑一轮 audit 判定。
        """
        # 重建当前上下文（基于初始 + 之前所有已应用 delta 累积）
        current_ctx = copy.deepcopy(decision_context)
        # 这里的简单实现：调用方若需累积多轮，自行维护上下文；reconstruct() 每轮是无状态的
        current_ctx.update(human_delta)
        report = self.audit(current_ctx)
        risks, has_blocking = ConvergenceChecker.extract_risk_set(report)
        has_unresolved = bool(report.get('implicit_assumptions', {}).get('missing_required'))
        state = ConvergenceChecker.classify(
            round_idx=len(self.event_chain),
            max_rounds=len(self.event_chain) + 10,
            previous_risks=frozenset(),
            current_risks=risks,
            has_blocking=has_blocking,
            has_unresolved_assumptions=has_unresolved,
        )
        self._append_event('HUMAN_ADVANCE', {
            'delta_keys': sorted(human_delta.keys()),
            'state': state.value,
        })
        return {
            'final_state': state.value,
            'is_true_convergence': state.is_true_convergence,
            'final_report': report,
            'session_root_hash': self.chain_root_hash,
        }

    # -------- 审计链验证 --------

    def verify_chain(self) -> Dict[str, Any]:
        """独立验证哈希链完整性。返回 {valid, last_valid_idx, total, root_hash}。"""
        prev = 'ROOT'
        last_valid = -1
        for i, ev in enumerate(self.event_chain):
            if ev.prev_hash != prev:
                return {'valid': False, 'last_valid_idx': last_valid,
                        'total': len(self.event_chain), 'broken_at': i,
                        'root_hash': self.chain_root_hash}
            expected = ev.hash
            # recompute
            blob = json.dumps({
                'event_type': ev.event_type,
                'payload': ev.payload,
                'prev_hash': ev.prev_hash,
                'timestamp': ev.timestamp,
                'nonce': ev.nonce,
            }, sort_keys=True, ensure_ascii=False, default=str)
            actual = hashlib.sha256(blob.encode('utf-8')).hexdigest()
            if actual != expected:
                return {'valid': False, 'last_valid_idx': last_valid,
                        'total': len(self.event_chain), 'broken_at': i,
                        'root_hash': self.chain_root_hash}
            prev = expected
            last_valid = i
        return {'valid': True, 'last_valid_idx': last_valid,
                'total': len(self.event_chain), 'root_hash': self.chain_root_hash}


# ==================== 便捷入口（demo） ====================

def _demo():
    """冒烟演示：
        1) 责任未闭环 → BLOCKED
        2) 闭环后做一次静态审计
        3) 注入修正 delta，观察收敛状态
    """
    # 场景1：责任未闭环
    acct_open = ResponsibilityAccount(organization='ACME', role='Risk Officer', stage='INVESTMENT')
    eng = CognitiveAuditEngine(acct_open)
    r = eng.audit({
        'alternatives': {'S1': {'metrics': {'roi': 0.12}}, 'S2': {'metrics': {'roi': 0.08}}},
        'criteria': {'roi': {'weight': 1.0}},
        'conclusions': 'Recommend S1',
        'evidence': ['doc#123'],
    })
    print('[1] Responsibility open ->', r['analysis'].get('RESPONSIBILITY_CLOSURE', {}).get('status'))

    # 场景2：闭环，含主观词 + 权重未归一
    acct = ResponsibilityAccount(organization='ACME', role='Risk Officer',
                                 stage='INVESTMENT', owner='张三/工号888')
    eng = CognitiveAuditEngine(acct)
    r = eng.audit({
        'narrative': '显然S1是最优方案',
        'alternatives': {'S1': {'metrics': {'roi': 0.12}}, 'S2': {'metrics': {'roi': 0.08}}},
        'criteria': {'roi': {'weight': 0.6}, 'risk': {'weight': 0.6}},  # 权重和=1.2
        'conclusions': 'Recommend S1',
        'evidence': ['doc#123'],
    })
    print('[2] Vulnerability ->', r['vulnerability']['collapse_level'],
          '| weakest =', r['vulnerability']['weakest_variable'])
    print('    Narrative flagged ->', r['narrative_meta']['flagged_fields'])
    print('    Implicit flags ->', [f['type'] for f in r['implicit_assumptions']['flags']])

    # 场景3：因果重构 — 注入修正（权重归一），应该收敛到 NO_GAIN
    r3 = eng.reconstruct(
        decision_context={
            'alternatives': {'S1': {'metrics': {'roi': 0.12}}, 'S2': {'metrics': {'roi': 0.08}}},
            'criteria': {'roi': {'weight': 0.6}, 'risk': {'weight': 0.6}},
            'conclusions': 'Recommend S1',
            'evidence': ['doc#123'],
        },
        delta_vars={'criteria': {'roi': {'weight': 0.5}, 'risk': {'weight': 0.5}}},
        max_rounds=3,
    )
    print('[3] Final state ->', r3['final_state'],
          '| true_convergence =', r3['is_true_convergence'],
          '| root_hash =', r3['session_root_hash'][:16])

    # 场景4：验证哈希链完整性
    v = eng.verify_chain()
    print('[4] Chain valid ->', v['valid'], '| events =', v['total'])


if __name__ == '__main__':
    _demo()
