# ROADMAP

# AI Alpha Engine Development Roadmap

## Purpose

This document is the project-level source of truth. Completed work, the current readiness gate, the next safe boundary and intentionally deferred work are kept explicit so implementation does not outrun evidence.

---

# COMPLETED

## Phase 1 — Data Foundation

Historical data collection, validation, storage and visualization foundation. **Status: COMPLETED.**

## Phase 2 — Research & Strategy Foundation

Feature Engine, Strategy Library, Strategy Engine, Backtesting Engine, Performance Analyzer and the validated strategy set (EMA, RSI, MACD, Bollinger Bands, Donchian, ATR, Supertrend, ADX and Stochastic). **Status: COMPLETED.**

## Phase 3 — Robustness / Validation Stack

Benchmarking, out-of-sample validation, walk-forward analysis, falsification, validation pipeline, multi-asset evidence and market-regime diagnostics. Strategy Optimizer itself is intentionally deferred; the evidence controls required before optimization are already in place. **Status: CORE VALIDATION COMPLETED.**

## Phase 4 — Risk Engine for Paper Trading

Risk Engine v1 position sizing, v2 account protection and v3 trade-risk policy: exposure cap, drawdown/daily/weekly guards, kill switch, stop/target validation and configurable minimum reward/risk. **Status: COMPLETED FOR PAPER TRADING.**

## Phase 5 — Deterministic Paper-Trading Foundation

Paper Broker v1, Paper Trading Engine v1, stateful Session v2, provider-neutral MarketDataEvent / HistoricalReplayFeed and Backtest ↔ Paper Replay Consistency Validator v1. **Status: COMPLETED.**

---

# COMPLETED READINESS GATE

## Objective

Turn replay-consistency diagnostics into explicit evidence before external real-time connectivity is introduced.

## Active milestone

**Paper Readiness Gate v1 — Representative Replay Consistency + Roadmap Reconciliation**

The gate classifies representative comparisons as `MATCH`, `INTENDED`, `DEFECT` or `CONFIGURATION_MISMATCH`. A divergence is never silently normalized: only an exact, explicitly allow-listed `INTENDED` semantic difference may pass. Defects, configuration mismatches, unexpected fields and stale allow-lists block readiness.

## Exit criteria

- representative consistency scenarios are green or explicitly classified as intended semantics
- no unresolved defect/configuration mismatch is hidden by the gate
- project documentation reflects actual implementation state
- full automated regression remains green

---

# NEXT — Real-Time Paper Trading Path

## Milestone 1 — Real-Time Market Data Adapter + Feed Health — COMPLETED

First provider contract: Alpaca crypto websocket bars, controlled `BTC/USD` 1-minute scope. Provider normalization plus stale/duplicate/out-of-order/future/missing-gap health gates emit only the existing `MarketDataEvent` contract. Authenticated network transport and reconnect/backoff stay in the runtime milestone so transport failure handling is tested at the operational boundary.

## Milestone 2 — Operational Safety / Paper Runtime — COMPLETED

Controlled runtime loop, graceful shutdown, exception isolation, heartbeat/health state, bounded feed-failure halt policy, Alpaca websocket authentication/subscription with reconnect/backoff, and minimal durable checkpoint/restart recovery are implemented and regression-validated. Basic restart recovery preserves broker/open-position, Risk Engine protection and session/feed continuity state so a restarted paper process does not wake up with trading amnesia.

## Milestone 3 — First Controlled Real-Time Paper Run — PRE-FLIGHT

Pre-Flight Gate v1 validates redacted credential presence, controlled BTC/USD 1-minute scope, explicit risk guards, paper-account state, writable checkpoint storage, hard-disabled execution, provider connectivity/subscription and runtime startability. Any failed check blocks progression.

After pre-flight passes, run the full chain on real market data with simulated money, conservative scope and explicit observability. Compare forward behavior against backtest/replay expectations before expanding assets, timeframes or autonomy.

---

# SHOULD HAVE DURING PAPER TRADING

- operational alerts and richer watchdog telemetry
- session performance reports and replay/forward comparison reports
- richer data-quality metrics and provider reconnect telemetry
- durable order/event audit storage for extended forward testing

These improve long-duration operations but do not block the first controlled real-time paper run once the minimum safe runtime exists.

---

# DEFERRED / POST-PAPER-TRADING ENHANCEMENTS

These items are intentionally deferred, **not rejected**. A deferred capability moves into active development when required for safe unattended operation, when forward evidence exposes a material model gap, or when the next architectural boundary cannot be completed safely without it.

## Risk and Portfolio

- portfolio correlation/concentration and aggregate multi-position exposure — wait for multi-position forward evidence
- portfolio allocation/weighting and volatility targeting — wait until multiple simultaneous opportunities are proven relevant
- VaR / Expected Shortfall — add only if they improve decisions beyond current drawdown/exposure controls
- conservative fractional Kelly — wait for sufficiently stable edge estimates
- Monte Carlo drawdown as a hard gate — wait until acceptable drawdown policy is empirically calibrated
- broker-specific margin/leverage/buying-power checks — wait until a broker/exchange target is selected
- emergency forced liquidation — wait for the execution state machine/live adapter; Risk Engine should not secretly become execution

## Strategy Intelligence

- regime-based automatic strategy selection — current regime evidence remains diagnostic until conditioned performance is robust
- additional strategies — add only when validation/paper evidence shows a real coverage gap
- Strategy Optimizer/adaptive parameter optimization — defer until evidence demonstrates need and overfitting controls can govern it
- AI Learning Engine / autonomous adaptation — defer until stable forward evidence and governance exist

## Execution / Market Microstructure

- limit/stop order lifecycle — market-order boundary first
- partial fills/liquidity simulation — add if paper/live evidence shows deterministic fills materially overstate execution
- latency, queue position and richer microstructure — venue/timeframe dependent; evidence must justify complexity
- live broker/exchange adapter — only after stable paper runtime and forward evidence
- advanced broker reconciliation — requires live connectivity

## Data / Runtime Scale

- bounded rolling-history/replay performance optimization — wait for measured session-duration and warm-up requirements
- broad provider/asset/timeframe expansion — first prove one provider + controlled scope
- large-scale consistency matrices — expand after the v1 readiness evidence contract is trusted on representative cases

---

# Long-Term Objective

Evolve the validated research/risk/paper foundation into a safely operated AI Alpha Trading Agent that can research, validate, manage risk, trade through replaceable execution/data boundaries and improve only when evidence justifies adaptation.

# Development Principle

Architecture Review → Design → TDD → Validation → Documentation → Git Integration. Progress is measured by evidence, deterministic behavior and safe boundaries rather than feature count.

## Provider Substitution — Coinbase Public Feed v1

- [x] Keep market-data provider replaceable; Alpaca is not a hard dependency.
- [x] Add public Coinbase `BTC-USD` market-trades transport without credentials.
- [x] Aggregate trades into completed 1-minute OHLCV bars before Feed Health.
- [x] Subscribe to heartbeats and bound reconnect attempts.
- [x] Allow pre-flight credential check to PASS explicitly for public providers.
- [ ] Run real network connectivity/subscription dry-run with execution hard-disabled.
- [ ] Observe completed real 1-minute bars through Feed Health and Operational Runtime.
- [ ] Only then authorize a supervised simulated-execution paper session.

- [x] Coinbase public market-data connectivity dry-run runner (bounded, execution OFF)

### Live Paper Bridge v1
- [x] Public Coinbase BTC-USD live market-data dry-run
- [x] Real-world trade-batch ordering regression protection
- [ ] Bounded live-data -> Operational Runtime -> PaperTradingSession -> Risk Engine -> PaperBroker proof
- Deferred until bounded proof: real exchange execution, API credentials, multi-asset live trading, long-running cloud deployment, production monitoring, calibrated transaction costs. These add operational/capital risk without helping prove the current boundary.

### Forward Paper Session v1
- [x] Prove bounded Coinbase live-data -> Operational Runtime -> PaperTradingSession -> Risk Engine -> PaperBroker path.
- [x] Add supervised longer-session runner with configurable healthy-bar bound.
- [x] Add append-only JSONL audit records for accepted/rejected bars, strategy/risk/order outcome, account snapshot and explicit real-orders=0 evidence.
- [ ] Prove a naturally occurring paper entry and exit over forward data; do not manufacture signals merely to demonstrate orders.
- [ ] Add crash-transparent strategy-history/aggregator recovery before claiming unattended restart continuity. Reason: existing checkpoint state restores broker/risk/feed/session continuity, but not the accumulating EMA history or an in-progress 1m trade bucket.
- [ ] Add unattended/cloud operation only after forward-session evidence, restart continuity and operational alerting are proven.

### Forward Paper Continuity / Recovery v1
- [x] Add atomic forward continuity state covering runtime checkpoint, EMA input history and in-progress Coinbase 1m aggregation bucket.
- [x] Add one-time bootstrap from the first v1 live audit so the existing open paper position is not forgotten.
- [x] Keep mutable `runtime/*.json` and `runtime/*.jsonl` artifacts out of Git; retain the first live audit as immutable milestone evidence under `docs/evidence/`.
- [ ] Prove continuity live: bootstrap the audited position, restart, and confirm cash/position/order sequence before processing additional bars.
- [ ] Longer unattended/cloud sessions remain deferred until live restart continuity is proven.

### Restart Gap Reconciliation v1
- [x] Distinguish an intentional process-restart gap from an in-session missing-data defect.
- [x] Make the first fresh excessive-gap boundary bar non-tradable and audit-visible.
- [x] Restore normal strict gap enforcement immediately after the boundary.
- [x] Bound resumed forward sessions by bars processed in the current invocation.
- [ ] Prove the reconciliation path on live Coinbase data while preserving the existing paper position and `REAL_orders=0`.


### Extended Forward Run Readiness + Session Report v1
- [x] Add deterministic latest-session JSONL reporting with fail-closed audit-boundary validation.
- [x] Report bars/rejections/rebases, signals, risk outcomes, paper fills, equity/P&L, max drawdown, final position and real-order evidence.
- [ ] Run the first supervised 30-60 bar Coinbase forward-paper session and review its report before increasing duration.
- [ ] Keep unattended/cloud execution deferred until repeated supervised runs are clean and operational alerting is defined.

### Coinbase Late-Trade Ordering Robustness v2
Extended forward observation exposed event-time reordering across separate Coinbase websocket messages. Add a bounded 2-second event-time reorder buffer before strict minute aggregation, persist the pending buffer in forward continuity state, and keep truly late trades fail-closed after the watermark. This adds a small intentional bar-finalization delay to preserve OHLCV correctness rather than silently dropping late trades.

- [x] Align Coinbase completed-bar freshness with interval-close semantics after late-trade reorder buffering.

### Coinbase Transport Resilience v1
- [x] Confirm Coinbase public transport already subscribes to heartbeats and has bounded reconnect.
- [x] Distinguish transport reconnect evidence from market-data/feed-health evidence.
- [x] Reset reconnect attempt budget after a successfully restored connection instead of accumulating transient outages for the life of the process.
- [x] Discard incomplete/pending 1m aggregation state across a disconnect; do not manufacture a bar from potentially missed trades.
- [x] Reconcile the first fresh excessive-gap bar after reconnect as a non-tradable boundary, then restore normal strict Feed Health checks.
- [x] Report repeated Feed Health safety shutdown as `RUNTIME_HALTED`, not `TRANSPORT_ENDED`.
- [ ] Prove reconnect/rebase behavior on live Coinbase data and then repeat the supervised 30-bar forward run.
- Deferred: multi-provider failover and distributed supervision. Reason: one-provider reconnect/recovery must first be proven repeatedly before adding redundant infrastructure.

- [x] Transport Failure Recovery v2: bounded reconnect backoff, fatal transport audit closure, continuity checkpoint.


## Reconnect Replay Reconciliation v1
- Completed Coinbase bars at or behind the already-accepted feed watermark are classified as provider replay and dropped before the trading/Feed Health pipeline.
- Replay drops remain audit-visible (`PROVIDER_REPLAY_DROPPED`) but do not consume the operational runtime consecutive-failure budget.
- Fresh forward bars still pass through strict freshness, ordering and missing-gap validation; real execution remains impossible.
- This change targets the observed 10:25 -> 10:23 -> 10:24 replay sequence that previously caused a false `RUNTIME_HALTED` during the supervised 30-bar run.

## Forward Operational Diagnostics v1
- Add transport-quality and market-time continuity metrics to the deterministic forward-session report.
- Add signal activity and Risk Engine rejection diagnostics without changing trading policy.
- Use the diagnostics to judge the next 60-bar supervised gate before multi-hour/overnight soak testing.

## Future Scale Milestone — 24/7 Market Universe Scanner and Orchestration

The current `BTC-USD` Coinbase path is a controlled proving ground for live-paper transport, continuity, Feed Health, risk and operational safety. It is **not** the intended final trading scope.

After single-symbol operational stability and extended forward evidence are proven, expand toward a 24/7 market-intelligence architecture:

1. **Universe Manager** — maintain a configurable universe across supported crypto, equities and other approved markets; understand venue/session calendars and which instruments are currently actionable.
2. **Lightweight Market Scanner** — continuously screen the broad universe using low-cost liquidity, volume, volatility, trend, momentum, breakout and regime criteria.
3. **Candidate Ranking** — rank/filter scanner output so only the strongest candidates enter expensive analysis.
4. **Deep Analysis** — run relevant Strategy Library / Market Regime / validation logic on shortlisted candidates rather than brute-forcing every strategy over every instrument continuously.
5. **Portfolio Gate** — apply aggregate exposure, concentration/correlation and capital-allocation controls across simultaneous opportunities.
6. **Execution Orchestration** — route only fully authorized opportunities to replaceable venue/broker execution boundaries.

### Activation gates

- Do not activate broad scanning while the one-symbol transport/runtime path is operationally unstable.
- First prove repeated supervised single-symbol forward runs, then multi-hour/overnight continuity and monitoring.
- Expand next to controlled multi-symbol live-paper data and scanner correctness before broad market-universe coverage.
- Keep real multi-market execution disabled until portfolio-level risk and venue/session handling are validated.

**Long-term operating principle:** the Agent may run 24/7 even though individual markets do not. It should continuously know which configured markets are open/relevant, scan the appropriate universe, rank opportunities, and trade only when the full strategy + risk + portfolio policy authorizes action.
