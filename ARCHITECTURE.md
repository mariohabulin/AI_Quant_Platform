# ARCHITECTURE

## Purpose

The AI Alpha Engine is a modular quantitative research and decision-making system designed to power a fully autonomous AI Alpha Trading Agent.

The objective of this project is not simply to build a backtesting framework or a collection of trading strategies.

The objective is to build an intelligent system capable of:

- researching financial markets
- discovering statistically sustainable trading edges
- validating strategies objectively
- managing risk
- selecting appropriate strategies
- continuously improving through quantitative research

The AI Alpha Trading Agent will combine the AI Alpha Engine with live market connectivity, trade execution and operational infrastructure required for autonomous 24/7 trading.

```text
AI Alpha Trading Agent
│
├── Live Market Data
├── AI Alpha Engine
│   ├── Research Engine
│   ├── Strategy Optimizer
│   ├── Market Intelligence
│   ├── Alpha Decision Engine
│   ├── Risk Engine
│   ├── Portfolio Engine
│   └── AI Learning Engine
│
├── Execution Engine
├── Broker Integration
├── Live Monitoring
└── Safety Controls
```

The AI Alpha Engine is the quantitative intelligence core of the AI Alpha Trading Agent.

---

# 1. Architectural Philosophy

The architecture is built from independent modules.

Each module owns one clearly defined responsibility.

Modules communicate only through documented public interfaces.

Long-term maintainability, scalability and deterministic behaviour always have priority over short-term implementation speed.

Every architectural decision should move the project closer to a trustworthy autonomous trading system.

---

# 2. Core Design Principles

## Single Responsibility Principle

Each module owns exactly one responsibility.

Examples:

- Feature Engine generates features.
- Strategy Library stores strategies.
- Strategy Engine orchestrates strategy execution.
- Trading Strategies generate trading signals.
- Backtesting Engine simulates trading.
- Performance Analyzer evaluates results.

Responsibilities must never overlap.

---

## Fail Fast

Every public interface validates its inputs before performing calculations.

Invalid input must immediately produce predictable exceptions.

---

## Parameterize Before Optimize

Every configurable component must expose explicit parameters before optimization begins.

No optimizer should depend on hardcoded values.

---

## Composition Over Duplication

Reusable behaviour should be extracted into dedicated modules or functions.

Business logic should never be duplicated unnecessarily.

---

## Backward Compatibility

Existing validated behaviour should continue working unless intentionally changed.

---

## Architecture Before Features

Architecture always has priority over implementation convenience.

Temporary shortcuts that reduce future extensibility should be avoided.

---

# 3. High-Level Architecture

Current Research Engine modules:

- Feature Engine
- Strategy Library
- Strategy Engine
- Backtesting Engine
- Performance Analyzer

Future AI Alpha Engine modules:

- Strategy Optimizer
- Walk Forward Analysis
- Market Intelligence
- Risk Engine
- Portfolio Engine
- Alpha Decision Engine
- AI Learning Engine

The AI Alpha Trading Agent is the final autonomous system built around these modules.

No module should bypass another module without explicit architectural justification.

---

# 4. Module Responsibilities

## Feature Engine

Responsible for:

- validating market data
- generating requested market features

---

## Strategy Library

Responsible for:

- registering strategies
- validating strategy registration
- retrieving strategies by name
- preventing duplicate registration

---

## Strategy Engine

Responsible for:

- retrieving the selected strategy
- requesting required features
- executing the selected strategy
- validating strategy output

---

## Trading Strategies

Responsible for:

- exposing configurable parameters
- declaring required features
- generating trading signals

---

## Backtesting Engine

Responsible for:

- deterministic historical trade simulation
- simulated portfolio state management
- explicit execution-price modelling
- commission, slippage and spread modelling
- gross and net trade P&L accounting
- trade history generation
- equity curve generation

The Backtesting Engine manages portfolio state and historical execution assumptions only during simulation.

## Benchmark Engine

The Benchmark Engine provides passive reference performance for objective strategy validation.

It must remain independent from trading-strategy signal generation and must use the same historical execution-cost assumptions when comparing a strategy against buy-and-hold.

Its first responsibility is to expose benchmark return and excess return without introducing optimization logic.

Execution-cost assumptions must be explicit, validated and reproducible. Zero-cost defaults preserve backward compatibility for existing research tests.

Future portfolio allocation decisions belong to the Portfolio Engine. Live order execution belongs to the future Execution Engine.

---

## Out-of-Sample Validation

The Out-of-Sample Validation layer owns chronological research-data separation and independent validation on unseen data.

It must:

- preserve temporal ordering
- forbid random shuffling of time-series observations
- keep in-sample and out-of-sample partitions non-overlapping
- evaluate both partitions from the same initial-capital and execution-cost assumptions
- compare each partition against the same passive benchmark
- expose generalization results without introducing parameter optimization

Out-of-sample evaluation starts from fresh capital and is independent from in-sample profits. This prevents capital carry-over from disguising generalization failure.

Walk-forward orchestration, statistical falsification and parameter optimization remain separate future responsibilities.

---

## Performance Analyzer

Responsible for:

- objective performance evaluation
- trading statistics
- strategy comparison

---

# 5. Research Execution Pipeline

```text
Market Data
      │
      ▼
Strategy Library
      │
      ▼
Strategy Engine
      │
      ├── reads required_features
      ├── requests Feature Engine
      └── executes Trading Strategy
      │
      ▼
Trading Signals
      │
      ▼
Backtesting Engine
      │
      ▼
Performance Analyzer
      │
      ▼
Research Result
```

Every future component should integrate into this pipeline instead of creating alternative execution paths.

---

# 6. Development Workflow

Every implementation follows the same workflow:

Architecture Review

↓

Design

↓

RED

↓

GREEN

↓

REFACTOR

↓

Full Test Suite

↓

Code Review

↓

Documentation

↓

Git Commit

↓

Git Push

Development never skips validation.

---

# 7. Testing Philosophy

The project follows strict Test Driven Development.

Every feature begins with a failing automated test.

Implementation should be the minimum required to satisfy the test.

Refactoring begins only after all automated tests pass.

Every completed implementation is validated by the complete automated test suite.

---

# 8. Permanent Architectural Decisions

## Stateless Backtesting

Every execution begins from a clean portfolio state.

---

## Explicit Strategy Parameters

Strategies expose configurable parameters through their public interface.

---

## Strategy Contract

Every strategy exposes:

- `name`
- `required_features`
- `generate_signals()`

The Strategy Engine communicates exclusively through this contract.

---

## Strategy Independence

Strategies must never:

- depend on another strategy
- modify another strategy
- assume another strategy exists

Strategies communicate only through the Research Engine execution pipeline.

---

## Feature Requirement Contract

Strategies request features through structured feature requirements.

Example:

```python
[
    {
        "name": "RSI",
        "parameters": {
            "period": 14,
        },
    },
]
```

Every feature request must contain:

- `name`
- `parameters`

The Feature Engine validates every request before generation.

---

## Signal Contract

Every strategy must return a `Signal` column.

Allowed values:

- `1` → BUY
- `0` → HOLD
- `-1` → SELL

Signal generation belongs exclusively to trading strategies.

Signal execution belongs to the Backtesting Engine or future Execution Engine.

---

## Deterministic Research

Given identical input data and identical parameters, every module must produce identical output.

Randomness may only be introduced explicitly and must always remain controllable.

---

## Single Execution Pipeline

Every strategy executes through the same Research Engine pipeline.

Future optimizers, AI modules and live trading components must reuse the existing execution pipeline whenever possible.

---

## Objective Evaluation

Performance evaluation always occurs after completed backtesting.

Trading logic and performance analysis remain independent.

---

# 9. Future Extension Principles

Future modules should extend the architecture rather than replace it.

Whenever possible they should:

- reuse existing public interfaces
- minimise coupling
- maximise independence
- preserve backward compatibility
- avoid duplicate business logic

Every new module should simplify the system rather than increase complexity.

---

# 10. Architecture Review Checklist

Before implementing any new module verify:

- Is it consistent with VISION.md?
- Is it aligned with ROADMAP.md?
- Does it satisfy CURRENT_MISSION.md?
- Does it follow this architecture?
- Does it preserve module responsibilities?
- Does it introduce unnecessary coupling?
- Can future modules reuse it?
- Does it move the AI Alpha Engine closer to autonomous trading?
- Will existing automated tests remain valid?

---

# Living Document

ARCHITECTURE.md is a living document.

Permanent architectural principles belong here.

Development history belongs in LOG.md.

Current objectives belong in CURRENT_MISSION.md.

Long-term goals belong in VISION.md.

Project evolution belongs in ROADMAP.md.

Whenever a permanent architectural decision is made, this document should be updated before further development continues.

---

# Research and Production Principle

> **Autonomy in analysis. Discipline in production.**

The Research Engine may explore, compare, learn and propose improvements.

Production behaviour must remain deterministic, validated and bounded by explicit risk and safety controls. No learned change may bypass backtesting, paper trading and production approval.

---

# Supertrend Feature Contract

Supertrend is generated by the Feature Engine as a deterministic ATR-based trend feature.

It exposes:

- the active Supertrend line
- the current trend direction (`1`, `0`, or `-1`)

The strategy reacts only to confirmed direction changes. Feature calculation remains separate from signal generation, preserving Single Responsibility and preventing strategy-specific calculations from leaking into the execution pipeline.


---

# ADX Feature Contract

ADX is generated by the Feature Engine as deterministic trend-strength data using Wilder smoothing. It exposes `ADX`, `+DI`, and `-DI`. The strategy converts only newly confirmed strong directional conditions into signals, preserving separation between feature calculation and trading decisions.


---

# Research Engine Expansion v8 — Final Strategy Expansion

## Objective

Add a Stochastic momentum-reversal strategy and formally close the planned Research Strategy Expansion.

Completed:

- configurable Stochastic %K and %D feature generation
- strict period and threshold validation
- BUY signals for bullish crossovers from the oversold zone
- SELL signals for bearish crossovers from the overbought zone
- dynamic Feature Engine integration
- unit and end-to-end pipeline tests
- Strategy Library Version 1 closure

Architecture Impact

The Research Engine now supports nine independent strategies through the same execution pipeline without strategy-specific architectural changes.

Testing

243 / 243 tracked-project automated tests passing.


---

# Phase 3 Walk-Forward Validation Contract

Walk-forward validation is a separate research layer that composes existing backtesting, benchmark and performance components without changing strategy logic.

It must:

- preserve strict chronological ordering
- prevent train/test overlap within each window
- support deterministic expanding and rolling windows
- start every partition from fresh capital
- apply identical execution-cost assumptions in every window
- compare every evaluated partition against the same buy-and-hold baseline
- summarize repeated out-of-sample persistence rather than relying on one historical split

No parameter optimization is performed by this layer. Optimizer integration remains a later, separately validated responsibility.

---

# Phase 3 Statistical Falsification Contract

Statistical falsification is a separate research layer that consumes completed net trade P&L without changing strategy, execution or signal logic.

It provides:

- bootstrap confidence intervals for expectancy
- Monte Carlo trade-order stress testing for path-dependent drawdown
- permutation/sign-flip testing against a zero-edge null hypothesis
- explicit random seeds for reproducible experiments
- a conservative pass flag that requires both bootstrap and permutation evidence

A falsification pass is research evidence, not production approval. Market coverage, walk-forward persistence, risk controls and paper trading remain separate gates.

---

# Phase 3 Strategy Validation Pipeline Contract

The Strategy Validation Pipeline is an orchestration layer. It composes existing OOS, walk-forward and statistical-falsification components without changing strategy signals, execution assumptions or feature generation.

Validation Policy v1 uses explicit, inspectable gates:

- unseen OOS strategy return must be positive
- unseen OOS excess return versus buy-and-hold must be positive
- bootstrap/permutation statistical falsification must pass
- at least 60% of walk-forward test windows must have positive excess return for `VALIDATED`

If any of the first three hard gates fails, status is `REJECTED`. If all hard gates pass but walk-forward persistence is below the configured threshold, status is `CONDITIONAL`. If all gates pass, status is `VALIDATED`.

Monte Carlo drawdown remains diagnostic evidence rather than a classification gate until the Risk Engine defines normalized portfolio drawdown tolerances. Statistical falsification consumes only repeated unseen walk-forward test trades so in-sample trades cannot strengthen the evidence.

---

# Phase 3 Multi-Asset Validation Contract

Multi-asset validation is a portfolio-of-evidence research layer. It runs one frozen strategy through the existing Strategy Validation Pipeline independently on multiple named assets.

It must:

- preserve identical strategy logic and validation configuration across assets
- keep each asset's OOS, walk-forward and falsification evidence inspectable
- aggregate cross-asset coverage without pooling trades across unrelated markets
- report mean unseen return, mean unseen excess return and positive-excess coverage
- use an explicit configurable cross-asset classification policy
- remain deterministic for a fixed random seed

Default policy: at least two assets are required; `VALIDATED` requires at least 60% of assets individually validated and no more than 20% rejected; more than 50% rejected produces `REJECTED`; other mixed evidence is `CONDITIONAL`.

---

# Phase 3 Market Regime Detection Contract

Market-regime analysis is a causal research layer. It describes market state without changing strategy signals, parameters, execution assumptions or validation policy.

Regime Detection v1 uses two independent dimensions:

- trend: `BULLISH`, `BEARISH`, `SIDEWAYS`
- volatility: `LOW`, `NORMAL`, `HIGH`

Trend is derived from ATR-normalized fast/slow EMA separation. Volatility is derived from normalized ATR relative to its trailing median baseline. All calculations are causal: a label at time t may use only information available at or before t. Warm-up observations are explicitly `UNKNOWN` rather than backfilled from the future.

Regime-conditioned analysis attributes unseen OOS trades by the regime present at trade entry and reports trade count, net P&L, average P&L and win rate per observed regime. Regime evidence is diagnostic in v1; it does not yet select strategies or alter `VALIDATED / CONDITIONAL / REJECTED` classifications.

---

# Phase 3 Risk Engine v1 — Position Sizing Foundation Contract

Risk sizing is a separate decision layer between a strategy signal and execution. Strategy logic decides *when* to trade; the Risk Engine decides *how much* may be traded; the Backtesting Engine remains responsible for execution simulation.

Risk Engine v1 must:

- derive a monetary risk budget from current equity and configurable risk-per-trade
- size long positions from entry-to-stop distance
- cap position notional with a configurable maximum position fraction
- return explicit `ALLOW`, `REDUCE`, or `REJECT` decisions
- fail fast on invalid configuration and malformed numeric inputs
- reject invalid long stops at or above entry
- preserve the original all-in backtester when no Risk Engine is supplied
- keep execution costs and affordability constraints inside the Backtesting Engine

Portfolio exposure, drawdown guards, daily/weekly loss limits, kill switches and portfolio correlation remain later Risk Engine milestones.

# Phase 3 Risk Engine v2 — Account Protection Layer Contract

Risk Engine v2 extends sizing with stateful account-protection guards while preserving strategy/execution separation. The Backtesting Engine reports current mark-to-market equity before considering a new entry; the Risk Engine may ALLOW or REJECT new risk.

Protection controls:

- maximum peak-to-current equity drawdown, implemented as a latched kill switch
- daily loss limit measured from the first observed equity of each calendar day
- weekly loss limit measured from the first observed equity of each ISO week
- deterministic reset of protection state at the start of every independent backtest run
- explicit protection evidence (`drawdown`, `daily_loss`, `weekly_loss`, `kill_switch_active`)

Protection guards block **new entries**. They do not create trading signals, modify strategy exits, or force-liquidate an already open position. Forced liquidation, portfolio-wide multi-position exposure/correlation controls and live-broker authorization remain later execution/risk milestones.

When all protection limits are disabled, Risk Engine v1 behavior is preserved and non-datetime backtests remain backward compatible.

# Phase 3 Risk Engine v3 — Trade Risk Policy Contract

Risk Engine v3 completes the pre-paper-trading risk scope with an explicit pre-trade policy. Strategy logic still decides when a trade is desired; Risk Engine validates whether the proposed long trade has a structurally valid stop/target and sufficient configured reward relative to risk.

Trade Risk Policy v1:

- long stop must be strictly below entry
- optional long target must be strictly above entry
- configurable `min_reward_risk`; disabled by default for backward compatibility
- when `min_reward_risk` is enabled, a target is mandatory
- reward/risk is computed from planned market prices as `(target - entry) / (entry - stop)`
- trades below the configured threshold are `REJECT` decisions before execution
- approved trade history records planned stop, target and reward/risk evidence
- execution costs remain the Backtesting Engine's responsibility and are not silently folded into the strategy's planned R:R

Risk Engine v1-v3 is the minimum risk-control scope required before paper trading. More advanced portfolio and live-emergency controls are deliberately deferred rather than forgotten; see the ROADMAP deferred backlog.

---

# Paper Trading — Paper Broker v1 Contract

Paper Broker is the deterministic execution boundary for paper trading. It receives already-authorized orders and owns order lifecycle, simulated fills and account state. It must not generate strategy signals, alter strategy parameters or repeat Risk Engine authorization.

Paper Broker v1 responsibilities:

- long-only market-order submission
- deterministic sequential order IDs
- explicit `SUBMITTED`, `FILLED`, `REJECTED` and `CANCELLED` lifecycle states
- side-aware commission, slippage and spread execution modelling
- cash and long-position quantity management
- weighted average entry-price tracking
- open-position cost-basis tracking
- realized P&L accounting
- mark-to-market account equity snapshots
- fail-fast validation for malformed orders and market prices
- rejection of unaffordable BUY orders and SELL quantities larger than the held position

The intended paper-trading boundary is:

```text
Market Event
    ↓
Strategy Engine
    ↓
Signal / Trade Intent
    ↓
Risk Engine
    ↓
Authorized Order
    ↓
Paper Broker
    ↓
Order Lifecycle + Fill + Account State
```

Backtesting Engine remains responsible for deterministic historical simulation. Paper Broker remains responsible for forward paper execution. Neither module should absorb the other's orchestration responsibilities.

---

## Paper Trading Engine v1 — Orchestration Boundary

Paper trading now has an explicit orchestration layer:

```text
Market data available so far
        ↓
Strategy Engine
        ↓
Signal
        ↓
Risk Engine (protection + pre-trade authorization)
        ↓
Paper Broker (order + fill + account state)
        ↓
Paper Trading audit event
```

`PaperTradingEngine` contains no strategy-selection or sizing intelligence of its own. It coordinates existing boundaries, prevents duplicate long entries in the current long-only model, closes the current long position on a SELL signal, and records deterministic evidence for every processed event. External streaming connectivity remains outside this boundary so deterministic orchestration can be proven before network/API complexity is introduced.

## Paper Trading v2 — Session & State Foundation

A deterministic session boundary now coordinates ordered market events across time while preserving PaperTradingEngine, RiskEngine and PaperBroker state. Session snapshots record mark-to-market equity, cash, position, realized P&L and the associated orchestration outcome. Timestamps must be strictly increasing, preventing accidental replay/out-of-order processing in the deterministic forward loop.

The session deliberately remains in-memory. Durable persistence, restart recovery, external streaming feeds and watchdog/monitoring remain deferred in ROADMAP until the deterministic continuous lifecycle is validated.

## Market Data Boundary v1 — Historical Replay Contract

Paper trading now receives market data through a provider-neutral event contract. `MarketDataEvent` carries an ordered timestamp and a cumulative OHLCV view containing only information available up to that event. `HistoricalReplayFeed` is the first adapter: it validates historical bars and emits them deterministically one at a time, allowing the same PaperTradingSession boundary to be exercised as a forward-time process without network/API complexity.

```text
Historical OHLCV
      ↓
HistoricalReplayFeed
      ↓
Normalized MarketDataEvent (data available so far only)
      ↓
PaperTradingSession
      ↓
Strategy → Risk → Paper Broker
```

The feed owns data normalization, chronological ordering and OHLCV integrity checks. It does not generate signals, stops/targets, risk decisions or orders. Real streaming providers must later adapt into this same internal event contract rather than leaking provider-specific payloads into Strategy, Risk or Paper Trading layers.

## Replay / Backtest Consistency Boundary

`ReplayConsistencyValidator` is a diagnostic validation layer between the historical `BacktestingEngine` and the event-driven `PaperTradingSession`. It replays the same OHLCV history through the normalized `HistoricalReplayFeed` and compares evidence rather than assuming the two execution paths are equivalent.

V1 compares signal sequence, completed round trips, quantity, entry/exit fill prices, commission, realized trade P&L, final equity and final open-position state. A difference produces a structured `DIVERGENT` report; it is not hidden or automatically normalized away. This explicitly exposes known semantic differences such as the backtester's end-of-run forced close versus a paper session that keeps an open position alive.

The validator remains outside Strategy, Risk and Broker responsibilities. Its job is diagnosis only; it must not modify either execution path to manufacture agreement.

## Paper Readiness Gate v1 — Evidence Contract

`PaperReadinessGate` sits above `ReplayConsistencyValidator`; it does not execute trades and does not change Backtesting or Paper Trading semantics. It converts a set of named representative consistency scenarios into an aggregate `READY / BLOCKED` decision.

Each scenario retains the complete `ReplayConsistencyReport` and is classified as `MATCH`, `INTENDED`, `DEFECT` or `CONFIGURATION_MISMATCH`. A divergent scenario may pass only when it is explicitly classified `INTENDED` and the observed difference fields exactly match the scenario's expected allow-list. Any new/unexpected difference blocks the gate. A stale allow-list also blocks the gate if a previously expected divergence disappears, forcing documentation/evidence to be updated rather than silently carrying obsolete exceptions.

This boundary is intentionally diagnostic/governance logic. It must never rewrite fills, signals, risk decisions or account state to manufacture consistency.

## Real-Time Market Data Adapter + Feed Health v1

External provider schemas terminate at a dedicated adapter boundary. The first controlled provider contract is Alpaca crypto minute bars for `BTC/USD`, selected because the same provider supports websocket market data for both crypto and equities while crypto avoids stock-session gaps during initial 24/7 feed-health testing. `AlpacaCryptoBarAdapter` normalizes provider bar messages into the existing OHLCV/`MarketDataEvent` contract; Strategy, Risk and Paper layers remain provider-agnostic.

`RealTimeMarketDataFeed` is a safety gate, not trading intelligence. It rejects stale, future-dated, duplicate, out-of-order and excessive-gap bars before they can become trading events, preserves accepted cumulative history and exposes explicit `WAITING / HEALTHY / UNHEALTHY` health state. Network transport, authentication, reconnect/backoff and runtime supervision remain outside the adapter so connection concerns do not leak into market-data normalization.

## Operational Runtime Boundary

Real-time paper operation is isolated behind `PaperOperationalRuntime`. Provider transport is replaceable; `AlpacaWebSocketTransport` owns Alpaca authentication/subscription and bounded reconnect/backoff, `RealTimeMarketDataFeed` owns data-health gating, and `PaperTradingSession` remains the only trading-session orchestrator.

Runtime failures are fail-closed: unhealthy feed events never reach the session, repeated feed-health failures halt processing, and unknown strategy/risk/execution exceptions halt rather than silently continuing. `JsonCheckpointStore` persists the minimum continuity state (broker account/open position, Risk Engine protection state, session/feed timestamp continuity and runtime counters) with atomic replace semantics.

The checkpoint is intentionally not a general database or event store. Durable long-horizon audit storage, distributed supervision and multi-provider failover remain later operational concerns.

## Pre-Flight Safety Gate v1

Before any controlled real-time paper session, `PaperPreFlightGate` validates the operational boundary without submitting orders. The gate verifies redacted credential presence, the controlled BTC/USD 1-minute scope, explicit conservative Risk Engine guards, clean/reconciled paper-account state, writable checkpoint storage, hard-disabled execution, provider connectivity/subscription through an injected probe, and a startable runtime state. Any failed check blocks readiness. Credential values are never emitted in the report.

Pre-flight is intentionally separate from trading execution: passing the gate is permission to proceed to a supervised dry-run/forward session, not permission for live-money execution.

## Coinbase Public Market Data Boundary v1

`CoinbasePublicWebSocketTransport -> CoinbaseOneMinuteTradeAggregator -> CoinbaseOneMinuteBarAdapter -> RealTimeMarketDataFeed -> MarketDataEvent`

The transport subscribes only to public `market_trades` and `heartbeats`; no account credentials are required for this first dry-run. The aggregator emits only completed 1-minute buckets, so partial current-minute candles never cross the trading boundary. Coinbase product symbology (`BTC-USD`) is translated at the provider boundary to the platform's internal symbol (`BTC/USD`). Existing Feed Health, Operational Runtime, Risk Engine and Paper Trading boundaries remain provider-neutral and unchanged.

### Coinbase dry-run boundary
`CoinbasePublicWebSocketTransport -> CoinbaseOneMinuteTradeAggregator -> CoinbaseOneMinuteBarAdapter -> RealTimeMarketDataFeed`. The dry-run runner intentionally has no PaperBroker/PaperTradingSession dependency; execution is structurally unavailable.

### Coinbase Live Paper Bridge
The bounded live-paper path is Coinbase public WebSocket -> 1m trade aggregator -> Coinbase bar adapter / Feed Health -> PaperOperationalRuntime -> accumulating PaperTradingSession -> Strategy Engine -> Risk Engine -> PaperBroker. No real broker execution adapter is reachable from this runner. Historical strategy context is accumulated only from health-accepted completed bars.

## Forward Paper Observation Boundary
`src/forward_paper_session.py` reuses the Coinbase live-paper composition and adds only bounded duration plus append-only JSONL audit evidence. It has no real broker/exchange execution adapter. Audit persistence is evidence/observability, not a substitute for runtime checkpoint recovery. Exact restart continuity remains deferred until strategy history and in-progress market-data aggregation can be restored deterministically.

## Forward Paper Continuity Boundary
Forward-paper restart state is broader than the generic operational checkpoint because the live composition owns state outside `PaperOperationalRuntime`. `ForwardContinuityStore` atomically persists the runtime checkpoint, `AccumulatingPaperSession` strategy input history, and the Coinbase aggregator's in-progress minute bucket. This prevents a restart from forgetting an open paper position or recomputing EMA decisions from an empty history. Mutable runtime state/audit files are operational artifacts, not source code; milestone evidence is stored separately under `docs/evidence/`.

## Restart Gap Reconciliation Boundary
A resumed forward-paper process may legitimately reconnect after a gap larger than normal feed tolerance. `RealTimeMarketDataFeed.reconcile_after_restart` permits only a fresh, strictly forward excessive gap to establish a new timestamp baseline. The boundary bar is never emitted as a `MarketDataEvent`, never enters strategy history, and therefore cannot create a trading decision. Normal gap enforcement resumes immediately on the next bar; stale, future, duplicate and out-of-order protections remain fail-closed.


## Extended Forward Session Reporting Boundary
`src/forward_session_report.py` is a read-only evidence layer over the append-only forward JSONL audit. It selects only the latest complete `SESSION_START` -> `SESSION_END` block and fails closed on malformed or incomplete boundaries. The reporter never touches transport, strategy, risk or broker execution. A report is PASS only when audit counts reconcile and all recorded real-order evidence remains zero. This keeps longer forward observation measurable without widening the trading boundary.

### Coinbase Late-Trade Ordering Robustness v2
Extended forward observation exposed event-time reordering across separate Coinbase websocket messages. Add a bounded 2-second event-time reorder buffer before strict minute aggregation, persist the pending buffer in forward continuity state, and keep truly late trades fail-closed after the watermark. This adds a small intentional bar-finalization delay to preserve OHLCV correctness rather than silently dropping late trades.

- Completed-bar freshness semantics: adapters may define `freshness_reference(timestamp, timeframe)`; Coinbase completed 1m bars are aged from interval close, while timestamp ordering remains anchored to interval start.
