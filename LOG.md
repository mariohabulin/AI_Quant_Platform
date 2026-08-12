# LOG

# Purpose

This document records the permanent development history of the AI Alpha Engine.

Unlike CURRENT_MISSION.md, this document never describes ongoing work.

Only completed milestones are recorded here.

Every entry documents:

- completed implementation
- architectural impact
- testing milestones
- important development decisions
- lessons learned

This document serves as the permanent historical record of the project.

---

# Phase 1 — Data Foundation

## Objective

Establish a reliable and maintainable foundation for future quantitative research.

---

## Documentation Foundation

Completed

- Created VISION.md
- Created ROADMAP.md
- Created ARCHITECTURE.md
- Created CURRENT_MISSION.md
- Established project development workflow

Architecture Impact

The project transitioned from a collection of Python modules into a structured software architecture driven by long-term vision.

---

## Data Visualization

Completed

- Data visualization module
- CSV validation
- Column validation
- Automatic chart titles
- Candlestick visualization
- EMA visualization
- Volume visualization
- BUY / SELL marker visualization

Architecture Impact

Visualization became completely independent from trading logic.

Trading signals became the exclusive responsibility of trading strategies.

---

## EMA Strategy

Completed

- EMA crossover implementation
- Strategy validation
- BUY / SELL signal generation
- End-to-end visualization validation

Architecture Impact

Established the first reusable trading strategy.

---

## Phase 1 Result

Successfully completed:

- Data Loader
- Data Visualization
- EMA Strategy
- Stable development workflow

Phase 1 officially completed.

---

# Phase 2 — Research Engine

## Feature Engine

Completed

- Feature Engine architecture
- EMA generation
- RSI generation
- Return calculation
- Volatility calculation
- Volume MA
- Input validation

Architecture Impact

Feature generation became completely centralized.

Strategies consume features instead of calculating indicators.

Testing

Fully validated.

---

## Strategy Engine

Completed

- Common strategy interface
- Strategy execution
- Validation
- Signal validation
- Pipeline validation

Architecture Impact

Execution became independent from strategy implementation.

Testing

Completed.

---

## Strategy Library

Completed

- Strategy registration
- Strategy lookup
- Validation
- Duplicate protection
- Integration with Strategy Engine

Architecture Impact

Strategy management became independent from strategy execution.

Testing

Completed.

---

## Backtesting Engine

Completed

- Portfolio management
- BUY execution
- SELL execution
- Sequential execution
- Trade History
- Equity Curve
- Automatic position closing
- Stateless execution

Architecture Impact

Established deterministic backtesting.

Testing

Completed.

---

## Performance Analyzer

Completed

- Total Return
- Number of Trades
- Win Rate
- Average Win
- Average Loss
- Profit Factor
- Max Drawdown
- Expectancy
- Sharpe Ratio

Architecture Impact

Performance evaluation became completely independent from trading logic.

Testing

Completed.

---

# Optimizer Readiness

## Objective

Prepare the complete execution pipeline for future optimization.

Completed

- Stateless Backtesting
- Parameterized EMA Strategy
- Dynamic EMA generation
- Required Features contract
- Strategy ↔ Feature integration
- Strategy validation improvements
- End-to-End pipeline validation

Architecture Impact

The execution pipeline became fully parameterized and optimizer-ready.

Testing

94 / 94 automated tests passing.

---

# Research Engine Expansion v1

## Objective

Validate that the Research Engine supports multiple independent trading strategies without architectural changes.

Completed

### RSI Feature

- Dynamic RSI generation
- Parameter validation
- Feature Engine integration

### RSI Strategy

- Configurable RSI period
- Configurable thresholds
- Strategy validation
- Signal generation
- Required Features integration

### Pipeline Validation

Validated complete execution of:

- Feature Engine
- Strategy Engine
- Backtesting Engine
- Performance Analyzer

without modifying the existing architecture.

Architecture Impact

The Research Engine successfully evolved from supporting a single strategy into a modular multi-strategy research platform.

Testing

112 / 112 automated tests passing.


---

# Research Engine Expansion v2

## Objective

Validate that the Research Engine continues to scale by integrating an additional independent trading strategy without modifying the existing execution pipeline.

Completed

### MACD Feature

- Dynamic MACD generation
- Configurable fast period
- Configurable slow period
- Configurable signal period
- Feature validation
- Feature Engine integration

### MACD Strategy

- Configurable MACD parameters
- BUY crossover signal generation
- SELL crossover signal generation
- Required Features integration
- Strategy validation
- Missing feature validation

### Pipeline Validation

Validated complete execution of:

- Feature Engine
- Strategy Engine
- Backtesting Engine
- Performance Analyzer

using the MACD Strategy without modifying the existing architecture.

Architecture Impact

The Research Engine successfully demonstrated that additional trading strategies can be integrated through the existing architecture without requiring changes to the execution pipeline.

The Feature Engine now supports multiple parameterized technical indicators while preserving a single reusable feature generation interface.

Testing

139 / 139 automated tests passing.


# Research Engine Expansion v3

## Objective

Continue validating that the Research Engine architecture scales by integrating another independent trading strategy through the existing execution pipeline.

Completed

### Bollinger Bands Feature

- Dynamic Bollinger Bands generation
- Configurable period
- Configurable standard deviations
- Feature validation
- Feature Engine integration

### Bollinger Bands Strategy

- Configurable Bollinger Bands parameters
- BUY breakout signal generation
- SELL breakout signal generation
- Required Features integration
- Strategy validation
- Missing feature validation

### Pipeline Validation

Validated complete execution of:

- Feature Engine
- Strategy Engine
- Backtesting Engine
- Performance Analyzer

using the Bollinger Bands Strategy without modifying the existing architecture.

Architecture Impact

The Research Engine successfully demonstrated that a fourth independent trading strategy integrates through the same reusable execution pipeline without architectural changes.

The Feature Engine now supports four independent parameterized technical indicators through a unified feature generation interface.

Testing

160 / 160 automated tests passing.


---

# Research Engine Expansion v4

## Objective

Continue validating that the Research Engine architecture scales by integrating an additional breakout trading strategy through the existing execution pipeline.

Completed

### Donchian Channels Feature

- Dynamic Donchian Channel generation
- Configurable period
- Feature validation
- Previous-candle channel calculation
- Feature Engine integration

### Donchian Breakout Strategy

- Configurable Donchian period
- BUY breakout signal generation
- SELL breakout signal generation
- Required Features integration
- Strategy validation
- Missing feature validation

### Pipeline Validation

Validated complete execution of:

- Feature Engine
- Strategy Engine
- Backtesting Engine
- Performance Analyzer

using the Donchian Breakout Strategy without modifying the existing architecture.

Architecture Impact

The Research Engine successfully demonstrated that a fifth independent trading strategy integrates through the same reusable execution pipeline without architectural changes.

The Feature Engine now supports five independent parameterized technical indicators through a unified feature generation interface.

Testing

178 / 178 automated tests passing.

---
---

# Major Architecture Milestones

Completed

✓ Modular Feature Engine

✓ Strategy Library

✓ Strategy Engine

✓ Stateless Backtesting

✓ Performance Analyzer

✓ Required Features Contract

✓ Dynamic Feature Generation

✓ Parameterized Strategies

✓ Strategy-independent Execution Pipeline

✓ Multi-strategy Architecture

✓ Deterministic Research

✓ MACD Feature Generation

✓ Three-strategy Research Engine Validation

✓ Bollinger Bands Feature Generation

✓ Four-strategy Research Engine Validation

✓ Donchian Channels Feature Generation

✓ Five-strategy Research Engine Validation

---

# Automated Testing Milestones

10 tests

15 tests

23 tests

25 tests

31 tests

51 tests

70 tests

71 tests

79 tests

84 tests

93 tests

94 tests

112 tests

139 tests

160 tests

178 tests

---

# Development Philosophy Confirmed

Throughout the project the following principles proved successful:

- Test Driven Development
- Small incremental implementation
- Fail Fast validation
- Single Responsibility Principle
- Parameterize Before Optimize
- Deterministic execution
- Continuous architectural validation

These principles remain the standard development methodology of the AI Alpha Engine.

---

# Research Engine Expansion v5

## Objective

Add a volatility-based strategy that is structurally distinct from the existing trend, momentum, mean-reversion and channel-breakout strategies.

Completed

### ATR Feature

- Average True Range generation
- Wilder smoothing
- Configurable period
- Strict parameter validation
- Dynamic Feature Engine integration

### ATR Volatility Breakout Strategy

- Configurable ATR period and breakout multiplier
- BUY and SELL volatility-breakout signals
- Previous-candle close and ATR usage
- Required Features integration
- Missing feature validation

### Pipeline Validation

Validated complete execution of:

- Feature Engine
- Strategy Engine
- Backtesting Engine
- Performance Analyzer

using the ATR Volatility Breakout Strategy without modifying the execution architecture.

Architecture Impact

The Research Engine now supports six independent trading strategies through the same reusable pipeline.

Testing

194 / 194 tracked-project automated tests passing.

Environment Note

The Git archive excludes the ignored `data/AAPL.csv` fixture. In the isolated archive environment, four pre-existing Strategy Engine tests therefore cannot run; all 190 runnable tests pass. The full local repository with its data fixture is expected to run all 194 tests.



---

# Research Engine Expansion v6

## Objective

Add an ATR-based trend-following strategy that identifies confirmed trend reversals while preserving the existing reusable Research Engine pipeline.

Completed

### Supertrend Feature

- ATR-based adaptive upper and lower bands
- Configurable ATR period and multiplier
- Deterministic Supertrend line generation
- Explicit trend direction feature
- Strict parameter validation
- Dynamic Feature Engine integration

### Supertrend Strategy

- Configurable period and multiplier
- BUY signal on bearish-to-bullish trend reversal
- SELL signal on bullish-to-bearish trend reversal
- HOLD while the current trend remains unchanged
- Required Features integration
- Missing feature validation

### Pipeline Validation

Validated complete execution of:

- Feature Engine
- Strategy Engine
- Backtesting Engine
- Performance Analyzer

using the Supertrend Strategy without modifying the execution architecture.

Architecture Impact

The Research Engine now supports seven independent trading strategies through the same reusable pipeline.

Testing

208 / 208 tracked-project automated tests passing.

Environment Note

The Git archive excludes the ignored `data/AAPL.csv` fixture. In the isolated archive environment, four pre-existing Strategy Engine tests therefore cannot run; all 204 runnable tests pass. The full local repository with its data fixture is expected to run all 208 tests.


---

# Research Engine Expansion v7

## Objective

Add trend-strength confirmation through ADX while preserving the reusable Research Engine pipeline.

Completed:

- Wilder-smoothed +DI, -DI and ADX feature generation
- configurable ADX period and strength threshold
- BUY signals for newly confirmed strong bullish trends
- SELL signals for newly confirmed strong bearish trends
- dynamic Feature Engine integration
- unit and end-to-end pipeline tests

Architecture Impact

The Research Engine now supports eight independent strategies through the same execution pipeline.

Testing

222 / 222 tracked-project automated tests passing.


---

# Research Engine Expansion v8 — Stochastic Strategy

## Status

Completed.

## Delivered

- Stochastic %K and %D feature generation
- configurable %K period, %D period, oversold and overbought thresholds
- bullish crossover BUY signals from the oversold zone
- bearish crossover SELL signals from the overbought zone
- dynamic Feature Engine integration
- isolated strategy tests and end-to-end research pipeline validation
- formal closure of Research Strategy Expansion
- Strategy Library Version 1 frozen with nine validated strategies

## Validation

243 / 243 tracked-project automated tests passing.

## Outcome

The planned Research Strategy Expansion is complete. Future strategy additions must be justified by backtesting or paper-trading evidence rather than indicator count.


---

# Phase 3 — Realistic Execution Layer

## Objective

Upgrade the Backtesting Engine from frictionless historical execution to explicit, deterministic execution-cost modelling without changing the Research Engine pipeline.

## Delivered

- configurable commission rate
- configurable slippage rate
- configurable bid/ask spread rate
- side-aware BUY and SELL execution prices
- all-in sizing that reserves entry commission and never drives cash negative
- explicit entry and exit market prices
- explicit entry and exit execution prices
- gross P&L, commission, execution cost, total cost and net P&L in trade history
- fail-fast validation for invalid execution-cost assumptions
- zero-cost backward compatibility with legacy backtest behaviour

## Architecture Impact

The existing Strategy Engine → Backtesting Engine → Performance Analyzer pipeline is preserved. The Backtesting Engine now owns historical execution friction while future live execution remains the responsibility of the Execution Engine.

## Validation

All 67 Backtesting Engine and Performance Analyzer tests pass in the isolated snapshot environment.

The full isolated snapshot reports 251 passing tests and four pre-existing Strategy Engine fixture failures because the Git archive excludes the ignored `data/AAPL.csv` file. The complete local repository is expected to run 255 / 255 tracked-project tests.


---

# Phase 3 — Benchmark Engine

## Objective

Add an objective passive baseline so strategy performance is evaluated relative to a simple alternative rather than absolute return alone.

## Delivered

- deterministic buy-and-hold benchmark
- the same commission, slippage and spread assumptions used by historical execution
- explicit benchmark gross P&L, execution costs, commissions and net P&L
- strategy return, benchmark return and excess-return comparison
- fail-fast validation for benchmark inputs and execution assumptions
- isolated unit coverage for profitable, flat, cost-adjusted and underperforming cases

## Architecture Impact

Benchmark evaluation is kept separate from Strategy Engine signal generation and Backtesting Engine portfolio simulation. This preserves single responsibility while giving Phase 3 validation an objective baseline.

## Validation

77 / 77 Benchmark Engine, Backtesting Engine and Performance Analyzer tests pass in the isolated snapshot environment.


---

# Phase 3 — Out-of-Sample Validation

## Objective

Introduce chronological in-sample / out-of-sample validation so strategy performance must generalize to unseen data rather than relying on development-period results.

## Delivered

- deterministic chronological data splitting
- configurable in-sample fraction
- explicit rejection of non-chronological indexes
- non-overlapping in-sample and out-of-sample partitions
- independent fresh-capital backtests for IS and OOS
- identical commission, slippage and spread assumptions across both partitions
- buy-and-hold benchmark comparison on both partitions
- generalization summary for strategy return and excess return
- fail-fast validation for invalid split and execution assumptions
- isolated unit coverage for chronology, leakage prevention, costs and benchmark integration

## Architecture Impact

Out-of-sample validation is implemented as a separate validation layer that composes the existing Backtesting Engine, Benchmark Engine and Performance Analyzer. It does not modify strategy logic or introduce optimization.

## Validation

88 / 88 OOS, Benchmark, Backtesting and Performance Analyzer tests pass in the isolated snapshot environment.

The full isolated snapshot reports 272 passing tests and four pre-existing Strategy Engine fixture failures because the Git archive excludes the ignored `data/AAPL.csv` file. The complete local repository is expected to run 276 / 276 tracked-project tests.


---

# Phase 3 — Walk-Forward Validation

## Objective

Extend chronological validation from one IS/OOS split to repeated train/test windows so strategy generalization can be evaluated through time.

## Delivered

- deterministic expanding walk-forward windows
- optional fixed-length rolling windows
- configurable train, test and step sizes
- strict chronology and duplicate-index rejection
- non-overlapping train/test partitions within every window
- independent fresh-capital strategy evaluation for every partition
- identical commission, slippage and spread assumptions across windows
- buy-and-hold benchmark comparison in every window
- summary of mean OOS strategy/excess return and positive-window persistence
- no optimizer coupling or parameter fitting

## Architecture Impact

Walk-forward validation is implemented as a separate validation layer that composes the existing Out-of-Sample, Backtesting, Benchmark and Performance components. Strategy logic remains frozen and unchanged.

## Validation

The milestone adds dedicated unit coverage for chronology, expanding/rolling behavior, leakage prevention, execution costs, benchmark integration and repeated OOS summaries.

---

## Phase 3 — Statistical Falsification Layer

Added a reproducible statistical robustness layer for completed trade histories.

Implemented:

- bootstrap expectancy confidence intervals
- Monte Carlo trade-order drawdown stress testing
- permutation/sign-flip zero-edge testing
- deterministic random-seed support
- conservative combined falsification result
- fail-fast trade-history validation

This layer intentionally does not optimize strategy parameters or alter trading logic.

---

## Phase 3 — Strategy Validation Pipeline v1

Added an orchestration layer that turns the completed Phase 3 validation components into one deterministic research result.

Implemented:

- unified OOS, walk-forward and statistical-falsification execution
- statistical falsification based only on repeated unseen walk-forward test trades
- explicit Validation Policy v1
- `VALIDATED`, `CONDITIONAL` and `REJECTED` classifications
- configurable walk-forward persistence threshold
- transparent per-gate classification output
- Monte Carlo drawdown retained as diagnostic evidence pending Risk Engine tolerances
- isolated tests for policy boundaries, orchestration, reproducibility and execution-cost propagation

---

## Phase 3 — Multi-Asset Validation

Added a cross-market validation layer that reuses the complete Strategy Validation Pipeline independently for each asset.

Implemented:

- deterministic named-asset validation
- isolated per-asset OOS, walk-forward and falsification evidence
- cross-asset return/excess-return/persistence summaries
- explicit Multi-Asset Policy v1
- `VALIDATED`, `CONDITIONAL` and `REJECTED` aggregate classification
- configurable breadth and rejection thresholds
- input immutability and execution-cost propagation tests

The layer intentionally does not pool trades across assets or introduce portfolio weighting. Correlation, allocation and portfolio risk remain responsibilities of the future Risk Engine.

## Phase 3 — Market Regime Detection v1

- Added causal two-dimensional market regime detection.
- Trend states: BULLISH / BEARISH / SIDEWAYS using ATR-normalized EMA separation.
- Volatility states: LOW / NORMAL / HIGH using normalized ATR versus trailing median baseline.
- Added explicit UNKNOWN warm-up state; no future backfilling.
- Added regime-conditioned unseen OOS trade attribution by entry regime.
- Added per-regime trade count, net P&L, average P&L and win rate.
- Kept regime evidence diagnostic: no strategy selection or validation-policy mutation.
- Added dedicated Market Regime test coverage.

## Phase 3 — Risk Engine v1: Position Sizing Foundation

- Added deterministic risk-per-trade position sizing from equity and stop distance.
- Added configurable maximum position exposure cap.
- Added explicit ALLOW / REDUCE / REJECT risk decisions.
- Integrated optional risk-managed sizing into Backtesting Engine.
- Preserved legacy all-in behavior when no Risk Engine is configured.
- Added risk decision evidence to completed trade history.
- Kept execution affordability and trading costs inside Backtesting Engine.
- Added dedicated Risk Engine and integration test coverage.

## Phase 3 — Risk Engine v2: Account Protection Layer

- Added causal peak-equity drawdown tracking.
- Added configurable maximum-drawdown kill switch that latches for the current backtest run.
- Added configurable daily loss guard with calendar-day reset.
- Added configurable weekly loss guard with ISO-week reset.
- Added explicit protection decisions and diagnostic loss/drawdown evidence.
- Integrated protection authorization before new Backtesting Engine entries.
- Reset Risk Engine protection state between independent backtest runs.
- Preserved Risk Engine v1 position sizing and legacy behavior when guards are disabled.
- Kept forced liquidation and portfolio-wide correlation/exposure outside this milestone.

## Phase 3 — Risk Engine v3: Trade Risk Policy

- Added configurable minimum reward/risk policy; disabled by default for backward compatibility.
- Kept 1:3 available as configuration rather than hardcoded trading truth.
- Added explicit long target validation and mandatory target when minimum R:R is enabled.
- Added pre-trade rejection for structurally invalid or insufficient-R:R proposals.
- Added planned stop, target and reward/risk evidence to completed risk-managed trades.
- Preserved v1 position sizing, v2 account-protection guards and legacy no-risk-engine behavior.
- Kept execution costs and actual fill simulation inside Backtesting Engine.
- Documented advanced portfolio/risk capabilities as deferred work rather than expanding the pre-paper-trading scope.

---

# Paper Trading — Paper Broker v1

## Objective

Create the first deterministic paper-execution boundary without coupling live connectivity, strategy logic or risk authorization into broker state management.

## Delivered

- standalone Paper Broker module
- long-only market BUY/SELL order lifecycle
- deterministic sequential order IDs
- explicit `SUBMITTED / FILLED / REJECTED / CANCELLED` statuses
- commission, slippage and spread execution modelling
- cash, position quantity, weighted average entry price and open cost-basis accounting
- realized P&L and mark-to-market equity snapshots
- insufficient-cash and insufficient-position rejection paths
- deterministic cancel-before-fill behaviour
- auditable in-memory order history
- fail-fast validation for malformed order and market-price inputs
- dedicated Paper Broker unit tests

## Architecture Impact

Paper Broker is intentionally separate from Backtesting Engine, Strategy Engine and Risk Engine. It executes already-authorized orders and owns only order lifecycle, fills and paper account state. This keeps the future transition from `PaperBroker` to a live broker adapter isolated from trading intelligence.

## Deferred Work

Real streaming market data, Paper Trading Engine orchestration, persistence/restart recovery, richer order types, partial fills, latency/microstructure modelling and live broker integration are deliberately deferred. Each item is tracked in ROADMAP.md together with the reason for deferral so future scope is explicit rather than forgotten.

---

## Paper Trading Engine v1 — Orchestration Foundation

Added a deterministic `PaperTradingEngine` that connects Strategy Engine, Risk Engine and Paper Broker without duplicating their responsibilities. Each market event uses only the data explicitly supplied to the engine, the latest strategy signal is risk-authorized before a BUY order reaches the broker, SELL closes the current long position, and HOLD/rejected/no-position outcomes remain auditable without creating phantom orders. Added deterministic event history for forward-test diagnostics. Real streaming data, persistence/restart recovery and unattended monitoring remain deferred per ROADMAP until this in-memory orchestration boundary is validated.

## Paper Trading v2 — Session & State Foundation

A deterministic session boundary now coordinates ordered market events across time while preserving PaperTradingEngine, RiskEngine and PaperBroker state. Session snapshots record mark-to-market equity, cash, position, realized P&L and the associated orchestration outcome. Timestamps must be strictly increasing, preventing accidental replay/out-of-order processing in the deterministic forward loop.

The session deliberately remains in-memory. Durable persistence, restart recovery, external streaming feeds and watchdog/monitoring remain deferred in ROADMAP until the deterministic continuous lifecycle is validated.

## Market Data Boundary + Historical Replay Feed v1

- Added provider-neutral `MarketDataEvent` contract.
- Added deterministic `HistoricalReplayFeed` with strict OHLCV, timestamp and price-geometry validation.
- Replay emits cumulative data available only up to each event, preventing future-bar leakage by construction.
- Proved replay events can drive the existing stateful PaperTradingSession without changing Strategy, Risk or Paper Broker boundaries.
- External streaming/API connectivity remains deferred until deterministic replay and consistency evidence are green.

## Backtest ↔ Paper Replay Consistency Validator v1

Added a diagnostic bridge between `BacktestingEngine` and event-driven `PaperTradingSession`. The validator runs the same historical OHLCV evidence through both paths and compares signals, round trips, sizing, fills, commission, P&L, final equity and open-position state. Differences are returned as structured diagnostics rather than being normalized away. This deliberately makes end-of-backtest forced liquidation visible when paper replay would keep the position open.

## Paper Readiness Gate v1 — Representative Replay Consistency + Roadmap Reconciliation

- Added an explicit readiness gate above `ReplayConsistencyValidator`.
- Added named representative scenarios and structured aggregate readiness evidence.
- Added `MATCH / INTENDED / DEFECT / CONFIGURATION_MISMATCH` classifications.
- Only exact allow-listed `INTENDED` semantic differences can pass; unexpected fields, stale allow-lists, defects and configuration mismatches block readiness.
- Preserved consistency diagnostics as evidence rather than silently modifying Backtesting or Paper Trading semantics.
- Reconciled ROADMAP with actual completed Research/Validation, Risk Engine and Paper Trading work.
- Promoted minimal checkpoint/restart recovery into the required operational-runtime milestone before unattended paper sessions.
- Kept provider expansion, optimizer/AI learning, advanced portfolio risk and microstructure complexity deferred with explicit reasons.

## Real-Time Market Data Adapter + Feed Health v1

- Selected Alpaca crypto websocket bar schema as the first provider contract, initially scoped to `BTC/USD` 1-minute bars.
- Added provider-specific normalization without leaking Alpaca fields into the existing `MarketDataEvent` boundary.
- Added feed-health rejection for stale, future-dated, duplicate, out-of-order and excessive-gap bars.
- Added explicit feed health state and mutation-safe accepted history.
- Kept network transport/authentication/reconnect outside the adapter; those belong to the Operational Safety / Paper Runtime milestone.
- Kept provider/asset expansion deferred until one controlled real-time path is stable.

## Operational Safety / Paper Runtime v1

Implemented the final MUST-HAVE operational boundary before the first controlled real-time paper run: health-aware runtime loop, fail-closed exception isolation, graceful shutdown, heartbeat state, atomic JSON checkpoint/restart recovery, and injected Alpaca websocket transport with authentication/subscription plus bounded reconnect/backoff. Recovery intentionally persists only minimum trading continuity state; richer durable audit/event storage, distributed supervision and provider failover remain deferred until forward operation demonstrates the need.

## Pre-Flight Gate v1

Added `src/preflight.py` as the final explicit safety/configuration gate before the first controlled real-time paper run. The gate produces a structured PASS/FAIL report and never submits orders. It checks credential presence with redacted reporting, BTC/USD 1-minute scope, explicit risk protections, paper-account cleanliness, checkpoint writability, execution lock, injected provider connectivity/subscription, and runtime startability. Failures block progression rather than being silently tolerated.

## Coinbase Public Market Data Adapter v1

After Alpaca account/MFA onboarding blocked the first external dry-run, the provider-neutral boundary was exercised by adding Coinbase Advanced Trade public market data as a replaceable source. Added an unauthenticated `BTC-USD` market-trades WebSocket transport, heartbeat subscription, deterministic 1-minute OHLCV aggregation from trades, a Coinbase completed-bar adapter, bounded reconnect behavior, and public-provider pre-flight support that does not require credentials. Order execution remains hard-disabled for the connectivity/dry-run stage. Alpaca remains a deferred provider option rather than an architectural dependency.

- Added Coinbase public connectivity dry-run runner and deterministic tests; runner has no broker/session dependency and cannot submit orders.

## 2026-08-08 — Coinbase Live Paper Bridge v1
- Added bounded live-paper runner: Coinbase completed 1m bars -> Feed Health -> Operational Runtime -> accumulating PaperTradingSession -> EMA Strategy -> Risk Engine -> PaperBroker.
- Real broker/order transport is structurally absent from this runner; only PaperBroker can execute simulated orders.
- Live strategy history is accumulated across accepted bars; risk policy uses 1% stop distance and 3R target for paper authorization.
- Corrected StrategyEngine package import compatibility so `python -m src...` runners can reuse the tested engine.
- Deferred: exchange execution adapter/API credentials, persistence hardening, multi-asset live orchestration, production stop/target policy, fees/slippage calibration, monitoring/alerts. Reason: first prove bounded end-to-end live-data paper behavior before increasing operational or capital risk.

## Forward Paper Session v1
- Promoted the proven bounded Coinbase live-paper bridge into a configurable supervised forward-paper observation runner.
- Added append-only JSONL audit evidence for session boundaries, rejected bars, paper events, strategy/risk/order outcomes and account snapshots.
- Real order execution remains structurally unavailable.
- Explicitly deferred crash-transparent strategy-history and in-progress 1m aggregator recovery; current operational checkpoints alone are insufficient to claim exact EMA continuity after restart.

## Forward Paper Continuity / Recovery v1
The first supervised forward-paper run produced a real-data BUY and ended with an open paper BTC position. That promoted exact restart continuity from deferred work to MUST-HAVE. Added atomic continuity persistence for broker/risk/feed/session state plus accumulated EMA history and the in-progress Coinbase minute bucket, and added a one-time bootstrap path from the preserved first-live audit. Mutable runtime artifacts are now ignored by Git; the first live audit is retained as evidence.

## Restart Gap Reconciliation v1
- Added explicit restart-only feed rebase for intentional offline gaps without weakening normal missing-bar protection.
- Restart boundary bar is audit-visible but non-tradable; the next contiguous bar returns to normal Feed Health -> strategy -> risk -> paper flow.
- Forward-session bar limits now count bars processed in the current invocation rather than cumulative restored runtime history.


## Extended Forward Run Readiness + Session Report v1
- Added deterministic read-only reporting for the latest complete forward-paper audit session.
- Report covers processed/rejected/rebase bars, BUY/SELL/HOLD signals, risk ALLOW/REDUCE/REJECT outcomes, paper/fill counts, start/final equity, net P&L, max drawdown, final position, end reason and explicit real-order evidence.
- Incomplete/malformed latest sessions fail closed instead of producing a misleading summary.
- Longer unattended/cloud operation remains deferred; the next evidence step is a supervised 30-60 bar live Coinbase forward-paper run followed by report review.

## 2026-08-09 — Coinbase Late-Trade Ordering Robustness v2
- First extended forward run stopped safely on an out-of-order Coinbase trade arriving across websocket messages.
- Added a bounded 2-second event-time reorder buffer ahead of the strict 1-minute aggregator; trades are processed chronologically only after the watermark makes them safe.
- Persisted pending reorder-buffer state through Forward Paper Continuity so restart does not silently lose buffered trades.
- Preserved fail-closed behavior for trades that arrive beyond the configured reorder window.

- Live 5-bar probe exposed false stale rejection after event-time buffering. Added adapter-specific completed-bar freshness reference (bar close), preserving strict future/order/gap guards.

## 2026-08-09 — Coinbase Transport Resilience v1
- Investigated the first extended forward run ending after 12 healthy bars followed by stale/missing-gap rejections.
- Corrected the earlier hypothesis: Coinbase heartbeats and reconnect were already present. The run ended because repeated Feed Health failures halted the operational runtime, after which Forward Paper mislabeled the stop as `TRANSPORT_ENDED`.
- Added transport disconnect/reconnect control events and audit visibility.
- Reconnect budget now resets after a successful post-reconnect message so separate transient outages do not accumulate against one lifetime counter.
- Partial Coinbase aggregation state is discarded across a disconnect to avoid constructing OHLCV from a market interval that may contain missed trades.
- The first fresh excessive-gap completed bar after reconnect is a non-tradable `RECONNECT_REBASE`; strict gap enforcement resumes immediately afterward.
- Runtime safety halts are now audited as `RUNTIME_HALTED`.

## Transport Failure Recovery v2
- Added bounded exponential reconnect backoff for temporary DNS/network outages.
- Reconnect exhaustion is now a controlled transport terminal event rather than an uncaught exception.
- Forward-paper audit always closes with `SESSION_END reason=TRANSPORT_FATAL` on exhausted reconnects.
- Continuity state is checkpointed before controlled transport-fatal shutdown; real execution remains impossible.


## Reconnect Replay Reconciliation v1
- Completed Coinbase bars at or behind the already-accepted feed watermark are classified as provider replay and dropped before the trading/Feed Health pipeline.
- Replay drops remain audit-visible (`PROVIDER_REPLAY_DROPPED`) but do not consume the operational runtime consecutive-failure budget.
- Fresh forward bars still pass through strict freshness, ordering and missing-gap validation; real execution remains impossible.
- This change targets the observed 10:25 -> 10:23 -> 10:24 replay sequence that previously caused a false `RUNTIME_HALTED` during the supervised 30-bar run.

## Forward Operational Diagnostics v1
- Extended the read-only forward session report with transport disconnect/reconnect counts, reconnect success rate, reconnect exhaustion count and provider replay-drop count.
- Added market-time continuity diagnostics: first-to-last processed-bar span, contiguous 1-minute expectation and observed gap minutes. This makes long wall-clock runs with sparse accepted bars visible instead of hiding them behind a simple PASS.
- Added trading-activity diagnostics: actionable signal rate, risk-rejection rate among actionable signals and grouped risk-rejection reasons.
- Diagnostics remain observational only: no strategy, risk threshold, execution, reconnect or Feed Health behavior is changed.

## 2026-08-09 — 24/7 Market-Universe Target Clarified
- Clarified that `BTC-USD` is the controlled live-paper proving instrument, not the final product scope.
- Recorded the long-term 24/7 operating model: Universe Manager -> lightweight broad scanner -> candidate ranking -> deep strategy/regime analysis -> Risk Engine -> portfolio gate -> execution.
- The Agent is intended to run continuously while respecting venue/session calendars; individual markets are not assumed to trade 24/7.
- Broad multi-market scanning remains intentionally deferred until single-symbol transport/runtime stability and extended forward evidence are proven, so scale does not multiply unresolved operational defects.

## 2026-08-09 — Hybrid WS + REST Recovery v1
- The first 60-bar operational-quality run finished 60/60 but required more than three hours, with 17 disconnects, 16 reconnects and 144 minutes of observed market-time gap.
- Kept WebSocket as the primary live source but removed perfect-socket continuity as a system assumption.
- Added public Coinbase Exchange REST 1-minute candle recovery for exact missing intervals after restart/reconnect.
- Backfilled bars are validation/state catch-up only: they update feed continuity, EMA input history, mark-to-market and Risk Engine equity observation but never execute historical signals/orders.
- Added exact-minute coverage validation, bounded recovery size, short bounded retry for REST propagation delay, audit evidence and `BACKFILL_FATAL` fail-closed shutdown when continuity cannot be proven.
- Extended Forward Session Report with hybrid backfill/failure counts and continuity metrics that include recovered minutes.

## Startup Historical Catch-up v1
A 60-bar Hybrid gate attempted after overnight downtime stopped safely before trading because the persisted-to-live gap was 896 minutes, exceeding the normal 300-minute reconnect limit. This was classified as a different operational boundary rather than solved by weakening the reconnect limit. Added startup-only bounded historical catch-up using the already chunked REST client, exact minute validation, non-tradable state reconstruction, separate audit evidence, and a seven-day default startup ceiling. Normal reconnect recovery remains capped at 300 minutes.

## 2026-08-10 — Exact One-Minute Boundary Recovery
- Hybrid 60-bar live evidence completed 60/60 with REST recovery and a real paper BUY, but operational diagnostics reported `observed_gap=1.0m`.
- Audit isolation proved the missing minute was `11:34`: the last accepted live bar was `11:33`, reconnect occurred, and trading resumed on `11:35` without a REST backfill record for `11:34`.
- Root cause was an off-by-policy boundary: recovery started only when the live timestamp delta was greater than Feed Health `max_gap=2m`; a 2m delta therefore bypassed recovery even though it represents one missing 1m candle.
- Reconnect/restart recovery now uses strict timeframe continuity (`gap > 1m`) while normal live Feed Health tolerance remains unchanged.
- Added a regression test reproducing `11:33 -> reconnect -> 11:35`, requiring REST recovery of exactly `11:34` before `11:35` can be processed.

## 2026-08-10 - Post-Recovery Position Reconciliation v1
Forward-paper evidence isolated a real lifecycle edge case rather than a strategy-frequency issue. The current long was opened live at 11:20 UTC. Offline reconstruction of audited bars found EMA20 crossing below EMA50 at 12:27 UTC inside startup catch-up. Because recovery bars intentionally cannot trade, the event-based SELL disappeared once live state resumed already BELOW. Added durable recovery-transition detection and first-fresh-live-bar reconciliation: historical bars remain non-actionable, the pending exit survives checkpoints, execution occurs only at current live price/time, and REAL execution remains impossible. Added regression tests around persistence and non-retroactive exit timing.


## 2026-08-10 — Hybrid 60-Bar Verification Gate — PASS WITH TRANSPORT WARNING
- Completed the fresh supervised gate with 60/60 processed, 0 rejected, `MAX_BARS`, `audit_complete=True`, hybrid recovery failures=0, `observed_gap=0.0m`, and `REAL_orders=0`.
- Preserved exact market-time continuity across a 306-minute span by reconstructing 191 reconnect REST backfill bars plus 56 startup catch-up bars; recovery bars remained non-retroactive/non-tradable.
- Post-Recovery Position Reconciliation activated in forward evidence: the recovery-detected bearish transition produced a current-live-time paper SELL rather than a historical fill.
- Strategy Behavior Diagnostics v2 observed both regimes and transitions; a later bullish BUY signal was rejected by Risk Engine because the minimum reward/risk requirement was not met.
- Transport remained materially unstable on the local Windows environment: 16 disconnects, 12 reconnects (75% success), ~2697.2s total outage and ~1967.4s maximum outage, with RESET and DNS causes.
- Classification: continuity/safety gate PASS; transport quality WARNING. Local WebSocket behavior is not accepted as production-grade. Controlled cloud transport validation plus monitoring/alerting remains required before unattended 24/7 live deployment.

## 2026-08-11 — Risk/Reward Decision Diagnostics v1
- Traced the observed live BUY rejection at `63850.18` through strategy -> planned stop/target -> Risk Engine.
- Proved the bridge constructed an exact 3R target while binary floating-point arithmetic produced `2.9999999999999885`, falsely satisfying the previous strict `< 3.0` rejection check.
- Added an exact live-price regression test and a separate meaningfully-below-threshold rejection guard.
- Added a fixed `1e-12` relative tolerance only for threshold equality; stop/target validation, risk sizing, exposure caps and the configured 3R policy are unchanged.
- Added planned entry, stop, target, computed reward/risk and required-minimum evidence to both approved and rejected paper BUY events.
- Extended the read-only forward-session report with reward/risk evaluation count, rejection count, observed ratio range and required thresholds.
- Validation: 72/72 targeted Risk Engine, Paper Trading and Forward Session Report tests pass; the complete local Windows/Python 3.14.6 repository passes 553/553 automated tests.

## 2026-08-11 — Operational Monitoring & Alerting v1
- Promoted monitoring/alerting into the active operational-readiness path before cloud soak testing.
- Added an independent read-only monitor over the latest forward audit session and continuity state.
- Added deterministic `OK` / `WARNING` / `CRITICAL` classification, stable alert codes, operator-readable and JSON output, and process exit codes `0/1/2`.
- Added critical detection for missing/unreadable/stale active-session evidence, fatal backfill/transport/runtime endings, REST recovery failure, reconnect exhaustion, non-zero REAL-order evidence and active Risk kill switch.
- Added warnings for a current transport disconnect and pending post-recovery long-exit reconciliation.
- Added explicit `recorded_at` timestamps to new audit records and `saved_at` timestamps to new forward continuity checkpoints without changing market timestamps or trading decisions.
- External notification delivery and process supervision remain separate deferred adapters that will consume this monitoring boundary during Cloud Runtime Readiness.
- Real retained runtime validation classified the completed 60-bar session as `OK / COMPLETED / MAX_BARS` with `REAL_orders=0` and no alerts. That probe exposed a backward-compatibility display gap: legacy `SESSION_END` records predate `recorded_at`, so audit age incorrectly appeared as zero. Added file-modification-time fallback and regression coverage for legacy completed audits.
- Repeated real-artifact monitoring after the fallback reported matching audit/checkpoint age, retained `OK / COMPLETED / MAX_BARS`, `REAL_orders=0` and zero alerts.
- Final validation: 37/37 targeted Operational Monitoring and Forward Paper tests pass; the complete local Windows/Python 3.14.6 repository passes 572/572 automated tests.

## 2026-08-11 — Cloud Runtime Readiness v1
- Added a provider-neutral pre-deployment gate before cloud-provider selection or paid infrastructure creation.
- Added fail-closed checks for explicit PAPER mode, disabled real execution, a positive bounded session, monitoring cadence below stale threshold, absolute colocated audit/state paths, writable persistent storage, required runtime imports and Python 3.12-3.14.
- Storage readiness uses a temporary write/read/cleanup probe; invalid paths block the probe so a failed configuration cannot create an unintended relative runtime directory.
- Added operator-readable and JSON reports with deterministic exit codes `0=PASS` and `2=FAIL`.
- The gate does not start trading, place orders, alter strategy/risk policy, provision infrastructure or choose a cloud vendor.
- Validation: 13/13 focused Cloud Runtime Readiness tests and the complete 585/585 local Windows/Python 3.14.6 repository suite pass.
- Real CLI validation passed all seven checks with PAPER mode, real execution disabled, five bounded bars, 30-second monitoring, 180-second staleness, absolute colocated paths, writable storage, importable runtime components and Python 3.14.

## 2026-08-11 — Controlled Cloud Deployment Baseline v1
- Provisioned the first controlled paper-validation host: Hetzner CPX22 in Nuremberg with Ubuntu 24.04 LTS, x86, 2 vCPU, 4 GB RAM and 80 GB SSD.
- Enabled Hetzner account 2FA, retained an offline recovery key and configured a dedicated passphrase-protected ED25519 SSH key.
- Attached a free provider firewall with SSH and ICMP inbound rules; all unrelated new inbound traffic is implicitly denied while required outbound connectivity remains available.
- Installed all available Ubuntu LTS security updates and proved a controlled server reboot followed by successful SSH-key reconnection.
- At initial provisioning, no repository code, API credentials, trading runtime or real-order capability was deployed to the host.
- Clean-clone validation reproduced four failures in `tests/test_strategy_engine.py`: the tests read workstation-only `data/AAPL.csv`, which is excluded by the repository `*.csv` ignore rule.
- Replaced only those external test reads with deterministic in-memory OHLCV data; production Strategy Engine and trading policy are unchanged.
- Validation: 9/9 targeted Strategy Engine tests and the complete 585/585 repository suite pass both in the isolated clean repository without the local CSV artifact and on Windows/Python 3.14.6.
- Deployed exact commit `6095960` to `/opt/ai-alpha`; Ubuntu 24.04/Python 3.12.3 reproduced 9/9 focused Strategy Engine tests and the complete 585/585 suite.
- Created root-only persistent runtime storage at `/var/lib/ai-alpha`; the real cloud CLI gate passed all seven readiness checks with PAPER mode, real execution disabled, five bounded bars, 30-second monitoring cadence and 180-second stale threshold.
- Started the first bounded cloud PAPER session as transient systemd unit `ai-alpha-paper-smoke-v1`; it completed independently of SSH with `Result=success`, `ExecMainStatus=0` and `MAX_BARS`.
- Deterministic session evidence: `PASS`, `audit_complete=True`, 5 processed, 0 rejected, 0 rebases, BUY/SELL/HOLD `0/1/4`, paper/filled/REAL orders `0/0/0`, disconnects/reconnects `0/0`, recovery failures `0`, market span `4.0m` and `observed_gap=0.0m`.
- Operational Monitoring classified the persistent cloud evidence as `OK / COMPLETED / MAX_BARS`, with `REAL_orders=0` and zero alerts.
- Controlled Cloud Deployment Baseline v1 is closed. No exchange credentials or real-order capability were installed; longer supervised cloud soak testing and operational service/restart controls remain mandatory before unattended 24/7 readiness.

## 2026-08-12 — Cloud Service Supervision & Restart Validation v1 (Implementation)
- Added reviewed systemd deployment artifacts for a bounded ten-bar PAPER service, independent Operational Monitoring oneshot/timer, non-activating installer and operator runbook.
- The forward process runs under the passwordless/non-login `ai-alpha` system identity with a private `0700` state directory; project/OS paths are read-only and no exchange credentials or real-execution adapter are introduced.
- Every start is blocked by the existing Cloud Runtime Readiness gate unless PAPER mode, disabled real execution, bounded bars, monitoring cadence, persistent paths, writable storage, components and Python runtime all pass.
- Added bounded `Restart=on-failure`, restart rate limiting, controlled `SIGINT` shutdown and journald evidence. Normal `MAX_BARS` completion does not restart.
- Added a persistent one-minute timer that invokes only the existing read-only Operational Monitoring policy. The timer cannot start/restart paper trading; installation performs no activation.
- Extended the read-only forward report with the latest `resumed` session boundary so cloud restart evidence is explicit and machine-readable; trading decisions and recovery semantics are unchanged.
- TDD evidence: the new supervision suite first failed 10/10 because no deployment artifacts existed, then passed 10/10 after minimal implementation. The report extension first failed 2 tests, then passed 22/22 combined supervision/report tests.
- Local isolated validation: 72/72 focused supervision/readiness/monitor/runtime tests and the complete 595/595 suite pass. systemd 255 offline security analysis reports `3.0 OK` for the paper service and `2.7 OK` for the monitor.
- Windows/Python 3.14.6 validation: 22/22 combined supervision/report tests and the complete 595/595 repository suite pass.
- Pending before closure: commit/push, exact-revision CPX22 installation, native systemd verification, controlled restart with `resumed=True`, clean ten-bar completion and recurring monitoring evidence.
