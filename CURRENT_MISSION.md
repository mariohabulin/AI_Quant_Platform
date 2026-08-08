# CURRENT MISSION

## Paper Readiness Gate v1 — Representative Replay Consistency + Roadmap Reconciliation

**Status:** IMPLEMENTED / VALIDATION PENDING

### Objective

Convert Backtest ↔ Paper Replay consistency diagnostics into an explicit readiness decision before external real-time market connectivity is introduced, while reconciling project documentation with the implementation that already exists.

### Implemented

- `PaperReadinessGate` aggregates named representative consistency scenarios
- evidence classifications: `MATCH`, `INTENDED`, `DEFECT`, `CONFIGURATION_MISMATCH`
- only exact, explicitly expected `INTENDED` semantic differences may pass
- unexpected difference fields block readiness
- stale allow-lists block readiness when an expected divergence disappears
- defect and configuration-mismatch classifications remain blocking even when their fields are known
- structured per-scenario evidence and aggregate `READY / BLOCKED` result
- ROADMAP reorganized into COMPLETED / CURRENT / NEXT / SHOULD HAVE / DEFERRED
- basic restart recovery promoted into the pre-unattended-paper runtime milestone

### Definition of Done

- readiness-gate tests pass
- full regression remains green
- matched representative scenarios pass as `MATCH`
- known forced-close semantics can be explicitly classified without hiding new divergence
- execution/configuration drift blocks the gate
- documentation matches actual project state

### Next after validation

Build the Real-Time Market Data Adapter + Feed Health boundary for one selected provider and one controlled asset/timeframe. External connectivity must continue to emit the existing normalized `MarketDataEvent` contract.
