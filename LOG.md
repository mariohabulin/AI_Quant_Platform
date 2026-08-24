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

## 2026-08-12 — Cloud Service Supervision & Restart Validation v1
- Added reviewed systemd deployment artifacts for a bounded ten-bar PAPER service, independent Operational Monitoring oneshot/timer, non-activating installer and operator runbook.
- The forward process runs under the passwordless/non-login `ai-alpha` system identity with a private `0700` state directory; project/OS paths are read-only and no exchange credentials or real-execution adapter are introduced.
- Every start is blocked by the existing Cloud Runtime Readiness gate unless PAPER mode, disabled real execution, bounded bars, monitoring cadence, persistent paths, writable storage, components and Python runtime all pass.
- Added bounded `Restart=on-failure`, restart rate limiting, controlled `SIGINT` shutdown and journald evidence. Normal `MAX_BARS` completion does not restart.
- Added a persistent one-minute timer that invokes only the existing read-only Operational Monitoring policy. The timer cannot start/restart paper trading; installation performs no activation.
- Extended the read-only forward report with the latest `resumed` session boundary so cloud restart evidence is explicit and machine-readable; trading decisions and recovery semantics are unchanged.
- TDD evidence: the new supervision suite first failed 10/10 because no deployment artifacts existed, then passed 10/10 after minimal implementation. The report extension first failed 2 tests, then passed 22/22 combined supervision/report tests.
- Local isolated validation: 72/72 focused supervision/readiness/monitor/runtime tests and the complete 595/595 suite pass. systemd 255 offline security analysis reports `3.0 OK` for the paper service and `2.7 OK` for the monitor.
- Windows/Python 3.14.6 validation: 22/22 combined supervision/report tests and the complete 595/595 repository suite pass.
- Deployed exact commit `accedf0` to CPX22; 22/22 focused supervision/report tests and the complete 595/595 Ubuntu/Python 3.12.3 suite pass.
- The installer created the non-login `ai-alpha` identity and private `0700` runtime directory, passed native `systemd-analyze verify`, installed all units and activated none. The PAPER service remained boot-disabled.
- Every controlled service start passed all seven Cloud Runtime Readiness checks. Initial resume reconstructed 1056 offline minutes as non-tradable startup catch-up before fresh PAPER processing.
- After three fresh durable bars, one operator restart delivered `SIGINT`, stopped cleanly and started a second process with another readiness PASS and `resumed=True`; one provider replay at the accepted watermark was safely dropped.
- The restarted service completed 10/10 fresh bars with `Result=success`, `ExecMainStatus=0` and no automatic failure restarts. The final report returned `PASS`, `audit_complete=True`, `resumed=True`, zero rejected bars, zero disconnects, zero recovery failures, `observed_gap=0.0m`, `MAX_BARS` and `REAL=0`.
- Enabled only the persistent one-minute Operational Monitoring timer. Recurring journald evidence reports `OK / COMPLETED / MAX_BARS`, `REAL_orders=0` and zero alerts while the PAPER service is inactive and boot-disabled.
- Cloud Service Supervision & Restart Validation v1 is closed. Next evidence boundary: a bounded multi-hour cloud PAPER soak; overnight, 24-hour, multi-day and any real execution capability remain gated.

## 2026-08-12 — Bounded Multi-Hour Cloud PAPER Soak v1 (Preparation)
- TDD RED: the expanded supervision contract failed 5 tests because no reviewed session configuration existed, the systemd unit duplicated a fixed ten-bar literal and the installer did not deploy root-controlled duration policy.
- Added committed `deploy/systemd/ai-alpha-paper.env` with the first multi-hour bound of 180 completed one-minute bars, approximately three hours.
- The systemd service now imports the root-owned configuration before Cloud Runtime Readiness and passes the identical value to `forward_paper_session --bars`, preventing validation/execution drift.
- The non-activating installer deploys the configuration under `/etc/ai-alpha` before native unit verification. It still cannot start, restart or enable trading.
- TDD GREEN: all 12 supervision-contract tests pass after the minimal deployment-adapter change.
- Isolated validation: 25/25 combined supervision/readiness tests and the complete 597/597 Python 3.12.13 suite pass; whitespace and installer shell syntax checks are clean.
- Windows validation: 25/25 combined supervision/readiness tests and the complete 597/597 repository suite pass on Python 3.14.6.
- Strategy, Risk Engine, Feed Health, hybrid recovery, PaperBroker decisions and the structural `REAL_orders=0` lock are unchanged.
- Pending evidence: exact-commit cloud deployment validation and the controlled 180-bar cloud PAPER run with recurring monitoring and deterministic final reports.

## 2026-08-13 — Bounded Multi-Hour Cloud PAPER Soak v1 — PASS WITH ORDERING/RESTART WARNING
- Deployed exact commit `0d5477c` to CPX22 with root-owned `AI_ALPHA_SESSION_BARS=180`, boot-disabled PAPER activation and the enabled read-only monitor timer.
- Reproduced the complete 597/597 Ubuntu/Python 3.12.3 suite, native systemd verification and all seven Cloud Runtime Readiness checks before starting.
- The first attempt recovered four transient WebSocket disconnects, then correctly failed closed on a Coinbase trade arriving outside the strict reorder boundary. The process exited status 1; systemd restarted it after ten seconds with `resumed=True` and preserved PAPER continuity.
- The recovered attempt completed 180/180 fresh bars, zero rejected bars, complete audit, `MAX_BARS`, two of two reconnects, 11.2 seconds total outage, zero recovery failures and `observed_gap=0.0m`.
- Strategy/Risk evidence contained BUY/SELL/HOLD `1/0/179`, one exact-3R BUY reduced by the exposure cap, one PAPER fill and `REAL_orders=0`. Final equity was `4998.56`, final open PAPER position `0.01971055`, session mark-to-market change `+1.70` and max drawdown `0.0273%`; these are operational observations, not profitability evidence.
- Final monitoring reported `OK / COMPLETED / MAX_BARS`, but review proved that latest-session selection hid the prior failed process. The functional continuity/safety gate passed; the complete milestone remains warning-bearing until restart incident visibility is deployed and proven.

## 2026-08-13 — Restart Incident Visibility v1 (Local Implementation)
- TDD RED proved three gaps: no persistent systemd post-stop incident record, a failed latest attempt was mislabeled `RUNNING`, and a later healthy restart hid the previous failure.
- Added standard-library append-only `PROCESS_INCIDENT` persistence using systemd's `SERVICE_RESULT`, `EXIT_CODE` and `EXIT_STATUS` evidence. Clean results create no incident; missing evidence fails visible as unknown.
- Added read-only monitoring policy: current process incidents are `CRITICAL / FAILED / PROCESS_FAILURE`; an incident in the immediately previous attempt remains `PREVIOUS_PROCESS_FAILURE WARNING` throughout the restarted attempt, including after `MAX_BARS`.
- Preserved lifecycle ownership by ignoring only the recorder command's exit status at the systemd boundary. The recorder cannot start/restart PAPER, alter the original service result, classify alerts or enter trading logic.
- TDD GREEN: 39/39 focused process-incident/monitoring/supervision tests and the complete 605/605 Python 3.12.13 suite pass. Native systemd 255 syntax verification passes in the isolated path-adjusted validation environment.
- Strategy, Coinbase ordering policy, Feed Health, hybrid recovery, Risk Engine, PaperBroker and structural `REAL_orders=0` behavior are unchanged. Exact-commit Windows and cloud deployment validation remain the next operational gate.

## 2026-08-13 — Restart Incident Visibility v1 — Cloud Validation and Closure
- Committed and pushed exact revision `7d3a203`; reproduced 39/39 focused and 605/605 complete tests on Windows/Python 3.14.6 and CPX22 Ubuntu/Python 3.12.3.
- Installed the revised systemd unit without starting or enabling PAPER. Native target-unit verification passed; the new `ExecStopPost` recorder, failure-only restart policy and ten-second restart delay were present; PAPER remained boot-disabled.
- Started the bounded PAPER service through all seven Cloud Runtime Readiness checks with `resumed=True`. Startup catch-up reconstructed 923 offline minutes without retroactive trading; the first fresh live bar safely executed the previously pending PAPER long exit and restored a flat position before the incident probe.
- Issued one controlled `SIGKILL` to the PAPER main process. systemd reported `signal / killed / KILL`; `src.process_incident` durably appended `PROCESS_INCIDENT`; direct Operational Monitoring returned `CRITICAL / FAILED / PROCESS_FAILURE`; `REAL_orders=0` remained invariant.
- systemd performed one automatic restart after ten seconds. All seven readiness checks passed again, continuity restored with `resumed=True`, and direct plus recurring timer monitoring returned `WARNING PREVIOUS_PROCESS_FAILURE` while the new process ran.
- The restarted process completed 180/180 fresh bars with zero rejected bars, complete audit, `MAX_BARS`, zero transport disconnects, zero recovery failures and `observed_gap=0.0m` across a 179-minute market span.
- Strategy/Risk evidence recorded BUY/SELL/HOLD `2/1/177`, ALLOW/REDUCE/REJECT `178/2/0`, two exact-3R evaluations, three filled PAPER orders and `REAL=0`. Final equity was `5002.09`, final open PAPER position `0.01963061`, session equity change `+4.56` and max drawdown `0.0946%`; the equity change includes open-position mark-to-market movement and is not profitability evidence.
- After `MAX_BARS`, both direct monitoring and the independent timer retained `WARNING / COMPLETED / MAX_BARS` with the exact prior `signal / killed / KILL` incident visible. PAPER ended `inactive/dead/disabled`; the monitor timer remained `active/waiting/enabled`; the cloud repository was clean on `7d3a203`.
- Restart Incident Visibility v1 is closed. The next authorized activity is repository-reviewed preparation for a bounded overnight PAPER soak; 24-hour, multi-day, unattended production and real execution remain gated.

## 2026-08-13 — Overnight Cloud PAPER Soak v1 (Preparation)
- TDD RED: the supervision contract expected a reviewed twelve-hour overnight bound while the committed root-owned configuration still contained the completed three-hour value of 180 bars.
- Set `AI_ALPHA_SESSION_BARS=720`, approximately twelve hours of fresh one-minute PAPER evidence and strictly below the separate 24-hour gate. Cloud Runtime Readiness and the forward runner continue to consume the same installed root-owned value.
- Defined a clean overnight pass as 720/720 processed, zero rejected bars, complete audit, `MAX_BARS`, `observed_gap=0.0m`, zero recovery failures, zero reconnect exhaustion, 100% reconnect success when needed, systemd `Result=success`, `ExecMainStatus=0`, `NRestarts=0`, final monitoring `OK` and `REAL_orders=0`.
- The overnight gate contains no intentional restart or fault injection. Any durable process incident, automatic restart, critical monitoring decision or previous-process-failure warning blocks a clean pass and requires explicit review.
- Strategy, Coinbase ordering, Feed Health, hybrid recovery, Risk Engine, PaperBroker, process-incident visibility and the structural real-execution lock are unchanged. The installer remains non-activating and PAPER remains boot-disabled.
- TDD GREEN and isolated validation: 13/13 supervision-contract tests, 26/26 combined supervision/readiness tests and the complete 605/605 Python 3.12.13 suite pass; whitespace and installer shell-syntax checks are clean.
- Windows/Python 3.14.6 validation: 26/26 combined supervision/readiness tests and the complete 605/605 repository suite pass; patch-format validation is clean.

## 2026-08-14 — Overnight Cloud PAPER Soak v1 — Failure Review
- Committed/pushed and deployed exact preparation revision `d96c981`; both Windows and CPX22 reproduced 26/26 focused plus 605/605 complete tests. Native systemd verification and all seven Cloud Runtime Readiness checks passed with `AI_ALPHA_SESSION_BARS=720` before the explicit start.
- Started PAPER at 2026-08-13 17:37 UTC with `resumed=True`. Startup catch-up reconstructed 156 minutes without retroactive orders, and initial monitoring was `OK / RUNNING` with fresh audit/state and `REAL_orders=0`.
- The overnight activation accumulated seven automatic restarts. Every failed process exited status 1 with the same safe boundary: `ValueError: Out-of-order Coinbase trade rejected.` Incidents occurred at 20:59 and 23:10 UTC on August 13, then 00:22, 00:25, 00:26, 04:54 and 05:18 UTC on August 14.
- Only two WebSocket disconnects were recorded, at 21:27 and 03:19 UTC, and both reconnected successfully. Most ordering failures were therefore not immediately preceded by a recorded disconnect; the evidence does not justify blindly widening the existing two-second reorder window.
- Because every automatic restart created a fresh per-process 720-bar counter, the reviewed twelve-hour bar bound did not bound the complete service activation. The latest process was still active with `NRestarts=7` the next morning.
- Issued a controlled stop at 07:56 UTC. systemd delivered SIGINT and returned `success`; PAPER remained inactive/dead/disabled. Final durable account evidence was flat at equity `4977.59`, with `REAL_orders=0` throughout.
- The clean stop exposed a distinct audit-lifecycle defect: `main()` caught `KeyboardInterrupt` and returned 130 without `SESSION_END`. Monitoring later returned stale `CRITICAL / RUNNING`, and the deterministic report failed closed because the latest session was incomplete.
- Stopped, but did not disable, the monitor timer and reset the monitor failure. Final parked state: PAPER inactive/dead/disabled; monitor service inactive/dead/static; timer inactive/dead/enabled; all service results success and all audit/journal evidence retained.
- Classified the overnight gate `FAIL WITH SAFETY PRESERVED`. No 24-hour/multi-day progression is authorized.

## 2026-08-14 — Overnight Soak Failure Closure v1 (Local Implementation)
- TDD RED specified typed late-trade timing evidence, durable `LATE_TRADE_REJECTED`/`ORDERING_FATAL`, a closed `OPERATOR_STOP`, MAX_BARS-only report PASS semantics, fatal/root-cause monitoring and a whole-activation restart budget.
- Added `CoinbaseTradeOrderingError` without widening the two-second policy. It retains trade/active bucket timestamps, latest-seen timestamp, event-time watermark, configured window and measured seconds beyond the watermark.
- Forward PAPER now writes late-trade diagnostics, saves continuity, appends `SESSION_END reason=ORDERING_FATAL` and re-raises for the existing non-zero/systemd restart path.
- A controlled KeyboardInterrupt now closes only the newly opened current attempt as `OPERATOR_STOP` from durable audit/checkpoint evidence before the CLI returns 130. A startup interrupt cannot relabel an older incomplete attempt.
- Operational Monitoring classifies operator stop as `WARNING / STOPPED` with no stale-running alerts and ordering fatal as `CRITICAL / FAILED`; an appended systemd process incident no longer hides the explicit ordering root cause.
- Forward report `audit_complete` remains a structural/safety measure, while `PASS` now additionally requires `MAX_BARS`. Operator/fatal ends remain inspectable but non-passing.
- Changed systemd start limiting to `StartLimitIntervalSec=infinity` and `StartLimitBurst=2`, allowing the reviewed initial start plus one automatic recovery start. The runbook requires a guarded budget-opening step before a new inactive activation and prohibits resetting the budget during a gate.
- Focused closure regression passes 97/97; the complete local Python 3.12.13 suite passes 615/615. The exact diff applies cleanly to a detached overnight-base worktree, where 97/97 focused and 615/615 complete tests reproduce with clean whitespace and installer shell syntax. Strategy, Feed Health, recovery, Risk Engine, PaperBroker and `REAL_orders=0` behavior are unchanged.

## 2026-08-14 — Overnight Soak Failure Closure v1 — Cloud Validation and Closure
- Applied the exact closure diff on Windows/Python 3.14.6, reproduced 97/97 focused plus 615/615 complete tests, committed `93b7565` and pushed it with a clean worktree.
- CPX22 fast-forwarded to exact revision `93b7565`. The cloud reproduced 97/97 focused and 615/615 complete tests; the non-activating installer, native unit verification and all seven Cloud Runtime Readiness checks passed with the root-owned 720-bar bound, two-start supervision envelope and PAPER still boot-disabled.
- A first `reset-failed` attempt reported that `ai-alpha-paper.service` was not loaded. Review confirmed systemd had garbage-collected the successful inactive unit, which also removed any retained start-limit counters. The activation runbook now accepts only that exact unit-not-loaded branch after verifying `LoadState=loaded`; every other reset error aborts, and no broad `|| true` escape is permitted.
- Started a short diagnostic at 09:57 UTC. It restored continuity with `resumed=True`, reconstructed 121 startup catch-up bars, processed six fresh contiguous bars, retained `NRestarts=0`, and returned direct monitoring `OK / RUNNING` with fresh audit/checkpoint evidence, zero alerts and `REAL_orders=0`.
- Stopped the process deliberately at 10:02 UTC. systemd returned `success/0` with no restart; the audit appended `SESSION_END reason=OPERATOR_STOP`; monitoring returned `WARNING / STOPPED / OPERATOR_STOP` without stale alerts; and the deterministic report returned the expected non-gate `FAIL` with `audit_complete=True`, six processed bars, `observed_gap=0.0m`, flat final position and `REAL_orders=0`.
- The append-only audit contains no new `PROCESS_INCIDENT` after the diagnostic `SESSION_START`. Historical incidents remain retained as intended. No truly late trade occurred during the short live probe, so `ORDERING_FATAL` remains covered by the 97 deterministic focused tests rather than being presented as live cloud evidence.
- Final parked state: PAPER `inactive/dead/disabled`, monitor timer `inactive/dead/enabled`, cloud repository clean on `93b7565`. Overnight Soak Failure Closure v1 is closed; the next authorized gate is a clean, non-injected 720-bar PAPER soak. No 24-hour, multi-day, unattended production or real execution progression is authorized yet.

## 2026-08-15 — Coinbase Provider Message Sequence Integrity v1 (Local Implementation)
- Reviewed the second non-injected 720-bar attempt from exact revision `e0592ff`.
  The first process reached 266 fresh bars before a 19.637-second
  `ORDERING_FATAL`; the one allowed recovery process reached 46 fresh bars before
  a 56.435-second `ORDERING_FATAL`; systemd then enforced the two-start ceiling.
  Both attempts retained complete terminal audit evidence and `REAL_orders=0`.
- Verified the official Advanced Trade WebSocket contract: `sequence_num`
  increments exactly once per product message, a forward jump identifies a
  dropped message, and a lower number may be ignored or represents out-of-order
  delivery. `market_trades` batches one or more identified trades every 250 ms.
- Root cause classification remains deliberately bounded: the old consumer did
  not inspect message sequence or retain `trade_id`, so historical evidence
  cannot prove whether either cloud event was a replayed envelope or a genuinely
  late trade. The two-second event-time window was not widened.
- Added connection-local sequence validation before OHLCV aggregation.
  Lower/equal envelopes become audit-visible
  `PROVIDER_MESSAGE_REPLAY_DROPPED` controls and never reach trading layers.
  Missing, invalid or forward-gap sequence evidence invalidates the socket and
  enters the existing bounded reconnect/exact REST recovery boundary before any
  contained trade is consumed.
- Closed the partial-boundary edge case: a reconnecting socket cannot trade a
  minute it observed only in part. Such a completed bar is durably recorded as
  `PROVIDER_SEQUENCE_BOUNDARY_BAR_DROPPED`, reconstructed through exact REST
  continuity, and summarized as `sequence_boundary_drops`; only a bar observed
  from its minute start may return to the live decision path.
- Kept the recovery budget honest across reconnects: heartbeats may demonstrate
  socket liveness but cannot reset a sequence-integrity failure. The consecutive
  failure counter resets only after the new socket delivers a validly sequenced
  `market_trades` payload.
- Extended genuine late-trade evidence with `trade_id`, message sequence,
  provider message timestamp and event type. Extended the deterministic report
  with a distinct message-replay count; handled replay records remain visible
  but non-alerting.
- TDD RED covered replay/duplicate suppression, gap-before-payload recovery,
  malformed sequence failure, provider identity on genuine late trades, forward
  audit persistence, report counting and monitoring neutrality. TDD GREEN:
  112/112 focused provider/forward/report/monitoring/supervision tests and the
  complete 630/630 repository suite pass.
- Exact-diff Windows and CPX22 validation remain pending. PAPER stays parked and
  boot-disabled; the monitor timer stays stopped/enabled; no 720-bar, 24-hour,
  multi-day, unattended-production or real-execution progression is authorized.

## 2026-08-15 — Coinbase Cross-Channel Sequence Integrity v1
- Applied and committed the first provider-sequence implementation on Windows as
  `066852b`; reproduced 112/112 focused and 630/630 complete tests on Windows and
  CPX22, followed by all seven Cloud Runtime Readiness checks.
- Started one short non-injected cloud diagnostic with PAPER boot-disabled. The
  process remained `success/0`, `NRestarts=0` and `REAL_orders=0`, but repeatedly
  classified healthy `market_trades` jumps from 0 to 3/4/5 as
  `PROVIDER_SEQUENCE_GAP`. The diagnostic was rejected and stopped through
  SIGINT; systemd parked PAPER `inactive/dead/disabled` without a new process
  incident.
- Ran a separate public read-only WebSocket probe with no Strategy, Risk,
  PaperBroker or service process. It captured one consecutive cross-channel
  stream: `market_trades=0`, `subscriptions=1/2`, `market_trades=3`,
  `heartbeats=4`, then every envelope through 39. The first implementation had
  filtered out the exact messages required to prove continuity.
- Added TDD coverage from the exact cloud fixture and moved sequence observation
  before channel routing. Every sequenced envelope advances the connection-local
  tracker; only market-trade payloads reach OHLCV aggregation. Gap diagnostics
  now retain `provider_channel`; market payloads without sequence remain fatal;
  non-market control messages without the optional field remain transparent.
- Correction validation passes 114/114 focused tests and the complete 632/632
  local suite. The two-second trade watermark, bounded reconnect/REST recovery,
  Strategy, Risk Engine, PAPER execution and `REAL_orders=0` are unchanged.
- Applied the exact correction on Windows/Python 3.14.6, reproduced 114/114
  focused plus 632/632 complete tests, committed `4ff9070` and pushed it from a
  clean worktree. CPX22 fast-forwarded to that exact revision and reproduced the
  same 114/114 focused and 632/632 complete Ubuntu/Python 3.12 suites.
- Re-ran the non-activating installer and all seven Cloud Runtime Readiness
  checks. PAPER remained boot-disabled and inactive before the explicit start.
- The second short cloud diagnostic started at 18:24 UTC with `resumed=True`,
  completed 1559 startup-catch-up bars without retroactive execution and then 13
  fresh contiguous PAPER bars. One post-recovery SELL flattened the inherited
  PAPER position; the remaining 12 decisions were HOLD.
- Diagnostic report evidence: zero rejected bars, rebases, disconnects,
  reconnects, exhaustion, provider bar replays, provider message replays,
  sequence-boundary drops and hybrid failures; 1571/1571 expected market minutes,
  `observed_gap=0.0m`, final position flat and `REAL_orders=0`.
- Stopped through controlled SIGINT. systemd returned `success/0`, `NRestarts=0`
  and PAPER `inactive/dead/disabled`; monitoring reported only the expected
  `WARNING / STOPPED / OPERATOR_STOP`. The report was complete and intentionally
  `FAIL` because the short test did not claim `MAX_BARS`. No process incident was
  created; the monitor timer remained inactive/dead/enabled.
- Coinbase Provider Message Sequence Integrity v1 is closed. One clean,
  non-injected 720-bar PAPER soak is now the next authorized evidence gate; no
  24-hour, multi-day, unattended-production or real-execution progression is
  authorized.

## 2026-08-16 — Coinbase Market-Trades Snapshot Boundary v1 (Local Implementation)
- Reviewed the clean 720-bar attempt on exact revision `46ed877`. The fatal
  attempt completed 603 fresh bars, six PAPER fills and exact 635-minute market
  continuity with zero rejected bars, disconnects, reconnects, exhaustion,
  provider replays, sequence-boundary drops or recovery failures before one
  automatic restart. Its report was complete but correctly failed at 603/720;
  final position was flat and `REAL_orders=0` remained invariant.
- Isolated the exact provider record: `market_trades` message sequence `102964`
  at `05:13:56.580642159Z`, `event_type=snapshot`, carrying trade
  `1070883132` from `05:12:54.738994Z`, 58.912 seconds behind the active
  two-second watermark. This correctly sequenced snapshot proves the prior
  cross-channel fix and does not justify widening live update tolerance.
- Confirmed the official Advanced Trade channel distinction: market-trades
  events may be `snapshot` or `update`, while `update` is the incremental batch
  collected over the preceding 250 milliseconds.
- Added pre-aggregation snapshot classification after full envelope-sequence
  validation. Snapshot trades are excluded from incremental OHLCV and converted
  into `PROVIDER_SNAPSHOT_BOUNDARY` with message/trade identity and event-time
  range; the aggregator also ignores snapshots defensively.
- Reset only the untrusted partial WebSocket minute, record it as
  `PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED`, and reuse exact REST recovery before
  the first fully observed live bucket. Existing `RESTART` startup catch-up
  ownership survives the initial snapshot; recovery remains non-tradable.
- Added deterministic report counts for snapshot boundaries/drops, kept handled
  snapshot evidence monitoring-neutral, and extended future `ORDERING_FATAL`
  alerts with event type, trade ID and provider message identity. Genuine late
  `update` trades remain fail-closed under the unchanged two-second watermark.
- TDD RED reproduced the exact old snapshot failure and the startup-boundary
  ownership edge case. TDD GREEN passes 119/119 focused tests and the complete
  637/637 local Python 3.12.13 suite. Windows and CPX22 reproduction remain
  pending; PAPER and the monitoring timer stay parked and real execution remains
  impossible.

## 2026-08-17 — Coinbase Post-Snapshot Trade Quarantine v1 (Local Implementation)
- Reproduced Snapshot Boundary v1 on Windows and CPX22 as revision `370664d`:
  119/119 focused and 637/637 complete tests, non-activating install and all
  seven readiness checks passed. A short cloud diagnostic processed 112 fresh
  bars after 204 startup-catch-up bars with exact continuity, one handled
  snapshot boundary/drop, no transport/recovery failure and `REAL_orders=0`.
- Reviewed the subsequent 720-bar gate as a failure. Attempt one processed 443
  bars before snapshot sequence `10784` and update `10786` exposed trade
  `1071015409` from `21:33:09.501792Z` at 57.988 seconds lateness. The one
  recovery attempt processed 27 bars before snapshot `7423` and update `7425`
  exposed trade `1071026960` from `22:02:55.664795Z` at 6.013 seconds lateness.
  Both attempts failed closed as `ORDERING_FATAL`; systemd blocked a third start
  and real execution remained impossible.
- Identified the remaining boundary gap: removing the snapshot payload did not
  stop a later sequence-valid `update` from replaying snapshot-era trade rows.
  Provider envelope integrity and incremental trade provenance are separate
  correctness boundaries.
- Added a monotonic trusted snapshot floor in Forward PAPER. Every snapshot,
  including a nonzero in-band snapshot, resets partial aggregation and causes
  later trades strictly older than the next full minute to be copied out before
  the reorder heap. The audit records
  `PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED` with snapshot/update identity,
  trusted floor, trade IDs/count and event-time range.
- Preserved explicit boundary-minute suppression and exact REST state catch-up
  before live decisions. The quarantine floor remains after PAPER resumes so
  delayed snapshot history cannot poison a later active minute.
- Added `snapshot_quarantine_trades` to the deterministic report and kept this
  handled evidence monitoring-neutral. Invalid timestamps remain visible to
  strict validation; a trade at or after the trusted floor that arrives behind
  an active later minute still produces `LATE_TRADE_REJECTED` and
  `ORDERING_FATAL` under the unchanged two-second watermark.
- TDD covers both exact cloud sequence/trade pairs, persistent quarantine,
  startup REST recovery, input immutability/invalid-time fail-closed behavior,
  true post-boundary fatality and `REAL_orders=0`. GREEN passes 124/124 focused
  tests and the complete 642/642 local Python 3.12 suite. Windows/CPX22
  reproduction is pending; cloud services stay parked.

## 2026-08-17 — Coinbase Post-Snapshot Trade Quarantine v1 (Cloud Closure)
- Applied the exact patch on Windows/Python 3.14.6, reproduced 124/124 focused
  and 642/642 complete tests, committed `e7a95ac` and pushed it from a clean
  worktree.
- CPX22 fast-forwarded to exact revision `e7a95ac`, reproduced the same 124/124
  focused and 642/642 complete Ubuntu/Python 3.12 suites, ran the non-activating
  installer and passed all seven Cloud Runtime Readiness checks with the
  root-owned 720-bar bound.
- The short live diagnostic observed one provider snapshot and safely
  quarantined 630 snapshot-era trades before aggregation. It explicitly dropped
  one partial snapshot boundary bar, completed 942 non-tradable startup-catch-up
  bars and then processed six fresh contiguous HOLD bars.
- Diagnostic evidence retained zero rejected bars, PAPER orders, REAL orders,
  disconnects, reconnects, exhaustion, replay drops and recovery failures;
  continuity covered exactly 947 expected market minutes with
  `observed_gap=0.0m`. No late-trade rejection, ordering fatal or new process
  incident occurred, and systemd retained `NRestarts=0`.
- Controlled SIGINT closed the bounded diagnostic as `OPERATOR_STOP`. Its report
  was complete and intentionally `FAIL` because only `MAX_BARS` can pass an
  endurance gate. Monitoring retained only the reviewed historical
  `PREVIOUS_PROCESS_FAILURE` plus expected operator-stop warning; safety stayed
  `REAL_orders=0` and the final position was flat.
- Final parked state: PAPER, monitor service and monitor timer are all inactive;
  PAPER remains boot-disabled, the timer remains enabled but stopped, and the
  cloud repository is clean on `e7a95ac`.
- Coinbase Post-Snapshot Trade Quarantine v1 is closed. One clean non-injected
  720-bar PAPER soak with `NRestarts=0` is the next authorized evidence gate;
  24-hour, multi-day, unattended-production and real-execution progression
  remain closed.

## 2026-08-18 — Clean 720-Bar Cloud PAPER Soak v1 (Pass)
- Reproduced exact closure revision `db5615e` on Windows and CPX22 with 17/17
  supervision tests and the complete 642/642 suite. The cloud repository was
  clean, installation remained unchanged and non-activating, all units were
  parked, and all seven readiness checks passed under `ai-alpha` with
  `AI_ALPHA_SESSION_BARS=720` and real execution disabled.
- Started one non-injected bounded gate at 2026-08-17 14:19 UTC. The same process
  reached normal `MAX_BARS` completion at 2026-08-18 02:32 UTC with systemd
  `Result=success`, `ExecMainStatus=0`, `NRestarts=0` and PAPER ending
  `inactive/dead/disabled`.
- The deterministic report returned `PASS` and `audit_complete=True`: 720/720
  processed, zero rejected/rebased bars, 10 BUY, 10 SELL and 700 HOLD signals,
  20/20 filled PAPER orders, final flat position and `REAL=0`.
- Provider-boundary handling remained safe under live load: 13 snapshot
  boundaries/drops and 5,777 quarantined snapshot-era trades never entered
  incremental decisions. Exact recovery consumed 29 startup-catch-up and 12
  REST backfill bars with zero failures or retroactive orders.
- Transport evidence was clean: zero disconnects, reconnects, exhaustion, bar
  replays, message replays and sequence-boundary drops. Exact continuity covered
  760/760 expected market minutes with `observed_gap=0.0m`.
- Operational Monitoring independently returned `OK / COMPLETED / MAX_BARS`,
  `REAL_orders=0` and zero alerts. PAPER equity moved from 4,983.17 to 4,986.83
  (`net_pnl=+3.66`, maximum drawdown 0.1610%); this remains bounded operational
  evidence rather than a profitability claim.
- Final parked state: PAPER, monitor service and timer are all inactive; PAPER
  remains boot-disabled, the timer remains enabled but stopped, and CPX22 is
  clean on `db5615e`.
- The 720-bar overnight gate is closed as PASS. The next authorized change is
  repository-reviewed preparation for a bounded 1,440-bar 24-hour PAPER gate.
  Multi-day soak, unattended production and real execution remain gated.

## 2026-08-18 — Bounded 24-Hour Cloud PAPER Soak v1 (Preparation)
- Promoted only the committed root-owned duration from 720 to 1,440 completed
  one-minute bars after the clean 720-bar gate passed. Cloud Runtime Readiness
  and Forward PAPER continue to consume the identical installed bound; no
  market-data, Strategy, Risk, recovery, broker or monitoring behavior changed.
- Defined the 24-hour run as a non-injected endurance gate. It requires exactly
  1,440/1,440 processed bars, zero rejected/rebased bars, complete audit,
  `MAX_BARS`, exact market-time continuity, zero recovery failures or reconnect
  exhaustion and 100% reconnect success whenever disconnects occur.
- Retained every provider/recovery diagnostic for review, including snapshot
  boundaries, post-snapshot quarantines, replay drops, backfills, outage causes
  and transport quality. Successful recovery may preserve continuity but may not
  hide the evidence that produced it.
- Required systemd `Result=success`, `ExecMainStatus=0`, `NRestarts=0`, final
  Operational Monitoring `OK / COMPLETED / MAX_BARS` with zero alerts and the
  invariant `REAL_orders=0`. Any process incident, restart, warning or critical
  decision blocks a clean pass.
- Kept installation deliberately non-activating and PAPER boot-disabled. The
  exact revision must pass focused/full Windows tests, commit/push review, the
  same CPX22 tests, non-activating installation and all seven readiness checks
  before an operator may explicitly start the gate.
- A future pass will be 24-hour operational evidence only, not profitability
  proof, unattended-production readiness or live-money authorization. Multi-day
  soak and all real execution remain gated.

## 2026-08-19 — Bounded 24-Hour Cloud PAPER Soak v1 (Pass)
- Reproduced exact revision `f0a7ea8` on Windows and CPX22 with 31/31 combined
  supervision/readiness tests and the complete 643/643 suite. The non-activating
  install placed the reviewed root-owned `AI_ALPHA_SESSION_BARS=1440`; native
  systemd verification and all seven readiness checks passed before activation.
- Ran one non-injected process from 2026-08-18 10:44 UTC to 2026-08-19 11:00
  UTC. It completed 1,440/1,440 fresh bars with zero rejected/rebased bars,
  complete audit, `MAX_BARS`, systemd `success/0` and `NRestarts=0`.
- The deterministic report returned `PASS`: 12 BUY, 12 SELL and 1,416 HOLD
  signals; 23/23 filled PAPER orders; zero Risk rejects; 12 exact 3R
  evaluations; and `REAL=0`.
- Six real WebSocket disconnects recovered six times for 100% success. Total
  outage was 34.9 seconds, maximum outage 5.8 seconds, with zero reconnect
  exhaustion, bar replay, message replay or sequence-boundary drop.
- Retained 15 provider snapshot boundaries/drops and quarantined 4,126
  snapshot-era trades before aggregation. Recovery processed 493 startup
  catch-up plus 15 REST backfill bars without failure or retroactive execution.
  Market continuity was exact across 1,947/1,947 expected minutes with
  `observed_gap=0.0m`.
- Operational Monitoring returned `OK / COMPLETED / MAX_BARS`, zero alerts and
  `REAL_orders=0`. Equity changed from 4,986.83 to 4,992.03 (`+5.20`, maximum
  drawdown 0.2289%); this is operational evidence, not profitability proof.
  The final open PAPER position of 0.01938861 BTC is reportable state rather
  than an endurance-gate failure.
- Parked all three units after review: PAPER remains boot-disabled, the monitor
  timer remains enabled but stopped, all results are `success`, and the cloud
  repository is clean on `f0a7ea8`.
- Bounded 24-Hour Cloud PAPER Soak v1 is closed as PASS. A separately reviewed
  multi-day bound and acceptance contract is next; unattended production and
  real execution remain unauthorized.

## 2026-08-19 — Bounded Three-Day Cloud PAPER Soak v1 (Preparation)
- Promoted only the committed root-owned duration from 1,440 to 4,320 completed
  one-minute bars after the 24-hour gate passed. The same value gates Cloud
  Runtime Readiness and Forward PAPER; no runtime, provider, Strategy, Risk,
  recovery, broker, persistence or monitoring logic changed.
- Defined one non-injected three-day run with exact requirements: 4,320/4,320,
  zero rejected/rebased bars, complete audit, `MAX_BARS`, exact market-time
  continuity, zero recovery failure or reconnect exhaustion and 100% reconnect
  success whenever disconnects occur.
- Retained all provider snapshot/quarantine, replay, backfill, transport-cause
  and outage-duration counters. Successful continuity repair does not erase the
  evidence that exercised it.
- Required systemd `Result=success`, `ExecMainStatus=0`, `NRestarts=0`, final
  Operational Monitoring `OK / COMPLETED / MAX_BARS`, zero alerts and
  `REAL_orders=0`. Any incident, restart, warning or critical decision blocks a
  clean pass.
- Added final CPU-time, memory-peak and swap/OOM review to detect resource growth
  that shorter gates might miss without inventing an arbitrary performance
  threshold.
- Kept installation non-activating, PAPER boot-disabled and real execution
  impossible. The exact revision must pass Windows/cloud focused and complete
  tests, non-activating installation and all seven readiness checks before an
  explicit operator start.
- A future three-day pass authorizes Strategy Evaluation v1 preparation only.
  It is not profitability proof, unattended-production readiness or live-money
  authorization.

## 2026-08-20 — Bounded Three-Day Cloud PAPER Soak v1 (Running Evidence)
- Reproduced exact revision `62e517c` with 31/31 focused and 643/643 complete
  tests, the non-activating installer and all seven readiness checks under the
  committed 4,320-bar bound before the explicit operator start.
- Started one non-injected process at 2026-08-19 15:14 UTC. The reviewed
  2026-08-20 12:45 UTC snapshot retains systemd `success/0`, `NRestarts=0` and
  PAPER `active/running`; PAPER remains boot-disabled and real execution remains
  impossible.
- Three recent monitor cycles returned `OK / RUNNING / RUNNING`, fresh audit and
  checkpoint ages, zero alerts and `REAL_orders=0`. Current strategy/P&L/order
  observations remain interim diagnostics rather than acceptance evidence.
- The process is deliberately left untouched. Exact 4,320-bar completion,
  report/continuity/transport evidence, systemd result and CPU/memory/swap/OOM
  review are still required before the gate can pass.

## 2026-08-20 — Strategy Evaluation Protocol v1 (Local Preparation)
- Added an immutable candidate declaration covering candidate and strategy
  identity, written hypothesis, parameter-set ID, dataset version, timeframe and
  exact named-asset scope. Evidence with changed identity or scope is rejected.
- Added explicit nonzero baseline and strictly harsher component-wise execution-
  cost profiles. The same frozen Multi-Asset Validation configuration now runs
  independently under both profiles; zero-cost research cannot be promoted.
- Added initial configurable evidence-volume and risk gates: at least five
  non-overlapping walk-forward test windows, at least 30 completed unseen trades
  per asset and at most 20% unseen OOS drawdown under either cost profile.
- Added deterministic `PAPER_CANDIDATE`, `RESEARCH_HOLD` and `REJECTED`
  decisions with failed-gate, per-asset and threshold evidence. Every result
  retains `live_execution_authorized=False`; the protocol can promote only to a
  later bounded forward-PAPER review.
- TDD RED proved the new module was absent. GREEN passes 84/84 focused
  protocol/OOS/walk-forward/falsification/multi-asset tests and the complete
  663/663 Python 3.12.13 suite, including one real integration through the
  existing Multi-Asset Validator.
- The change is repository-only and does not alter the active cloud process,
  Strategy logic, Risk Engine, provider, broker, persistence, monitoring or
  systemd configuration. Windows reproduction and Git integration remain
  pending; first candidate promotion remains blocked by the active three-day
  infrastructure gate.

## 2026-08-20 — Strategy Evaluation Protocol v1 (Windows Integration)
- Applied the exact repository-only protocol change on Windows/Python 3.14.6,
  reproduced 84/84 focused validation/protocol tests and the complete 663/663
  repository suite, and retained a clean reviewed file scope.
- Committed `b69f5b1` (`Add Strategy Evaluation Protocol v1`) and pushed it to
  `origin/main`. The active CPX22 process remained untouched on exact soak
  revision `62e517c`; no runtime or systemd unit was changed or restarted.
- Candidate execution remained blocked until the external three-day
  infrastructure gate could finish and be reviewed independently.

## 2026-08-22 — Bounded Three-Day Cloud PAPER Soak v1 (Pass)
- The one non-injected process started on exact revision `62e517c` at
  2026-08-19 15:14 UTC and reached normal completion at 2026-08-22 15:55 UTC.
  systemd retained `Result=success`, `ExecMainStatus=0`, `NRestarts=0` and no
  process incident.
- The deterministic report returned `PASS`, `audit_complete=True`,
  `resumed=True` and `MAX_BARS`: 4,320/4,320 fresh bars, zero rejected/rebased
  bars, 44 BUY, 47 SELL and 4,229 HOLD signals, 89/89 filled PAPER orders,
  zero Risk rejects, 44 exact 3R evaluations, final flat position and `REAL=0`.
- Fifteen genuine WebSocket disconnects recovered 15 times for 100% success.
  Total outage was 88.2 seconds and maximum outage 6.0 seconds, with zero
  reconnect exhaustion, bar replay, message replay or sequence-boundary drop.
- Provider handling retained 39 snapshot boundaries/drops and quarantined
  18,200 snapshot-era trades before aggregation. Exact recovery processed 255
  startup-catch-up and 40 REST backfill bars with zero failure or retroactive
  order. Continuity covered exactly 4,614/4,614 expected market minutes with
  `observed_gap=0.0m`.
- Operational Monitoring independently returned `OK / COMPLETED / MAX_BARS`,
  zero alerts and `REAL_orders=0`. Equity changed from 5,037.72 to 5,134.30
  (`net_pnl=+96.58`, maximum drawdown 1.1202%); this is infrastructure and
  strategy-behavior evidence, not a profitability conclusion.
- Final resource review retained 59 minutes 43.025 seconds CPU time, 97.0 MB
  memory peak, 0 B swap peak and no kernel OOM/killed-process evidence.
- Parked all units after review: PAPER is `inactive/dead/disabled`, the monitor
  service is `inactive/dead/static`, the timer is `inactive/dead/enabled`, all
  results are `success`, and CPX22 remains clean on `62e517c`.
- Bounded Three-Day Cloud PAPER Soak v1 is closed as PASS. Controlled
  Strategy Evaluation Protocol integration and first-candidate research are
  now authorized; unattended production and live-money execution remain closed.

## 2026-08-22 — Strategy Evaluation Protocol v1 (Cloud Integration)
- Fast-forwarded the parked CPX22 repository non-activating from exact soak
  revision `62e517c` through `b69f5b1` to closure revision `9a063fa`. The
  working tree remained clean and no trading or monitoring process was started.
- Reproduced 20/20 standalone protocol tests, 84/84 focused
  protocol/validation tests and the complete 663/663 suite on Ubuntu/Python
  3.12. This matches the previously completed Windows/Python 3.14.6 focused
  and complete validation boundary.
- Ran the standard installer, which explicitly started and enabled nothing.
  All seven Cloud Runtime Readiness checks passed with PAPER mode, the committed
  4,320-bar bound, one-minute monitoring cadence, persistent storage, importable
  runtime components and real execution disabled.
- Confirmed the final parked state: PAPER `inactive/dead/disabled`, monitor
  service `inactive/dead/static`, monitor timer `inactive/dead/enabled`, all
  unit results `success`, zero retained restarts and clean repository
  `9a063fa`.
- Closed Strategy Evaluation Protocol v1 cloud integration as PASS. The next
  authorized activity is pre-registration and offline evaluation of the first
  strategy candidate. `PAPER_CANDIDATE` remains only eligibility for a separate
  bounded forward-PAPER gate and cannot authorize live execution.

## 2026-08-22 — Research Execution Timing Integrity v1 (Local Preparation)
- Architecture review before the first candidate exposed look-ahead execution
  semantics: a signal derived from the current completed Close could receive a
  fill at that same Close even though the signal is known only afterward.
- Added explicit `same_bar_close` and `next_bar_open` modes. The former remains
  the backward-compatible engine default; Strategy Evaluation Protocol v1
  permits only the causal next-open mode.
- Next-open execution retains separate signal and execution indexes, ignores a
  terminal-bar signal without a following Open, values each execution bar at
  its Close and force-closes any remaining terminal position at the final Close
  without inventing an exit signal.
- Aligned buy-and-hold evidence to first-bar Open entry/final-bar Close exit and
  propagated one canonical timing value through OOS, walk-forward, validation
  pipeline and multi-asset passes under both baseline and stressed costs.
- Added report/configuration evidence for signal observation, order execution,
  terminal-position policy and benchmark entry timing. No candidate identity,
  parameter, dataset or result has been selected or inspected.
- TDD and integration evidence pass 130/130 focused research-stack tests and
  the full 684/684 suite locally. Divergent Open/Close manual checks, Python
  compilation and `git diff --check` also pass. Windows/cloud integration and
  Git closure remain pending; all live-money capability remains absent.

## 2026-08-22 — Research Execution Timing Integrity v1 (Windows and Cloud Closure)
- Windows/Python 3.14.6 reproduced 130/130 focused timing/validation/protocol
  tests and the complete 684/684 suite. The reviewed 19-file scope passed both
  unstaged and staged diff checks, was committed as `daf6c5d` and pushed to
  `origin/main`; the local repository remained clean.
- Confirmed the cloud safety boundary before integration: PAPER and monitoring
  were inactive, results were `success`, restart counts were zero and the clean
  repository was on exact `7f2e7fc`.
- Fast-forwarded non-activating to exact `daf6c5d`, then reproduced 130/130
  focused and 684/684 complete tests on Ubuntu/Python 3.12. The systemd
  installer explicitly started and enabled nothing.
- An initial direct readiness command omitted the unit environment and returned
  `FAIL` with `None` configuration values as designed. No unit started and no
  runtime or audit state changed. A corrected invocation used the installed
  4,320-bar configuration plus the exact service environment under the
  `ai-alpha` identity and returned seven of seven checks `PASS`.
- Final verification retained PAPER `inactive/dead/disabled`, monitor service
  `inactive/dead/static`, monitor timer `inactive/dead/enabled`, all results
  `success`, zero restarts and a clean repository on `daf6c5d`.
- Closed Research Execution Timing Integrity v1 as PASS. First-candidate
  pre-registration may now begin, but no strategy result has been inspected,
  no parameters optimized, no forward PAPER authorized and real execution
  remains structurally unavailable.

## 2026-08-22 — First Strategy Candidate Pre-registration v1 (Local Preparation)
- Froze the first candidate before data acquisition or result inspection as
  `ema-crossover-20-50-btc-eth-native-6h-v1`: existing long-only EMA 20/50,
  `BTC-USD` plus `ETH-USD`, native six-hour candles, no leverage, completed-
  Close signal, next-Open execution and final-Close terminal reporting.
- Froze the public Coinbase research range at
  `[2019-01-01T00:00:00Z, 2026-08-01T00:00:00Z)`, exactly 11,076 expected rows
  per asset. The builder is read-only, credential-free and separate from the
  live transport and every broker/order path.
- Added finite 300-candle-aware chunk/retry acquisition, strict UTC continuity
  and OHLCV validation, canonical CSV bytes, per-asset SHA-256 evidence,
  canonical manifest metadata and a manifest SHA-256 sidecar.
- Added an independent candidate lock that rejects noncanonical manifests,
  checksum/source/contract drift, path escape, hash or row mismatch, incomplete
  time grids and invalid/non-finite OHLCV before binding the manifest digest to
  the immutable data version.
- Froze conservative low-volume taker research costs: 0.60% commission per
  side, 0.05% baseline slippage and 0.10% full spread; stress retains
  commission and raises slippage to 0.15% and full spread to 0.30%.
- Added declaration and dataset-lock CLIs that explicitly do not evaluate the
  strategy. Injected provider tests pass 160/160 focused and 714/714 complete
  locally without downloading historical data or observing performance.
- Windows reproduction, exact Git integration and non-activating cloud
  verification remain required before the real dataset may be acquired and
  hashed. Optimization, forward PAPER and live execution remain unauthorized.

## 2026-08-22 — First Strategy Candidate Pre-registration v1 (Windows/Cloud Closure)
- Windows initially returned 158/160 focused tests because the test-only
  manifest mutation helper wrote its SHA sidecar through platform text mode,
  producing `CRLF`. The production builder already used exact bytes and the
  lock correctly rejected the noncanonical sidecar before later assertions.
- Changed only that helper to write explicit ASCII/LF bytes. Windows then
  reproduced 160/160 focused and 714/714 complete tests; the staged nine-file
  scope passed diff checks and was committed/pushed as exact revision
  `27dacb3`. The repository remained clean.
- Confirmed the cloud safety boundary before integration: PAPER and monitoring
  were inactive, unit results were `success`, restart counts were zero and the
  clean repository was on `5168dd8`.
- Fast-forwarded non-activating to `27dacb3`, reproduced 160/160 focused and
  714/714 complete tests on Ubuntu/Python 3.12, and ran the standard installer,
  which explicitly started and enabled nothing.
- Reproduced all seven Cloud Runtime Readiness checks with the exact installed
  PAPER environment, persistent storage, 4,320-bar bound and real execution
  disabled.
- Final verification retained PAPER `inactive/dead/disabled`, monitor service
  `inactive/dead/static`, monitor timer `inactive/dead/enabled`, every result
  `success`, zero restarts and a clean cloud repository on `27dacb3`.
- Closed First Strategy Candidate Pre-registration v1 as PASS without acquiring
  historical data, inspecting a result, optimizing a parameter or activating a
  runtime. The exact dataset SHA-256 lock is the next separate gate.

## 2026-08-23 — First Candidate Evaluation v1 (Rejected and Closed)
- Acquired and independently locked the exact 11,076-row BTC-USD and ETH-USD
  native six-hour datasets under manifest SHA-256
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`.
- Added and integrated the one-shot evaluation runner with fixed evidence paths,
  fail-closed staging, frozen-manifest enforcement, deterministic canonical JSON
  and structural prohibition of optimization, bounded forward PAPER and live
  authorization.
- Recorded the first execution's Pandas `Timestamp` serialization incident. No
  report, checksum, staging directory, outcome or performance value was
  persisted or printed. Added timestamp/scalar normalization and regression
  coverage without changing candidate identity, data, parameters, costs,
  thresholds, seed or protocol logic.
- Recovered the deterministic evaluation once and recorded canonical report
  SHA-256
  `6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c`
  in evidence commit `8978c72`.
- Closed the protocol outcome as `REJECTED`: baseline and stress each rejected
  both assets; no asset passed statistical falsification or the required 60%
  positive walk-forward excess rate. BTC/ETH supplied 11 windows and 75/74
  unseen walk-forward trades, but worst-profile OOS drawdown was 44.36% and
  57.22% against the frozen 20% maximum.
- Preserved all safety boundaries as false: bounded forward PAPER review
  eligibility, bounded forward PAPER authorization, optimization authorization
  and live execution authorization. Candidate v1 will not be mutated or rerun
  as unseen evidence.
- Authorized only a research-stage Timeframe Sensitivity Study v1 across 1h,
  6h and 1d BTC/ETH evidence. Any later candidate v2 must receive a new frozen
  identity and a separately locked unseen final-validation boundary; equity
  research remains a separate venue/calendar track.

## 2026-08-23 — Timeframe Sensitivity Study v1 (Local Preparation)
- Added a research-only declaration for fixed-order `1h`, `6h` and `1d`
  BTC/ETH comparison using the unchanged long-only EMA 20/50 implementation.
- Froze equal 720-day train and 180-day non-overlapping test/step durations:
  17,280/4,320 bars on 1h, 2,880/720 on 6h and 720/180 on 1d. The unchanged
  nominal periods intentionally represent different calendar EMA horizons.
- Prohibited candidate-v1 rerun. The six-hour evidence path accepts only the
  exact recorded report SHA-256
  `6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c`
  and rechecks its sidecar, identity, configuration, rejected outcome and
  authorization flags.
- Added distinct canonical 1h and 1d Coinbase contracts for 66,456 and 2,769
  continuous rows per asset. Extracted the already proven manifest, hash, grid
  and OHLCV validation into a reusable dataset lock while preserving the
  candidate-v1 lock behavior.
- Added one-shot canonical study evidence with pre-serialization and fail-closed
  staging. Each complete in-memory evaluation receives a SHA-256 before bounded
  compact persistence omits duplicated equity/trade arrays while retaining OOS,
  per-window, drawdown, trade, persistence and falsification metrics.
- Deliberately generated no score, ranking, winner or promotion outcome. All
  study history is development evidence; candidate-v1 reopening, candidate-v2
  authorization, optimization, bounded forward PAPER and live execution remain
  false.
- Added TDD for the new boundary; 196/196 focused research-stack tests and the
  complete 740/740 Python 3.12 suite pass locally. Windows reproduction, exact
  Git integration and separate 1h/1d dataset-lock evidence remain pending
  before any study execution.

## 2026-08-23 — Timeframe Study Windows Integration and 1h Acquisition Incident
- Windows/Python 3.14.6 reproduced the complete 740/740 suite, committed exact
  study revision `c39fd7c`, pushed it to `origin/main` and verified a clean tree
  before network acquisition.
- Acquired the native daily BTC/ETH development dataset with 2,769 rows per
  asset. Its canonical manifest SHA-256 is
  `77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691`;
  no evaluation ran.
- The first native one-hour attempt failed closed when the primary BTC response
  lacked 19 expected grid buckets. The builder wrote no one-hour CSV, manifest
  or checksum; the output directory was empty and no study/staging evidence
  existed.
- Recorded the incident as technical provider-data incompleteness. Added TDD for
  a bounded exact-gap recovery path: at most two passes and 100 exact-bucket
  requests per asset, with existing request retries, duplicate-conflict checks
  and full grid/OHLCV validation retained.
- Recovery never interpolates, forward-fills, resamples or synthesizes candles.
  Persistent gaps remain fatal with exact missing timestamp diagnostics. The
  recovery revision passes 202/202 focused research-stack tests and the complete
  746/746 local Python 3.12 suite. It must still pass focused/full Windows tests
  and commit/push review before the one-hour acquisition is retried.
  Candidate-v2, optimization, bounded forward PAPER and live authorization
  remain false.

## 2026-08-23 — Persistent 1h Provider Gaps and Schema-v2 Local Preparation
- Windows reproduced 23/23 focused dataset tests and the complete 746/746 suite,
  committed exact recovery revision `0b3e5bd` and pushed it before attempt 2.
- Attempt 2 repeated the complete BTC acquisition and two exact-bucket passes;
  all 19 gaps persisted with `recovery=exhausted_2_passes`. It wrote no one-hour
  CSV, manifest, checksum, study result or staging evidence.
- Independently queried the first gap through Exchange native 1h, Exchange
  native 5m and Advanced Trade native 1h views. Each returned zero rows inside
  the exact half-open interval; no real lower-timeframe row existed to derive
  the hour.
- Added a study-only sparse-native schema v2 without changing the continuous 6h
  candidate or 1d dataset locks. It permits at most 50 missing and 24 consecutive
  missing buckets per asset only after the frozen two-pass/100-request recovery,
  records every UTC gap and prohibits synthetic, interpolated, forward-filled or
  resampled candles.
- Added atomic two-asset acquisition and an independent sparse manifest lock for
  exact contract, hashes, counts, gap list, recovery status and OHLCV evidence.
- Added calendar-time 70/30 OOS and 720-day/180-day walk-forward boundaries.
  Missing rows cannot shift windows; a pre-gap signal executes only at the next
  provider-observed Open.
- Local validation passes 216/216 focused research-stack tests and the complete
  760/760 Python 3.12 suite. Windows reproduction and reviewed commit/push remain
  mandatory before attempt 3. All promotion and live authorizations stay false.

## 2026-08-23 — Timeframe Datasets Locked and Study Serialization Incident
- Windows exposed a Pandas index storage-unit difference in the calendar
  alignment check. Replaced raw `asi8`/nanosecond comparison with unit-neutral
  calendar flooring and added explicit microsecond-index regression coverage.
- Reproduced 30/30 focused and 761/761 complete Windows tests, committed/pushed
  sparse-native schema v2 as `b61853f`, then ran acquisition attempt 3.
- Atomically locked 1h BTC with 66,437 observed rows/19 explicit gaps and ETH
  with 66,438 observed rows/18 gaps; each longest gap is five hours. Manifest
  SHA-256 is
  `b9ba8126ca0612402919dd7f0f0096db2b2ef2f0a7d0669b6848276e88bc8157`.
- Rehashed every 1h/1d manifest and CSV, committed only the four manifests and
  sidecars as `e07b93e`, pushed them and verified clean one-shot preflight.
- Study attempt 1 failed during pre-staging compaction because one daily window
  carried the Performance Analyzer's legitimate `profit_factor=inf` state. No
  final report, checksum, staging evidence, aggregate outcome or comparison was
  persisted or printed.
- Added local schema-v3 evidence encoding: only positive infinite
  `profit_factor` becomes `POSITIVE_INFINITY_NO_LOSING_TRADES`, with exact count
  metadata. NaN, negative infinity and all other non-finite fields remain fatal.
  Frozen strategy/data/configuration and every authorization boundary are
  unchanged; Windows tests and commit/push are required before recovery.

## 2026-08-23 — Timeframe Sensitivity Study v1 (Completed and Closed)
- Reproduced schema-v3 recovery on Windows with 32/32 focused and 763/763 full
  tests, committed/pushed revision `8042816`, then verified absent final/staging
  evidence and a clean repository before deterministic recovery.
- Recorded canonical study report SHA-256
  `505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab`
  and committed/pushed it as evidence revision `cb43a74`.
- Closed all 1h, 6h and 1d baseline/stress aggregates as `REJECTED`; every one
  of 12 asset/profile views failed statistical falsification.
- One-hour losses/drawdowns reached 93.06%-97.90% despite extensive trade
  evidence. Six-hour BTC lost its positive absolute return under stress and
  retained drawdown above 44%; six-hour ETH remained deeply negative.
- Daily ETH produced relative development evidence (23.95/20.96 percentage-
  point excess and 7/11 baseline persistent windows), but absolute returns were
  -17.77%/-20.99%, stress persistence failed and falsification remained false.
  It is not a selected winner or promotion candidate.
- Verified schema-v3 encoding counts: two positive-infinite profit factors in
  daily baseline and two in daily stress, zero in 1h/6h, with all other
  non-finite evidence still rejected.
- Closed the study as `COMPLETED_NO_ROBUST_EDGE`. All history through 2026-08-01
  is now development evidence; candidate-v2 formal validation requires a new
  identity and independently locked future/unseen boundary. Optimization,
  PAPER and live authorization remain false.

## 2026-08-23 — Strategy Research Inventory v1 (Integrated)
- Inventoried exact default implementations for ADX, ATR breakout, Bollinger,
  Donchian, closed EMA crossover, MACD, RSI, Stochastic and Supertrend; retained
  the eight non-EMA entries as unevaluated research components.
- Added a deterministic synthetic-only integration audit for default parameters,
  declared features, input preservation, repeatability, valid signals, buy/sell
  activity and prefix causality. It invokes no market dataset or performance
  engine and generates no ranking.
- All nine implementations pass the local 720-row diagnostic. Counts remain
  integration evidence only and cannot support strategy selection.
- Added strict loading and fact extraction for only canonical Timeframe Study
  report SHA-256
  `505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab`;
  authorization/identity/hash or no-ranking drift fails closed.
- Froze next-hypothesis constraints around cost/turnover survival, bounded
  drawdown, explicit regime mechanism, baseline/stress retention, unseen future
  validation and no parameter leaderboard.
- Windows reproduced 180/180 focused strategy/inventory tests and the complete
  773/773 suite. Committed/pushed exact revision `53202c0`, then loaded the
  canonical study report through the non-evaluating CLI.
- Confirmed all nine implementations integration-ready. Only EMA carries a
  market result (`CLOSED_REJECTED_CANDIDATE_V1`); the other eight remain
  unevaluated, with no selected strategy or authorization change.

## 2026-08-23 — Strategy Family Screening Protocol v1 (Local Preparation)
- Froze a development-only scope containing exactly one default configuration
  for ADX, ATR breakout, Bollinger, Donchian, MACD, RSI, Stochastic and
  Supertrend; excluded the already rejected EMA candidate-v1 mechanism.
- Bound the future screen to the exact native BTC/ETH six-hour manifest SHA-256
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`.
  Six hours is an evidence-density working resolution, not a performance winner.
- Reused the exact 2,880/720/720 windows, 70/30 OOS split, seed, causal
  completed-Close/next-Open timing, baseline/stress costs and frozen evidence
  gates from candidate v1.
- Added a descriptive multiple-comparison guard: no score, ranking, tie-break,
  winner or formal validation claim; allowed per-strategy outcomes are only
  `SCREEN_OUT`, `MECHANISM_RETAINS_INTEREST` and `INCONCLUSIVE`.
- Added declaration and exact dataset locking without a performance runner.
  Both paths retain `screening_executed=false`; 15/15 new, 233/233 focused
  research/integration and 788/788 complete tests pass locally. Windows
  integration remains pending before a separately reviewed screening runner
  can exist.

## 2026-08-23 — Screening Protocol Integration and Runner Local Preparation
- Windows reproduced 15/15 protocol and 788/788 complete tests, committed and
  pushed exact revision `c7fc411`, then printed the non-executing declaration.
- Revalidated canonical 6h manifest SHA-256
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`
  plus 11,076 BTC and 11,076 ETH rows. Screening/performance execution remained
  false and the repository stayed clean.
- Added a separate one-shot runner for the exact eight strategies, baseline then
  stress, using 16 fixed multi-asset calls and no parameter/combination loop.
- Added fail-closed validation for manifest, configuration, asset scope, engine
  order/identity, declarations and validator classification evidence.
- Extracted shared bounded evidence compaction from Timeframe Study. Complete
  raw evaluations are hashed; persisted evidence omits trade/equity duplication,
  encodes only positive-infinite profit factor and rejects other non-finite data.
- Implemented pre-registered `SCREEN_OUT`, `MECHANISM_RETAINS_INTEREST` and
  `INCONCLUSIVE` gates without score, ranking, tie-break or selected strategy.
- Completed 19/19 new runner, 37/37 runner/timeframe regression and 807/807 full
  local tests. Windows reproduction, exact commit/push and absent-evidence
  preflight remain required before the single development-screen execution.

## 2026-08-23 — Strategy Family Screening v1 (Executed and Closed)
- Windows reproduced 37/37 focused runner/timeframe tests and the complete
  807/807 repository suite, committed/pushed exact runner revision `e8afe12`
  and passed clean preflight with matching manifest/study hashes and absent
  final/staging evidence.
- Executed the frozen development matrix exactly once: eight standalone default
  strategies, baseline then stress, for 16 multi-asset evaluations and 32
  BTC/ETH asset/profile views. No parameter loop, combination, score, ranking or
  automatic selection executed.
- Recorded canonical report SHA-256
  `9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f`
  and sidecar under evidence revision `2973636`, pushed to `origin/main`.
- Closed ADX 14/25, ATR breakout 14/1, Bollinger 20/2, Donchian 20, MACD
  12/26/9, RSI 14/30/70, Stochastic 14/3/20/80 and Supertrend 10/3 as
  `SCREEN_OUT` in their exact standalone frozen configurations. Baseline and
  stress aggregates are `REJECTED` for every strategy.
- All 32 asset/profile views have negative absolute OOS return and fail
  statistical falsification. OOS drawdown ranges from 40.32% to 93.71%, so
  every strategy also fails the frozen 20% drawdown gate. Required window and
  unseen-trade evidence-volume gates pass.
- Generated zero `MECHANISM_RETAINS_INTEREST` and zero `INCONCLUSIVE` outcomes.
  Candidate v2, optimization, bounded-forward-PAPER and live authorizations all
  remain false.
- Scoped the conclusion to the tested artifacts: the screen rejects deployable
  standalone default variants, not their indicator families as potential
  features, regime filters or components. It does not establish that systematic
  trading is impossible.
- Moved the next research boundary to controlled alpha discovery: first
  attribute signal/cost/turnover/regime failure, then freeze a bounded
  train/validation calibration and combination procedure that mirrors intended
  live behavior. Existing inspected history remains development-only.

## 2026-08-24 — Failure Attribution and Volume Protocol v1 (Local Preparation)

- Added a causal, scale-independent volume research layer with a frozen lagged
  trailing-median baseline, per-asset relative volume, relative dollar volume,
  OBV and LOW/NORMAL/HIGH volume regimes.
- Required signal-bar attribution through `entry_signal_index`; the following
  execution bar cannot supply market or volume context to the decision that
  preceded it.
- Froze volume as mandatory evidence for the next alpha hypothesis while
  explicitly rejecting raw BTC-versus-ETH volume comparison and any claim that
  candle volume substitutes for live spread, depth or market impact.
- Added a strict loader for only screening report SHA-256
  `9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f`
  and its canonical sidecar, including exact dataset, strategy scope, eight
  closed outcomes and authorization state.
- Froze zero-cost, baseline and stress diagnostic profiles plus gross/cost,
  turnover, exposure, holding, drawdown, benchmark, walk-forward, market-regime
  and volume-regime axes. Zero cost is diagnostic only.
- Added declaration and evidence-lock paths without a performance runner or
  evidence write. Ranking, result-driven tuning, combinations, candidate v2,
  optimization, PAPER and live execution remain prohibited.
- Local TDD passes 36/36 new volume/attribution tests and the complete 843/843
  repository suite. Windows reproduction and integration remain pending.

## 2026-08-24 — Failure Attribution Runner v1 (Local Preparation)

- Added a one-shot 8-strategy by 3-profile runner for exactly 24 multi-asset
  diagnostic replays and 48 BTC/ETH asset/profile views.
- Reused the causal next-Open multi-asset validation stack under zero, baseline
  and stress costs; zero cost remains explanatory rather than deployable.
- Added fail-closed raw OOS attribution for gross/net P/L, commission,
  spread/slippage, turnover, exposure, holding periods and drawdown
  peak/trough/recovery plus yearly concentration.
- Extended the causal volume layer with relative dollar-volume and OBV-direction
  trade context while retaining per-asset normalization and signal-bar timing.
- Added descriptive cross-profile changes and failure flags without a score,
  ranking, tie-break, selected strategy or automatically generated hypothesis.
- Hashes every complete normalized raw evaluation, persists bounded compact
  evidence and requires all computation to finish before atomic staging/rename.
  Existing final or staging evidence prevents repetition.
- Candidate v2, optimization, bounded forward PAPER and live execution remain
  false; cloud infrastructure is unchanged and parked.
- Local TDD passes 59/59 focused volume/protocol/metrics/runner tests and the
  complete 866/866 repository suite. Windows integration remains pending.

## 2026-08-24 — Strategy Failure Attribution v1 (Executed and Closed)

- Windows reproduced 59/59 focused volume/protocol/metrics/runner tests and the
  complete 866/866 suite, committed/pushed runner revision `334ceba` and passed
  a clean preflight with matching manifest/screening evidence plus absent final
  and staging output.
- Executed the exact eight-strategy by zero/baseline/stress matrix once: 24
  multi-asset replays and 48 BTC/ETH asset/profile views. Recorded canonical
  report SHA-256
  `e4193bff907a2121701e7ddc1d740894641c7bf427c9501fd4ecd4392a1f81f4`
  under pushed evidence revision `f189689`.
- Confirmed nine of sixteen positive zero-cost OOS views but zero positive
  baseline/stress views. Baseline cumulative modeled costs span 1,488.68 to
  5,274.93 and round-trip turnover spans 42.53x to 150.71x initial capital.
- Retained universal baseline/stress drawdown-limit, walk-forward-persistence
  and statistical-falsification failures. The result attributes failure to a
  combination of unfiltered turnover/cost destruction, drawdown and temporal
  instability rather than declaring every raw mechanism information-free.
- Identified the strongest cross-asset development slice: ADX with `HIGH`
  per-asset relative volume retains baseline P/L of 1,850.49 over 25 BTC trades
  and 763.89 over 21 ETH trades. ADX in `BULLISH_NORMAL` market regime is also
  positive after baseline costs for both assets.
- Kept OBV descriptive: falling-OBV ADX views lose for both assets; rising OBV
  remains positive after costs only for ETH and cannot be promoted as a
  standalone cross-asset gate.
- Prohibited adding marginal regime/volume profits or treating their untested
  intersection as validated. Moved next work to a bounded Alpha Development
  Protocol v2 with joint causal conditions, mandatory volume, risk/turnover
  controls, temporal calibration and reviewed venue/execution profiles.
- Generated no ranking, automatic strategy selection, candidate v2,
  optimization, PAPER or live authorization. Cloud services remain parked.

## 2026-08-24 — Alpha Development Protocol v2 (Local Preparation)

- Converted the closed failure diagnosis into three fixed causal ablations:
  ADX plus high relative volume; that mechanism plus `BULLISH_NORMAL`; and an
  optional rising-OBV interaction. No grid, rank or hindsight winner exists.
- Added a reusable joint strategy component with ADX 14/25 entries, ADX 20 exit
  hysteresis, four-bar cooldown, mandatory lagged relative-volume confirmation,
  signal-bar two-ATR risk distance and intended 3:1 reward/risk.
- Froze 0.50% risk per position, 50% maximum position size, no leverage or
  shorting, 20% drawdown, daily/weekly new-risk limits and annual turnover/cost
  budgets before any performance evidence.
- Recorded Coinbase baseline/stress and a dated Kraken Pro $10k-volume taker
  sensitivity. The maker scenario is present but blocked pending causal
  placement, non-fill and partial-fill evidence plus current account-tier
  revalidation.
- Exposed a critical execution prerequisite: current Stop/Target annotations do
  not actively exit positions. A separately reviewed protective-fill engine
  must implement conservative intrabar/gap semantics before a v2 runner.
- Added strict canonical loading for Failure Attribution report SHA-256
  `e4193bff907a2121701e7ddc1d740894641c7bf427c9501fd4ecd4392a1f81f4`
  and its exact ADX regime/volume/OBV hypothesis basis.
- Declaration and evidence-lock paths perform no performance evaluation,
  calibration, optimization or promotion. Candidate v2, PAPER and live remain
  false; cloud services remain parked.
