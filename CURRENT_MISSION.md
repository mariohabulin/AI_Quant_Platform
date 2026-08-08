# CURRENT MISSION

## Backtest ↔ Paper Replay Consistency Validator v1

**Status:** IMPLEMENTED / VALIDATION PENDING

### Objective

Measure whether deterministic historical backtesting and event-driven paper replay tell the same execution story under matched strategy, risk and execution assumptions, and produce explicit diagnostics when they do not.

### Implemented

- structured `ReplayConsistencyReport` with `CONSISTENT / DIVERGENT` status
- field-level `ConsistencyDifference` diagnostics
- same-history replay through `HistoricalReplayFeed`
- bar-by-bar signal-sequence comparison
- completed round-trip count comparison
- quantity, entry/exit fill, commission and trade P&L comparison
- final-equity comparison
- final open-position-state comparison
- configurable numeric tolerance
- explicit detection of backtest forced-close versus persistent paper-position semantics
- fresh-session requirement to prevent contaminated comparisons

### Definition of Done

- consistency-validator tests pass
- full regression remains green
- matched execution assumptions can produce a clean `CONSISTENT` report
- intentionally mismatched execution assumptions produce useful field-level diagnostics
- semantic differences are exposed, not silently corrected

### Next after validation

Use the validator on representative real strategies/data and decide which divergences are intended semantics versus defects. Real streaming/provider integration remains deferred until replay/backtest consistency evidence is understood.
