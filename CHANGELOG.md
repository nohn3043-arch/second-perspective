# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-09-22

### Added

**Assumption Interaction Layer** (`src/second_perspective/interaction/`)
- New `interaction/` module with four formal invariants (I-1 through I-4):
  - I-1 Non-conjectural: every interaction strength Δ is explicitly declared by a responsible party; the engine never estimates or learns Δ.
  - I-2 Order-conservation: interactions only apply when **all** member assumptions are simultaneously invalidated.
  - I-3 Effect-boundedness: cumulative interaction effect ≤ `amplification_ceiling × Σ|first_order|`; redundant (negative) interactions have no floor clamp.
  - I-4 Monotonicity (union semantics): adding a failure never un-triggers an already-triggered interaction (`augment()`).
- Three interaction types: `conjunctive` (amplification, Δ > 0), `disjunctive` (redundancy, Δ < 0), `degenerate` (Δ = 0, retained as proof of inspection).
- `InteractionEngine` with `triggered()`, `joint_effect()`, `augment()` methods.
- Declaration validator (`validate_all()`) enforcing all four invariants at construction time.

**Formal Convergence** (`src/second_perspective/convergence/`)
- New `convergence/` module replacing heuristic stop checks with a formally-classified five-state model:
  - `FIXED_POINT` — candidate set stable (true convergence, P-2).
  - `NO_GAIN` — no unresolved branches (true convergence).
  - `BUDGET_EXHAUSTED` — budget ran out (**not** convergence; requires human).
  - `DIVERGED` — still changing with budget remaining.
  - `BLOCKED` — structural blocking condition hit (requires human).
- `is_true_convergence` guard against the classic "budget exhaustion misclassified as convergence" bug.
- Three checkable propositions (P-1 Termination, P-2 Fixed-point, P-3 Effect-boundedness).
- Pure, stateless `ConvergenceChecker` class with deterministic output.

**LLM Compliance Layer** (`src/second_perspective/llm_compliance/`)
- New `llm_compliance/` module formalizing a three-tier permission model:
  - T1 (Annotation): LLM may label/propose descriptions — no structural change.
  - T2 (Proposal): LLM may propose alternatives/weights/deltas — all subject to human approval.
  - T3 (Narrative): LLM may generate explanatory text — never used as decision input.
- Three invariants (L-1 through L-3): zone isolation, no adjudication, strength stripping.
- `LLMGate` enforcing that LLM output can never directly flip status, adjudicate, or alter weights.
- Provenance tracking (model id, timestamp, prompt fingerprint) on every LLM call.

**Core integration points** (non-breaking additions)
- `models/enums.py`: added `InteractionEffectType` enum.
- `models/schemas.py`: added `InteractionDecl`, `InteractionDeclaration`, and an optional `interaction_declaration` field on `DecisionRequest`; added `triggered_interaction_ids` and `interaction_contribution` optional fields on `FailureBranch`.
- `decision/causal.py`: added `invalidation_closure_with_interaction()` returning first-order closure plus an optional `InteractionPropagationResult`; original `invalidation_closure()` is unchanged.
- `hub/session.py`: `_stop_condition()` now delegates to the formal `ConvergenceChecker` internally while preserving the existing `(SessionStatus, ConvergenceKind | None)` return contract for full backward compatibility.

### Tests
- 122 new tests across `test_interaction.py` (28), `test_convergence.py` (38), `test_llm_compliance.py` (39), and `test_v04_integration.py` (17).
- Full regression: **402 passed, 0 failures** (previously 280).

### Backward Compatibility
- All existing APIs and default behaviours are unchanged.
- When `interaction_declaration` is not supplied (the default), the engine behaves identically to v0.3.
- No existing functions or classes were removed or renamed.
- `Cognitive Audit Engine` (GCAE) was not modified.

---

## [0.3.0] - 2026-09-19 (previous release)

- Deterministic alternative evaluation with constraint + weighted scoring.
- Forward invalidation propagation (`invalidation_closure`).
- Counterfactual analysis (what-if on assumption failure).
- Three-layer reconstruction sessions (forward/backward/delta).
- Scenario stress testing.
- Cognitive audit engine (GCAE).
- FastAPI service layer and CLI entry points.
- PostgreSQL-backed repository.
