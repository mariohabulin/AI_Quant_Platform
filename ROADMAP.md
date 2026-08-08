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
