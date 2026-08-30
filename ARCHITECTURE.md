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

# Strategy Evaluation Protocol v1 Contract

Strategy Evaluation Protocol v1 is a research-governance layer above the
existing Strategy Validation Pipeline and Multi-Asset Validator. It does not
create indicators, optimize parameters, change signals, size positions or send
orders. Its only promotion target is a later bounded forward-PAPER candidate.

Every evaluation begins with an immutable candidate declaration containing a
candidate ID, exact Strategy Engine name, written hypothesis, parameter-set ID,
data version, timeframe and a fixed named-asset scope. The same engine,
chronological split sizes, non-overlapping walk-forward test windows, random
seed and asset scope are used for both evaluation passes. A strategy-name or
asset-scope mismatch is an evidence-integrity failure, not a result that may be
silently normalized.

Execution assumptions are explicit inputs rather than zero-cost defaults. The
baseline cost profile must be nonzero and reviewed for the intended venue. The
cost-stress profile may not lower commission, slippage or spread, and at least
one component must be strictly higher. Both passes independently retain each
asset's OOS, benchmark, walk-forward and statistical-falsification evidence.

Research execution timing is also an explicit integrity boundary. A strategy
signal produced from a completed bar may observe that bar's close, but the
formal protocol may execute it only at the following bar's open. The execution
bar and originating signal bar are both retained in trade evidence. A signal
from the final dataset bar has no attainable next-bar price and is therefore
never executed. An already-open terminal position is closed at the final close
under the frozen `force_close_at_final_close` reporting policy, with no
synthetic exit signal attributed to the strategy.

The general Backtesting Engine keeps `same_bar_close` as its legacy default so
existing replay and paper-consistency contracts do not change implicitly.
Strategy Evaluation Protocol v1 rejects that mode and requires
`next_bar_open`. Its buy-and-hold benchmark enters at the first bar's open and
exits at the final close. The same timing choice is propagated unchanged
through OOS, walk-forward, validation-pipeline and multi-asset layers for both
baseline and stressed-cost passes. This prevents final-close knowledge from
being converted into an unattainable fill while preserving explicit backward
compatibility outside governed candidate evaluation.

The initial configurable promotion gates are:

- baseline multi-asset classification must be `VALIDATED`
- cost-stress multi-asset classification must also be `VALIDATED`
- each asset must supply at least five non-overlapping walk-forward test windows
- each asset must supply at least 30 completed unseen walk-forward trades
- the maximum unseen OOS drawdown under either cost profile must not exceed 20%

These are versioned research thresholds, not calibrated live-risk limits. A
hard edge failure or identity/scope violation returns `REJECTED`. Evidence that
has not failed but lacks one or more promotion gates returns `RESEARCH_HOLD`.
Only complete evidence returns `PAPER_CANDIDATE`, with next stage
`BOUNDED_FORWARD_PAPER` and `live_execution_authorized=False` invariant in
every outcome. The separate three-day infrastructure gate must pass before the
first candidate evaluation is operationally promoted; this protocol cannot
override that boundary.

## Exploratory Timeframe Sensitivity Boundary

Timeframe Sensitivity Study v1 is intentionally outside formal candidate
promotion. It compares the unchanged long-only EMA 20/50 implementation on
native Coinbase `1h`, `6h` and `1d` BTC/ETH candles over the same historical
range. Equal 720-day train and 180-day non-overlapping test/step durations keep
the amount of market time comparable while the same nominal 20/50 bar periods
expose different calendar horizons.

The rejected six-hour candidate is never rerun. Its exact canonical report and
checksum are revalidated and reused as reference evidence. One-hour and daily
datasets receive distinct canonical contracts, hashes and independent locks,
then run through the same baseline/stress Multi-Asset Validation stack with the
frozen causal execution, cost, seed and falsification assumptions.

The daily lock remains continuous. Coinbase's native one-hour history contains
persistent provider gaps even after two exact-bucket recovery passes. The
study-only schema-v2 one-hour boundary therefore stores only observed native
candles and binds every missing UTC bucket in the manifest. It permits at most
50 missing and 24 consecutive missing buckets per asset; interpolation,
forward-fill, resampling and synthetic OHLCV remain prohibited. Both assets are
fully fetched and validated before atomic one-shot persistence.

One-hour OOS and walk-forward partitions use expected-grid UTC boundaries, not
observed row positions. The 70/30 split and expanding 720-day train plus
non-overlapping 180-day test windows therefore remain calendar-equivalent across
assets even when their missing timestamps differ. Within each partition,
next-bar-Open means the next provider-observed candle; an absent bucket can
never carry an execution.

The study report preserves complete evidence and a fixed-order metric summary,
but emits no score, ranking, winner or promotion decision. All inspected history
is development evidence. A later formal candidate requires a new identity and a
separately locked unseen final-validation boundary; no study result can reopen
candidate v1 or authorize optimization, bounded forward PAPER or live trading.

Canonical study evidence remains strict JSON. Study schema v3 maps only the
Performance Analyzer's defined positive-infinite `profit_factor` state (wins
with no losing P/L) to `POSITIVE_INFINITY_NO_LOSING_TRADES` and records an
occurrence count per compact evaluation. NaN, negative infinity and non-finite
values under every other key still fail before staging. The encoding is an
evidence representation rule, not a metric cap, score or strategy-policy
change.

## Strategy Research Inventory Boundary

The post-study inventory treats every existing strategy class as a research
component rather than a trading candidate. EMA crossover retains its closed
candidate-v1 status; ADX, ATR breakout, Bollinger, Donchian, MACD, RSI,
Stochastic and Supertrend remain formally unevaluated. Registration, feature
generation and signal tests do not imply profitability or promotion readiness.

A deterministic synthetic integration audit may verify default construction,
feature declarations, immutable input, repeatability, signal domain, diagnostic
buy/sell activity and prefix causality. It never invokes market performance,
Backtesting, Multi-Asset Validation or ranking. Synthetic signal counts are
connectivity evidence only.

Recorded failure-mode extraction accepts only the exact closed Timeframe Study
report and validates its canonical hash, sidecar, identity, no-ranking policy
and false authorization flags. It retains observed returns, drawdowns, trade
counts, persistence and falsification facts without recalculating a strategy or
selecting a successor. Any later family screening must receive a separate
pre-registered scope and multiple-comparison boundary before execution.

## Strategy Family Screening Pre-registration Boundary

Strategy Family Screening Protocol v1 freezes one development-only comparison
before any of its performance results exist. It excludes the closed EMA 20/50
mechanism and permits exactly one explicit default configuration for ADX, ATR
breakout, Bollinger, Donchian, MACD, RSI, Stochastic and Supertrend. Each entry
is bound by a deterministic name/family/mechanism/parameter fingerprint;
parameter variants and indicator combinations are outside the experiment.

The shared data identity is the already canonical native BTC/ETH six-hour
manifest SHA-256
`6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`.
Six hours is a fixed working resolution because it balances development
evidence density between recorded one-hour turnover failure and daily low trade
density. It is not a selected winner. The entire range through 2026-08-01 is
explicitly inspected development evidence.

All eight paths must reuse the same 2,880/720/720 expanding windows, 70/30 OOS
split, seed, completed-Close/next-Open timing, terminal-close policy,
baseline/stress costs, evidence-volume gates and 20% drawdown limit. The
multiple-comparison policy is descriptive: no score, ranking, tie-break,
winner or formal validation claim is allowed. Per-strategy outcomes are limited
to `SCREEN_OUT`, `MECHANISM_RETAINS_INTEREST` and `INCONCLUSIVE`.

Declaration and dataset lock do not import or invoke a screening runner. They
only validate immutable identity and return
`screening_executed=False`. A retained mechanism, if any, can support writing a
new hypothesis but cannot authorize candidate v2, optimization, bounded forward
PAPER or live execution. Formal candidate-v2 evidence requires a new identity
and separately locked genuinely unseen future data.

## Strategy Family Screening One-Shot Evidence Boundary

The separately reviewed runner consumes only the locked screening object. It
verifies exact manifest, configuration, asset scope, eight-strategy order,
engine names and declaration fingerprints before constructing any validator.
It then invokes the unchanged `MultiAssetValidator` exactly twice per strategy:
baseline followed by stress, yielding a fixed 16-run matrix without a parameter
or combination loop.

Research evidence compaction is shared with Timeframe Sensitivity Study. Each
complete raw evaluation is canonicalized and hashed in memory; persisted
evidence omits duplicated trade histories/equity curves while retaining OOS,
benchmark, drawdown, walk-forward, unseen-trade and falsification evidence. Only
defined positive-infinite profit factor is explicitly encoded. All other
non-finite values fail before persistence.

The per-strategy gate review implements the pre-registered three outcomes and
fixed-order comparison. It emits no score or ranking and leaves
`selected_strategy=None`. All evaluations and canonical final serialization
must finish before a staging directory is created. Report and SHA sidecar are
written under `.screening_v1.staging` and atomically renamed; existing final or
staging evidence blocks repetition.

The recorded report is inspected development evidence only. A retained-interest
mechanism is not a selected candidate and cannot authorize candidate v2,
optimization, PAPER or live execution.

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
`src/forward_session_report.py` is a read-only evidence layer over the append-only forward JSONL audit. It selects only the latest complete `SESSION_START` -> `SESSION_END` block and fails closed on malformed or incomplete boundaries. The reporter never touches transport, strategy, risk or broker execution. `audit_complete` means the boundaries/counts reconcile and all recorded real-order evidence remains zero; gate `PASS` additionally requires `SESSION_END reason=MAX_BARS`. A structurally complete operator stop or fatal termination is therefore measurable but cannot be promoted into a successful endurance run.

### Coinbase Late-Trade Ordering Robustness v2
Extended forward observation exposed event-time reordering across separate Coinbase websocket messages. Add a bounded 2-second event-time reorder buffer before strict minute aggregation, persist the pending buffer in forward continuity state, and keep truly late trades fail-closed after the watermark. This adds a small intentional bar-finalization delay to preserve OHLCV correctness rather than silently dropping late trades.

- Completed-bar freshness semantics: adapters may define `freshness_reference(timestamp, timeframe)`; Coinbase completed 1m bars are aged from interval close, while timestamp ordering remains anchored to interval start.

## Coinbase Provider Message Sequence Integrity v1
The Advanced Trade `market_trades` envelope is validated at the websocket
transport boundary before any contained trade can enter event-time buffering or
OHLCV aggregation. The connection-local `sequence_num` contract is distinct
from trade event time: the first valid non-negative integer establishes the
socket baseline and each subsequent accepted message must increment it by
exactly one.

A lower or equal sequence is a provider message replay/out-of-order delivery
that Coinbase documents as ignorable. The entire envelope is dropped before
aggregation and emitted as the typed internal control event
`PROVIDER_MESSAGE_REPLAY_DROPPED`; append-only audit retains previous/observed
sequence, provider message time, trade count and bounded first/last `trade_id`
evidence. It never reaches Feed Health, Strategy, Risk or PaperBroker and is not
itself an operational alert.

A forward sequence gap, missing sequence or invalid sequence is an integrity
failure before payload consumption. The socket is closed, the cause is
classified as `PROVIDER_SEQUENCE_GAP`, `PROVIDER_SEQUENCE_MISSING` or
`PROVIDER_SEQUENCE_INVALID`, and the existing bounded transport reconnect path
owns recovery. Forward PAPER discards the untrusted partial aggregation
boundary. A completed minute that began before the reconnected socket's first
trusted full-minute boundary is audit-dropped rather than traded; that minute is
then reconstructed by exact non-tradable REST recovery when the first fully
observed live bar arrives. The report exposes these events separately as
`sequence_boundary_drops`. Only that later live bar may resume normal decisions. Reconnect exhaustion still
closes the session as `TRANSPORT_FATAL`. Sequence state is never checkpointed
across sockets because a new connection establishes a new provider baseline.
After a sequence-integrity failure, heartbeats alone do not reset the consecutive
recovery budget or declare the market feed reconnected; that requires a validly
sequenced `market_trades` payload on the new socket.

The two-second event-time watermark remains independently enforced for payloads
whose message sequence is valid. A genuine late trade therefore still raises
`CoinbaseTradeOrderingError`; its diagnostics now also retain `trade_id`,
message `sequence_num`, provider message timestamp and event type. Provider
sequence handling does not widen the event-time window, fabricate candles,
change Strategy/Risk/Paper behavior or add real-execution capability.

Official provider contract:
[Advanced Trade WebSocket sequence numbers](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview#sequence-numbers)
and
[market trades channel](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-channels#market-trades-channel).

## Coinbase Transport Resilience v1
`CoinbasePublicWebSocketTransport` now emits explicit internal transport-control events around reconnects while preserving the public market-data contract. Reconnect attempts are bounded per consecutive outage and reset after the reconnected socket successfully delivers data; healthy periods therefore do not consume a lifetime reconnect budget.

A disconnect invalidates the in-progress Coinbase aggregation boundary because trades may have been missed while the socket was unavailable. `CoinbaseOneMinuteTradeAggregator.reset_stream_boundary()` discards only partial/pending aggregation state. After reconnect, Forward Paper marks the next fresh excessive-gap completed bar as a non-tradable reconnect rebase, then resumes normal Feed Health enforcement on subsequent bars. Account, Risk Engine and strategy history remain intact.

Forward audit now records `TRANSPORT_EVENT` and `RECONNECT_REBASE` evidence. A safety halt caused by repeated Feed Health failures is reported as `RUNTIME_HALTED`, not mislabeled as `TRANSPORT_ENDED`.

### Transport-failure boundary
Coinbase reconnect uses bounded exponential backoff. Exhaustion emits a terminal transport event; forward-paper checkpoints continuity and closes the append-only session audit with `TRANSPORT_FATAL` instead of allowing a transport exception to leave an incomplete session.


## Reconnect Replay Reconciliation v1
- Completed Coinbase bars at or behind the already-accepted feed watermark are classified as provider replay and dropped before the trading/Feed Health pipeline.
- Replay drops remain audit-visible (`PROVIDER_REPLAY_DROPPED`) but do not consume the operational runtime consecutive-failure budget.
- Fresh forward bars still pass through strict freshness, ordering and missing-gap validation; real execution remains impossible.
- This change targets the observed 10:25 -> 10:23 -> 10:24 replay sequence that previously caused a false `RUNTIME_HALTED` during the supervised 30-bar run.

## Forward Operational Diagnostics
`forward_session_report` is the read-only observability boundary for supervised forward operation. It derives transport reliability, provider replay, market-time continuity/gap and signal/risk activity metrics solely from append-only forward audit evidence. It must not mutate runtime, strategy, Risk Engine, Feed Health or execution state.

## Target 24/7 Market-Universe Architecture (Deferred Scale Boundary)

`BTC-USD` is the current live-paper proving instrument, not a permanent single-asset architecture. The future scale boundary is:

`Universe Manager -> Lightweight Scanner -> Candidate Ranking -> Strategy/Regime Deep Analysis -> Risk Engine -> Portfolio Gate -> Execution Adapter`

The Universe Manager owns configured instrument/venue scope and market-session awareness. The Scanner performs inexpensive broad filtering; Candidate Ranking bounds downstream computational work; only shortlisted instruments reach full strategy/regime analysis. Risk remains independent from signal generation, and a future Portfolio Gate adds aggregate multi-position exposure/concentration/correlation controls before execution.

The Agent process may operate continuously while respecting each venue's actual trading calendar. Crypto can be scanned continuously; exchange-traded instruments are activated/deactivated according to their sessions rather than treated as 24/7 markets.

This boundary is intentionally deferred until single-symbol live-paper transport, continuity and long-duration operational quality are proven. Broadening the universe must reuse provider-neutral market-data and execution contracts rather than embedding symbol/provider assumptions into Strategy or Risk layers.

## Hybrid Market-Data Continuity Boundary

The production-oriented Coinbase path is now explicitly hybrid:

`WebSocket live trades -> event-time reorder -> completed 1m bars`

`disconnect/restart gap -> public REST 1m candles -> exact continuity validation -> non-tradable state catch-up -> next live bar resumes normal trading`

WebSocket remains the low-latency source. REST is a recovery/backfill source only. Historical recovery bars advance provider/feed watermark, accumulated strategy input history, broker mark price and Risk Engine equity observation, but they do **not** invoke Strategy/Risk/Execution orchestration retroactively. This prevents a delayed historical BUY/SELL signal from becoming a current paper/live order.

Recovery is exact and fail-closed. Every expected missing minute must be present; candles are never fabricated. Recovery gaps above the configured safety bound or incomplete REST responses stop the session with `BACKFILL_FATAL` and preserve continuity state. The provider-neutral trading layers remain unaware of whether a bar originated from WebSocket or REST recovery.

Reconnect-boundary recovery is stricter than the normal live-feed `max_gap` tolerance. At a transport/restart boundary, any first-live timestamp jump greater than the configured timeframe requires exact REST recovery of every intervening minute. In particular, `last accepted=11:33` followed by `first live=11:35` means `11:34` is missing and must be recovered before `11:35` may trade. This prevents a one-minute hole from being silently accepted merely because the live Feed Health tolerance allows a two-minute timestamp delta.

## Startup Historical Catch-up Boundary v1
Long process downtime is distinct from an in-session WebSocket outage. On resume, the persisted feed watermark defines the start of a startup-only historical catch-up. Coinbase REST 1m candles are fetched through the existing per-request chunking, validated for exact minute coverage, and ingested as non-tradable state catch-up. Strategy history, feed continuity, risk observations and mark-to-market state advance; order generation is forbidden for historical bars. Only the subsequent fresh live bar may re-enter the normal Strategy -> Risk -> Paper execution path. Normal reconnect recovery keeps its tighter 300-minute limit; startup catch-up has a separate bounded default of seven days and fails closed beyond it or on incomplete coverage.

## Post-Recovery Position Reconciliation
Historical REST/startup catch-up bars are state-reconstruction inputs, never execution events. Strategy state is nevertheless evaluated after each recovered bar. If an actionable bearish transition occurs while a long paper position exists, the forward runtime records a durable pending `LONG_EXIT` reconciliation in continuity state. No order is submitted at the historical timestamp. On the first subsequently accepted fresh live bar, the normal paper stack observes current equity and executes the exit at the current live bar price/time, then clears the pending marker. Audit records separately identify detection and live reconciliation. This closes the event-loss gap between event-based crossover semantics and non-tradable recovery while preserving the no-retroactive-trading invariant.

## Risk/Reward Numerical Decision Boundary
Risk Engine remains the sole owner of minimum reward/risk authorization. Planned reward/risk is computed from validated market prices as `(target - entry) / (entry - stop)`. Threshold equality uses a fixed relative tolerance of `1e-12` solely to neutralize binary floating-point representation error at an otherwise exact configured boundary. The tolerance is not applied to stop/target validity, sizing, exposure caps or any other risk rule; a meaningfully sub-threshold ratio remains `REJECT`.

`PaperTradingEvent` carries the Risk Engine decision evidence for evaluated BUY signals: planned entry, stop, target, computed reward/risk ratio and configured minimum. The append-only forward audit serializes this event unchanged, and `forward_session_report` derives read-only reward/risk counts and ranges from that evidence. Reporting must never recompute, normalize or override the original Risk Engine decision.

## Operational Monitoring & Alerting Boundary v1
`src/operational_monitoring.py` is a read-only operational decision layer over the append-only forward audit and atomic forward continuity state. It does not import the live runtime composition, generate strategy signals, assess trade risk, repair market data, submit orders, restart processes or mutate operational artifacts.

The monitor converts existing evidence into `OK`, `WARNING` or `CRITICAL` plus stable alert codes. Critical conditions include missing/unreadable/stale required evidence for a running session, fatal runtime/recovery/transport termination, explicit REST backfill failure, non-zero REAL-order evidence and an active Risk Engine kill switch. Current disconnect and pending position reconciliation remain warnings unless stronger evidence makes the report critical. CLI exit codes are `0`, `1` and `2` respectively so an external watchdog can act without reimplementing policy.

Every new forward audit record carries `recorded_at`; every new forward continuity state carries `saved_at`. These are operational observation timestamps, distinct from market-event time. Historical artifacts without the new checkpoint timestamp fall back to file modification time for backward-compatible inspection.

Notification delivery and process supervision are outside this boundary. Future email/Slack/SMS adapters, cloud health checks, schedulers or service managers consume the monitoring report/exit code. They must not embed duplicate trading or alert-classification rules.

## Cloud Runtime Readiness Boundary v1
`src/cloud_readiness.py` is a provider-neutral, pre-deployment validation boundary. It consumes explicit environment configuration and emits a deterministic PASS/FAIL report before any cloud paper process is allowed to start. It does not import provider SDKs, provision infrastructure, start the forward session, submit orders or mutate trading state.

The gate requires PAPER mode with real execution explicitly disabled, a bounded session, a valid monitor/staleness cadence, distinct audit and continuity files in one absolute persistent runtime directory, writable storage, importable runtime/monitoring components and Python 3.12-3.14. Storage validation is limited to a temporary write/read/cleanup probe and is not attempted until path validation passes. Human-readable and JSON reports share the same checks; exit codes are `0=PASS` and `2=FAIL` for later service-manager deployment gates.

Provider selection, container/service orchestration, secrets delivery, notification adapters and cloud transport behavior remain outside this boundary. Those deployment concerns may consume the readiness result but must not duplicate or weaken its execution-lock and persistence requirements.

## Controlled Cloud Host Boundary v1
The first provider-specific validation environment is one Hetzner CPX22 instance in the Nuremberg EU location, running Ubuntu 24.04 LTS on x86. This is an operational test host, not a new dependency of the trading architecture: Strategy, Risk, Feed Health, recovery, monitoring and reporting remain unaware of the infrastructure provider.

Host access uses a dedicated passphrase-protected ED25519 SSH key. A provider firewall permits only SSH and ICMP as new inbound traffic; required outbound connections remain available for package repositories, DNS and the public Coinbase WebSocket/REST paths. No application port is publicly exposed. The initial image is security-updated and reboot/reconnect validated before code deployment.

Repository regression tests must be hermetic at the deployment boundary. Test inputs needed by committed tests must be generated in memory or committed under an explicit test-fixture policy; they must not depend on ignored workstation artifacts such as `data/AAPL.csv`. A cloud deployment is eligible to start only from an exact committed revision whose full suite passes in a clean clone, followed by the same full suite and Cloud Runtime Readiness gate on the target host.

## Cloud Service Supervision Boundary v1
`deploy/systemd/` is a provider-host adapter around the existing provider-neutral runtime, readiness and monitoring entrypoints. The bounded paper service runs as the passwordless/non-login `ai-alpha` system identity, never as `root`, with reviewed fixed values for PAPER mode, real execution disabled, a root-controlled bounded-session configuration and `/var/lib/ai-alpha` audit/state persistence. `src.cloud_readiness` is an `ExecStartPre` gate, so an unsafe or unwritable configuration prevents the forward process from starting. The service may write only its private state directory; project and operating-system paths remain read-only.

Unexpected process failure uses `Restart=on-failure`; normal `MAX_BARS` completion does not restart. One reviewed activation is bounded to two total starts across an infinite rate-limit interval: the initial start plus at most one automatic recovery start. A fresh budget is opened by an explicit guarded `systemctl reset-failed` while inactive. If systemd has already garbage-collected the successful inactive unit, its start-rate counters have also been flushed; only the exact unit-not-loaded result may proceed after the installed unit file is verified loadable. Every other reset error blocks activation. Operator stop/restart is delivered as `SIGINT`, and the next process consumes the existing atomic continuity state. The read-only forward report exposes the latest session's `resumed` boundary so restart evidence is deterministic rather than inferred from console output.

Operational Monitoring remains the sole alert-classification policy. A separate oneshot service invokes it every minute through a persistent systemd timer and records readable output in journald. `OK` and `WARNING` remain non-critical service outcomes, while the existing `CRITICAL` exit code marks the monitoring unit failed. The timer cannot start or restart trading, and the installer deliberately performs no service activation. Notification delivery, escalation and unattended boot-time paper activation remain deferred adapters.

## Bounded Cloud Session Configuration v1
The committed `deploy/systemd/ai-alpha-paper.env` is the single source for the cloud PAPER session bar bound and is installed as root-owned configuration under `/etc/ai-alpha`. The systemd unit imports that value before `ExecStartPre`, allowing Cloud Runtime Readiness to fail closed on a missing or invalid bound, and passes the identical value to the forward runner through `--bars`. This removes the prior duplicated ten-bar literals without moving duration policy into Strategy, Risk, recovery or execution logic.

The current reviewed bound is 4,320 completed one-minute bars, exactly three days of fresh cloud evidence. Progression to this duration is authorized by the successful 1,440-bar gate and changes only the root-owned session bound; market-data handling, Strategy, Risk, recovery and execution behavior remain unchanged. The PAPER service remains boot-disabled and real execution remains explicitly false. Longer bounds require another reviewed repository change and successful shorter-gate evidence; they are not authorized by ad hoc host edits.

The three-day gate is an endurance observation, not another injected-failure test. A clean pass requires normal `MAX_BARS` completion with 4,320/4,320 processed bars, zero rejected bars, complete audit, exact market-time continuity, no recovery failure or reconnect exhaustion, 100% reconnect success when disconnects occur, systemd `Result=success`, `ExecMainStatus=0`, `NRestarts=0`, final Operational Monitoring `OK` with no alerts and `REAL_orders=0`. Existing hybrid recovery may repair transient transport gaps, but all outage/reconnect and provider-boundary evidence remains visible. Final CPU time, memory peak and swap/OOM evidence are retained for resource-growth review. An unexpected process incident, automatic restart or monitoring warning/critical result prevents the run from being classified as a clean three-day pass. Passing remains infrastructure endurance evidence rather than strategy profitability proof or unattended-production authorization.

## Restart Incident Visibility Boundary v1
The systemd PAPER adapter invokes `src.process_incident` through `ExecStopPost`. systemd supplies the authoritative service result and main-process exit evidence through `SERVICE_RESULT`, `EXIT_CODE` and `EXIT_STATUS`. The adapter appends one `PROCESS_INCIDENT` record only when the result is not explicitly `success`; missing lifecycle evidence is recorded as unknown rather than assumed healthy. The recorder uses only Python standard-library persistence, never imports the trading runtime and never reads or mutates continuity state.

`ExecStopPost` is prefixed with systemd's failure-ignore command marker. This is deliberate separation of responsibility: incident persistence may add evidence but may not turn a clean PAPER completion into a failure, trigger a restart, suppress the original failure result or replace the existing rate-limited `Restart=on-failure` policy. Recorder failure remains visible in journald and existing stale/missing evidence checks, but cannot control trading lifecycle.

Operational Monitoring remains the sole alert-classification boundary. A `PROCESS_INCIDENT` after the latest `SESSION_START` changes operator state to `FAILED` and severity to `CRITICAL`. When no stronger audited terminal cause exists its end reason is `PROCESS_FAILURE`; an explicit fatal `SESSION_END`, such as `ORDERING_FATAL`, remains the reported root cause while the systemd incident is also visible. If the immediately previous session contains the incident and systemd has started a new session, the current session retains a `PREVIOUS_PROCESS_FAILURE` warning even when it later completes with `MAX_BARS`. The warning naturally clears only when another session starts after one incident-free recovery session; the append-only incident itself remains permanent audit evidence.

This boundary addresses process-failure visibility only. It does not widen Coinbase trade-reordering tolerance, reinterpret out-of-order data, alter Feed Health, recovery, Strategy, Risk Engine or PaperBroker behavior, and it does not add real execution capability.

## Overnight Soak Failure Closure Boundary v1
The two-second Coinbase event-time reorder watermark remains a correctness boundary, not a tuning knob. A trade whose minute is older than the active aggregation minute raises `CoinbaseTradeOrderingError`. The error carries its event timestamp, minute bucket, active bucket, latest-seen event timestamp, watermark, configured window and seconds beyond that watermark. Forward PAPER persists the same fields as `LATE_TRADE_REJECTED`, checkpoints continuity, closes the attempt with `ORDERING_FATAL` and re-raises so systemd retains failure/restart ownership. No late trade is dropped, reordered beyond policy or passed to Strategy/Risk/Execution.

SIGINT is a separate planned lifecycle boundary. The public runner records how many session starts existed before the invocation; only a newly opened, still-unclosed attempt may be finalized as `OPERATOR_STOP`. The terminal record is reconstructed from append-only PAPER/rejection evidence plus the latest durable checkpoint, making the handler idempotent and preventing an interrupt during startup from relabeling an older failed attempt. Exit status 130 remains accepted by systemd and creates no `PROCESS_INCIDENT`.

Operational Monitoring maps `OPERATOR_STOP` to `WARNING / STOPPED` and suppresses running-session staleness checks because the audit is closed. `ORDERING_FATAL` maps to `CRITICAL / FAILED`, and its root cause survives a later `PROCESS_INCIDENT` record. The forward report can show either terminal attempt with `audit_complete=True`, but only `MAX_BARS` can satisfy the endurance PASS gate.

The systemd start limit is also a whole-activation safety boundary. `StartLimitIntervalSec=infinity` plus `StartLimitBurst=2` bounds a reviewed activation to the initial start and one automatic recovery attempt; `Restart=on-failure` and the ten-second delay remain unchanged. The guarded activation procedure resets retained counters only while PAPER is inactive and accepts a direct start only when systemd explicitly reports that garbage collection has already unloaded the unit and discarded those counters. This prevents a per-process bar counter from extending one failed soak through an unbounded restart loop without turning unrelated reset failures into an activation path.

## Coinbase Cross-Channel Sequence Integrity Boundary v1
Coinbase's public Advanced Trade connection is consumed as one ordered envelope
stream before channel routing. A live CPX22 probe proved the exact interleaving:
`market_trades=0`, two `subscriptions` acknowledgements at `1/2`,
`market_trades=3`, `heartbeats=4`, then consecutive envelopes through `39`.
Validating only trade-channel sequence values therefore creates false gaps even
when the provider stream is complete.

`CoinbaseMessageSequenceTracker` observes every inbound envelope carrying
`sequence_num` before OHLCV aggregation or control-channel filtering. Only
`market_trades` payloads may reach the trade aggregator. A missing sequence is
immediately fatal when a market payload would otherwise be consumed; a
non-market control envelope without the optional field remains transparent and
the next sequenced envelope supplies the continuity check. Invalid sequence
values and forward gaps on any sequenced channel invalidate the socket because
the skipped envelope could have contained market data. Diagnostics retain the
provider channel as well as previous, expected and observed sequence values.

Lower/equal envelopes remain whole-message replays and are discarded before
trading. A valid market-trades payload is still required to reset recovery after
a sequence failure; subscription acknowledgements and heartbeats prove only
transport liveness. The exact REST/partial-minute recovery boundary, strict
two-second event-time rule, Strategy, Risk Engine, PaperBroker and structural
`REAL_orders=0` lock are unchanged.

## Coinbase Market-Trades Snapshot Boundary v1
Coinbase documents `market_trades` events as either `snapshot` or `update`, and
describes `update` as the incremental batch of trades collected over the prior
250 milliseconds. The 603-bar cloud attempt proved why that distinction is a
correctness boundary: a correctly sequenced `snapshot` envelope contained trade
`1070883132`, whose event time was 58.912 seconds behind the live watermark.
Treating provider state as a new incremental trade caused `ORDERING_FATAL` even
though the cross-channel sequence, transport and market-time continuity were
otherwise intact.

Every envelope still crosses `CoinbaseMessageSequenceTracker` first. After
sequence validation, the transport removes snapshot events from the data path
and emits `PROVIDER_SNAPSHOT_BOUNDARY` with message sequence/time, trade count,
trade IDs and oldest/newest trade timestamps. Snapshot trades never enter the
incremental reorder heap or OHLCV calculation. If one envelope contains both
snapshot and non-snapshot events, only the non-snapshot events may continue.
The aggregator independently ignores an explicit snapshot as a defensive
provider-adapter invariant.

A snapshot invalidates the in-progress WebSocket minute because its incremental
coverage cannot be proven. Forward PAPER resets only that partial aggregation
state, checkpoints the boundary and requires the first full bucket after the
provider message minute. Any earlier completed bucket is retained as
`PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED`; exact public REST candles reconstruct
the missing minute as non-tradable recovery before a fully observed live bar may
reach Strategy, Risk or PaperBroker. An existing startup `RESTART` boundary is
preserved, so a first-connection snapshot cannot accidentally replace the
separate seven-day startup-catch-up allowance with the smaller reconnect limit.

The forward report exposes `snapshot_boundaries` and
`snapshot_boundary_drops`. Both are handled continuity evidence, not alerts by
themselves. A genuinely late trade inside a correctly sequenced `update`
continues to raise `CoinbaseTradeOrderingError` under the unchanged two-second
watermark. Operational Monitoring now includes event type, trade ID and provider
message identity in any future `ORDERING_FATAL` alert. Strategy, Feed Health,
Risk Engine, PaperBroker, the two-start supervision budget and the structural
`REAL_orders=0` lock remain unchanged.

## Coinbase Post-Snapshot Trade Quarantine v1
The next cloud gate proved that excluding the snapshot payload is necessary but
not sufficient. Twice, Coinbase emitted a new nonzero-sequence snapshot on an
established connection and then delivered a correctly sequenced `update`
containing provider history older than the new trusted boundary. The observed
pairs were `10784 -> 10786` with trade `1071015409` from 57.988 seconds behind
the live watermark, and `7423 -> 7425` with trade `1071026960` from 6.013
seconds behind it. Both messages were sequence-valid, but neither old trade was
new incremental evidence.

Every `PROVIDER_SNAPSHOT_BOUNDARY`, including a nonzero in-band snapshot,
therefore establishes a monotonic event-time quarantine floor at the first full
minute after the snapshot message. Before any subsequent `market_trades`
payload reaches the reorder heap, trades strictly older than that floor are
removed from a copied message and recorded as
`PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED`. Evidence includes the snapshot
and update sequence identities, provider message time, trusted floor, trade
count/IDs and oldest/newest event time. Invalid timestamps are never hidden by
this filter; they remain subject to strict aggregator validation.

The boundary minute is explicitly retained as
`PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED`, and no Strategy, Risk or PaperBroker
decision is allowed until a complete minute at or after the trusted floor is
observed. Existing exact REST recovery reconstructs suppressed minutes only as
non-tradable state catch-up. The floor remains available after live PAPER
processing resumes so a later replay of snapshot-era history cannot poison the
active bucket.

This is a narrow provenance quarantine, not a wider lateness policy. A trade at
or after the trusted snapshot floor that arrives behind an already active later
minute still raises `CoinbaseTradeOrderingError`, closes the attempt as
`ORDERING_FATAL` and consumes the supervised recovery budget. The forward
report exposes the number of filtered trades as `snapshot_quarantine_trades`;
handled quarantine evidence remains monitoring-neutral. Cross-channel sequence
validation, the two-second update watermark, exact continuity, Strategy, Feed
Health, Risk Engine, PaperBroker and `REAL_orders=0` remain unchanged.

# First Strategy Candidate Pre-registration v1 Contract

The first offline candidate is frozen before any dataset result or performance
metric is inspected. Its immutable ID is
`ema-crossover-20-50-btc-eth-native-6h-v1`: the existing long-only
`ema_crossover` implementation with fast period 20 and slow period 50, no
leverage, exact `BTC-USD` / `ETH-USD` scope and native six-hour candles.
Signals are observed only at a completed Close and execute at the following
Open; any remaining terminal position is force-closed at the final Close for
reporting. Changing strategy, parameters, assets, timeframe, data range,
execution semantics, cost profiles or validation thresholds creates a new
candidate identity rather than mutating this one.

`coinbase_research_dataset.py` is a read-only research acquisition boundary
separate from the live Coinbase transport. It uses the public Exchange candles
endpoint without credentials and has no broker/order dependency. The frozen
range is `[2019-01-01T00:00:00Z, 2026-08-01T00:00:00Z)` at provider-native
`21600`-second granularity, yielding exactly 11,076 expected observations per
asset. Requests are deterministically chunked within Coinbase's 300-candle
response bound, retried only through a finite budget and accepted only when the
complete UTC grid, finite positive prices, non-negative volume and OHLC
geometry all pass. Missing, extra, misaligned or conflicting duplicate candles
fail closed.

After the primary chunk pass, missing grid buckets may be re-requested only by
their exact UTC intervals. The recovery boundary permits at most two passes and
100 exact-bucket requests per asset, while retaining the finite per-request
transport retry budget and duplicate-conflict checks. Only provider-returned
OHLCV data is accepted: interpolation, forward-fill, resampling and synthetic
candles are prohibited. Any persistent gap still fails closed with exact
timestamp samples and before any dataset file is written.

Accepted frames are serialized into canonical UTF-8/LF CSV bytes with UTC
second-precision timestamps, fixed `Timestamp/Open/High/Low/Close/Volume`
column order and `.17g` float representation. A canonical sorted JSON manifest
binds the acquisition contract, provider/source metadata, serialization rules,
file names, row boundaries and per-asset SHA-256 values. A separate
`manifest.sha256` binds the manifest bytes. The candidate lock independently
rechecks the manifest format and sidecar, asset scope, basename-only paths,
every file hash, exact row/time grid, numeric finiteness and OHLCV geometry.
Only then may the manifest digest become part of `data_version`.

Baseline execution assumptions are 0.60% commission per side, 0.05% slippage
per side and 0.10% full spread; the stress profile retains 0.60% commission and
raises slippage to 0.15% and full spread to 0.30%. The commission deliberately
uses Coinbase's published low-volume taker tier, while slippage/spread are
reviewed conservative research assumptions. Actual account pricing must be
re-frozen before any future venue integration.

Pre-registration and data locking never invoke Strategy Evaluation Protocol,
optimization, forward PAPER or any execution adapter. Until all bytes are
locked, status remains `DATASET_LOCK_PENDING`; after validation it becomes
`DATASET_LOCKED` with `evaluation_executed=False`. Even a later
`PAPER_CANDIDATE` result cannot authorize live trading.

## Strategy Failure Attribution and Volume Research Boundary v1

Controlled alpha discovery begins from the exact closed Strategy Family
Screening evidence rather than silently altering one rejected configuration.
`strategy_failure_attribution.py` accepts only the native BTC/ETH six-hour
manifest SHA-256
`6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`
and canonical screening report SHA-256
`9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f`.
It revalidates both evidence chains and all eight `SCREEN_OUT` outcomes before
binding any future diagnostic run. Declaration and lock paths execute no
backtest and write no evidence.

The diagnostic profiles are frozen as zero-cost, candidate-v1 baseline costs
and candidate-v1 stress costs. Their purpose is to separate absence of gross
signal from cost/turnover destruction while retaining the real-cost profiles as
the deployability boundary. Attribution also covers exposure, holding period,
drawdown concentration, benchmark excess, walk-forward persistence and market
regime. It creates no score, ranking, winner or parameter change.

`volume_research.py` supplies a causal per-asset participation layer. Relative
volume and relative dollar volume compare each completed bar with a lagged
20-bar trailing median; BTC and ETH raw volume are never compared. OBV and
LOW/NORMAL/HIGH volume regimes are retained as descriptive features. Trade
attribution uses `entry_signal_index`, ensuring that the following execution
bar cannot leak into the signal context. Volume is mandatory for the next alpha
hypothesis but is neither assumed to be standalone edge nor treated as a
substitute for live spread, order-book depth and market-impact evidence.

The protocol explicitly preserves inspected-development status. A separate
runner is required before diagnostics execute, and any combination/calibration
protocol remains a later boundary. Candidate v2, optimization, PAPER and live
execution remain false.

## Strategy Failure Attribution Runner Boundary v1

`strategy_failure_attribution_runner.py` is a one-shot, atomic evidence writer
for the exact 8-strategy by 3-profile matrix. Each profile uses the unchanged
multi-asset validation stack and causal next-Open execution. The complete raw
evaluation is normalized and hashed before bounded compaction; raw trade and
equity arrays are not duplicated in the recorded report.

`failure_attribution_metrics.py` consumes raw OOS evidence before compaction.
It verifies commission/execution/total-cost/net identities, derives turnover,
exposure and holding periods, and retains peak/trough/recovery plus yearly
drawdown concentration. Market and volume attribution both use
`entry_signal_index`. Relative volume, relative dollar volume and OBV direction
therefore describe only information available after the completed signal bar.

The report contains descriptive cross-profile changes and diagnostic flags but
no score, ranking or strategy-level winner. All 24 evaluations and derived
metrics complete before staging; canonical JSON and its SHA-256 sidecar are
atomically promoted together. Existing final or staging evidence blocks a
repeat. The runner changes no Strategy, Risk, cloud or execution behavior.

## Alpha Development Protocol v2 Boundary

`alpha_development_protocol.py` binds only the exact closed six-hour dataset
and Failure Attribution v1 report. It freezes a three-step causal ablation
chain around ADX direction, mandatory high per-asset relative volume, the exact
`BULLISH_NORMAL` market regime and optional rising OBV. The variants are direct
joint intersections, not sums of marginal conditioned profits and not a
parameter leaderboard.

`alpha_development_strategy.py` generates the joint conditions from completed
bars. All variants use ADX 14 entry threshold 25, exit hysteresis at 20, a
four-bar cooldown, ATR 14 risk distance and 3:1 intended reward/risk. Volume is
an entry confirmation rather than an immediate exit trigger. The feature path
is prefix-causal and preserves the input frame.

`protective_exit.py` removes the prior Backtesting Engine gap between sizing
from risk levels and actively executing them. It resolves levels at the next
Open from lagged signal-bar risk distance, checks stop gaps before pending
signals, uses conservative target-gap pricing and chooses stop first when an
OHLC bar touches both levels. Every fill uses normal sell friction and produces
explicit reason/trigger/fill evidence. Legacy behavior remains unchanged when
the optional policy is absent.

Protective policy and Risk Engine propagate through OOS, walk-forward,
validation-pipeline and multi-asset layers.

`alpha_development_runner.py` is the separate one-shot research boundary. It
locks the exact manifest and attribution report before executing the three
pre-declared joint variants under the three allowed taker scenarios. A fresh
Risk Engine and exact Protective Exit Policy are injected into every
multi-asset validator. Coinbase baseline/stress drive gate decisions; Kraken
remains venue sensitivity and the deferred maker scenario is unreachable.

Raw OOS trades are consumed only long enough to derive annualized executed
notional, modeled-cost fractions and protective/signal exit counts. The bounded
canonical report retains compact validation evidence and raw-evaluation hashes,
not trade histories. Atomic final/staging directories prevent overwrite and
repeat. Comparison preserves declaration order and exposes no ranking, winner
or automatic selection. Candidate v2, PAPER and live authorization are
hard-false report invariants.

`venue_execution_research.py` retains Coinbase baseline/stress, a dated Kraken
Pro taker sensitivity and a blocked maker scenario. Static Kraken tiers are
sensitivity assumptions, not proof of account eligibility. Maker evidence is
blocked until a causal placement, non-fill and partial-fill model exists.
Venue savings cannot override drawdown, persistence or falsification.

The boundary freezes 0.50% risk per trade, 50% maximum position size, no
leverage/shorting, 20% drawdown, daily/weekly new-risk limits and annual
turnover/cost budgets. Declaration and evidence locking execute no joint
performance, calibration or optimization. Candidate v2, PAPER and live remain
false.

## Alpha Discovery and Calibration Protocol v1

`src/alpha_discovery_protocol.py` is the non-executing boundary between closed
Alpha Development v2 evidence and any future adaptive research runner. It
strictly reloads the canonical Alpha v2 report, its sidecar and exact
`SCREEN_OUT` gate basis before permitting an evidence lock.

The module owns four deterministic components:

- an eight-member immutable parameter catalog;
- a nested expanding chronological window planner;
- an inner-evidence eligibility and deterministic selection policy; and
- a declaration/evidence-lock boundary that executes no market evaluation.

The catalog keeps volume mandatory and fixes causal `BULLISH_NORMAL` plus EMA
trend structure. It varies only two ADX hysteresis bands, two ATR risk distances
and static-versus-completed-bar break-even management while preserving the 3R
target. OBV is diagnostic only.

The planner exposes only inner validation windows ending at or before each
outer-test boundary. The selector accepts the complete ordered catalog and
exact BTC/ETH inner metrics; its API contains no outer-test input. Missing or
extra configurations, asset drift, non-finite metrics or lost protective
execution fail closed. If nothing meets every cross-asset baseline/stress,
persistence, trade, drawdown, turnover and cost gate, the required action is
hold cash.

`src/alpha_discovery_features.py` implements prefix-causal EMA 50/200 structure
from completed Close values. The optional break-even state in
`src/protective_exit.py` may ratchet the active stop to entry only after a
surviving completed bar reaches +1R; activation begins at the following Open.
`src/trade_path.py` and the Backtesting Engine derive MFE, MAE, realized R,
holding bars and time-to-MFE without using unreachable exit-bar extremes.

These components preserve static Alpha v2 behavior when break-even is disabled.

## Alpha Discovery Runner v1 Boundary

`src/alpha_discovery_strategy.py` maps every immutable catalog member to its
exact ADX hysteresis, ATR risk distance, completed-bar volume/regime/EMA gates
and optional next-Open break-even policy. Signal position state is reset at an
evaluation boundary while historical bars remain available only for causal
feature warm-up.

`src/alpha_discovery_runner.py` locks the exact development manifest and closed
Alpha v2 report in the execution process. It first performs non-selecting
zero-cost path attribution, then evaluates all eight members on prior inner
validation windows under baseline and stress. The selection API has no outer
result input. An ineligible catalog produces `HOLD_CASH`, not a least-bad
trade.

Window summaries are identity-bound to asset, parameter, cost profile, phase
and exact positional boundary and retain a complete canonical raw-partition
hash. Reused inner evidence is historical evidence available at the applicable
selection cutoff. Outer results never modify later catalog definitions or
produce a global hindsight leaderboard.

The one-shot canonical report is promoted from a staging directory only after
all diagnostics, inner selections and outer evaluations complete. Existing
final or staging evidence blocks another run. The report can retain only
development interest; Candidate v2, optimization, PAPER, cloud and live
authorization remain false.

## Trend Pullback and Volume Re-expansion Protocol v1

`src/trend_pullback_volume_protocol.py` is a declaration and evidence-lock
boundary for the
mechanism that follows closed Alpha Discovery v1. It reloads the exact
canonical Discovery report and sidecar, then recomputes its identity,
authorization state, seven hold-cash selections, complete catalog membership
and all 56 inner gate records before an evidence lock can succeed.

The new mechanism is a causal state sequence rather than an ADX threshold
tweak. Completed bars must establish bullish EMA structure and prior ADX
strength, pull back near EMA 50 on contracting/normal relative volume, then
recover price structure with renewed volume and positive directional movement.
Entry is deferred to the following Open.

The immutable four-member catalog varies only pullback distance and trigger
relative volume. ADX hysteresis, EMA periods, lagged volume baseline, static
2 ATR stop, 3R target, position-risk limits and nested chronological gates are
shared. Its literal catalog hash makes accidental semantic drift observable.

The protocol declaration contains no market evaluation. Its same-process lock
may authorize only the separately reviewed one-shot runner, while Candidate
v2, optimization, PAPER, cloud and live authorization remain false.

`src/trend_pullback_state.py` now implements the causal ordered setup. It uses
only completed-bar prefix data, resets at the requested evaluation boundary and
cannot trigger on its pullback bar. Setup expiry, trend invalidation and
position/cooldown suppression prevent stale entry context from crossing an
operational boundary.

`src/trend_pullback_volume_strategy.py` composes the reviewed ADX/ATR, lagged
relative-volume and EMA components with that state machine. It emits the exact
four-member catalog in declaration order and exposes static protective risk
inputs without executing a backtest. Market-regime and OBV entry gates are
explicitly absent.

## Trend Pullback Volume Runner v1 Boundary

`src/trend_pullback_volume_runner.py` locks the exact six-hour manifest and
closed Alpha Discovery report inside the execution process. It evaluates the
four-member catalog on ten unique historical inner validation windows under
baseline and stress, giving 80 complete two-asset inner evaluations. Reused
inner evidence is available only at the applicable chronological selection
cutoff.

The selector accepts only the complete frozen catalog in declaration order and
exact BTC/ETH metrics. It has no outer-test input. If no member passes every
return, persistence, trade-count, drawdown, turnover, cost and protective-exit
gate, the outer action is `HOLD_CASH` and no outer strategy evaluation occurs.
Otherwise, only the inner-selected member is evaluated on that outer window.

Every compact result binds parameter, asset, profile, phase and exact window
positions to a canonical raw-partition hash; raw trade histories are not
persisted. A canonical report and SHA-256 sidecar move atomically from staging
to final only after all seven outer decisions finish. Existing final or staging
evidence blocks another run. Development interest is descriptive only and can
never authorize Candidate v2, optimization, PAPER, cloud or live execution.

## Selective Swing Trading Research Boundary v1

`SELECTIVE_SWING_TRADING_RESEARCH_MANDATE_V1.md` defines a documentation-only
research reset after Trend Pullback Volume v1 closure. It introduces no signal,
dataset mutation, performance runner or deployment authorization.

The target research architecture has two independent alpha sleeves:

```text
Point-in-Time Equity Data -> CAN SLIM Replication Research ----\
                                                               \
Daily Crypto Data -> Blinded Replay -> Capitulation Research ----> Future Eligible-Signal Boundary
                                                               /
Common Risk / Cost / Portfolio / Evidence Infrastructure ------/
```

Equity research requires a dedicated point-in-time fundamentals and historical-
universe boundary. Earnings, revenue, corporate actions, industry membership,
institutional sponsorship and publication availability must be reconstructible
at the historical decision timestamp. Current constituent lists, revised
fundamentals and survivor-only price histories are invalid inputs.

Crypto research begins with a blinded daily chart-replay boundary. It reveals
bars sequentially, records entry/skip/exit reasoning before advancing and
preserves every decision as reconstruction evidence. Replay annotations cannot
authorize a strategy or serve as unseen performance.

The two sleeves may reuse validated OHLCV, feature, backtest, protective-exit,
risk and canonical-evidence components. They may not reuse market-specific
feature meaning or transfer tuned thresholds. A future portfolio layer accepts
only independently eligible signals and treats cash as a first-class outcome.

The previously planned exact six-hour pullback trade-path attribution remains
available as deferred inspected-data diagnostics. It is no longer the active
next mission and cannot influence the new daily crypto or equity protocol
without explicit pre-registration.

## BTC/ETH/XRP Daily Data and Blinded Replay Boundary v1

`src/daily_crypto_replay_protocol.py` binds the normalized Selective Swing
Trading mandate hash to the exact recorded BTC/ETH one-day Coinbase manifest.
It intentionally leaves the XRP provider unset until venue history, candle and
volume semantics, availability intervals, liquidity and costs are audited.
Consequently the current state is provider-audit-required: no complete three-
asset dataset or real replay is authorized.

`src/blinded_daily_replay.py` provides the causal replay primitive independently
of market performance. Each continuous provider-availability segment is
validated as exact UTC-midnight daily OHLCV without synthetic gap filling. A
session reveals only a rolling 30-bar copy and requires an immutable reasoned
decision before the next bar appears. Flat and long actions are explicitly
state constrained, and each decision binds the SHA-256 of its visible frame.

The replay component emits no P&L, return, drawdown, benchmark, ranking or
parameter selection. Its annotations are inspected hypothesis-reconstruction
evidence and cannot become unseen validation evidence. Dataset acquisition,
real replay, strategy definition and performance remain later separately
reviewed boundaries.

## Selective Swing Portfolio Construction Boundary v1

`src/selective_swing_portfolio_protocol.py` declares a shared portfolio layer
without creating an executable allocator. Every market sleeve must first
produce an independently eligible causal signal. Only then does the raw capital
envelope become `1/n` across eligible members; final notional remains the lower
of that envelope and stop-based, position, portfolio, cash, sector and
correlation limits. Zero eligible signals means cash.

The equity sleeve begins with no more than three concurrent positions. A future
five-position ceiling requires separate review. Exiting a member releases cash
but does not authorize automatic transfer to prior winners. Winner-only
pyramiding requires a fresh add-on structure, a smaller tranche and complete
risk recomputation; averaging down is prohibited.

The same boundary records `Exceptional Sideways Breakout Contingency v1` as a
separate unimplemented event-driven equity hypothesis. An observed 20–30% or
larger move from a causal sideways base is descriptive, not an entry threshold.
General day trading and scalping remain unauthorized. Any future contingency
requires point-in-time intraday data, halt/liquidity/cost review, confirmation,
no-chase and predefined-stop rules, smaller risk, one-position capacity and
same-session flattening under a separately reviewed protocol.

The portfolio boundary also separates three evidence books: daily crypto
swing, point-in-time CAN SLIM swing and the exceptional intraday contingency.
A shared future risk engine sits above them and may return
`NO_TRADE_HOLD_CASH` when signal, regime, stop, cost, data, reward-room,
correlation or portfolio-risk gates fail. Approximate 0.25%–0.50% swing risk and
1.00%–1.50% total open-risk ranges are research starting points only. The
intended `3R` opportunity is an entry-quality screen, not a guaranteed return or
forced full exit. PAPER/live policies remain frozen and may improve only through
offline versioned evaluation and explicit promotion.

## BTC/ETH/XRP Provider and Historical Availability Boundary v1

`src/btc_eth_xrp_provider_audit.py` binds the frozen daily replay protocol to a
reviewed provider decision without performing network acquisition. Coinbase's
existing BTC/ETH daily manifest remains independent recorded evidence, but
Coinbase is rejected as the common three-asset source because XRP trading was
suspended from January 2021 until July 2023.

The primary daily research path is one Kraken Spot venue for `BTC/USD`,
`ETH/USD` and `XRP/USD`. The provider's official complete OHLCVT archive and
required quarterly updates form the historical baseline. Kraken REST OHLC is a
recent same-venue bridge and overlap verifier only: its 720-entry retention
cannot reconstruct full history, and its final uncommitted bar is discarded.

The future builder must inventory archive members and hashes, preserve legacy
pair identity, require exact equality for duplicate completed archive/REST
buckets and publish nothing on a mismatch. Missing daily intervals are explicit
`NO_TRADE_UNAVAILABLE` boundaries; they are never forward-filled, synthesized
or converted into zero-volume observations. Replay segments split at gaps.

Kraken volume remains venue and base-asset bound. Relative volume is computed
causally within each asset; raw cross-asset and cross-venue volume comparison is
prohibited. Current fee observations document acquisition context only and do
not freeze a future execution profile. Exact archive coverage, liquidity,
spread, slippage and performance remain later gates.

## Kraken Native Daily Dataset Lock Boundary v1

`src/kraken_daily_dataset.py` binds the provider-audit hash to one exact
Kraken Spot dataset contract for BTC-USD, ETH-USD and XRP-USD over the
2019-01-01 inclusive through 2026-08-01 exclusive UTC daily window. It accepts
one official complete archive plus only reviewed quarterly updates, hashes each
ZIP and inventories every member before selecting exactly one 1440-minute file
for `XBTUSD`, `ETHUSD` and `XRPUSD`.

Archive rows retain Decimal OHLCV precision and trade counts during validation.
Equal duplicates across official inputs are audited; conflicting duplicates
have no precedence and block the lock. Kraken REST supplies only a recent
completed-bar bridge. Its uncommitted final row is removed, its raw response is
hashed, and every asset requires at least one exactly equal archive/REST bucket
before REST-only additions can enter the canonical window.

The publisher calculates the full expected UTC grid without manufacturing it.
Missing timestamps are listed and split into continuous availability segments;
canonical CSV output contains observed provider rows only. Archive inventory,
raw REST evidence, three canonical assets, the manifest and its sidecar are
written to a unique staging directory and atomically renamed only after all
checks pass. `KrakenDailyDatasetLock` independently revalidates every published
hash. This boundary can lock data provenance but cannot run replay, strategy,
performance, PAPER, cloud or live execution.

## Kraken Native Daily Archive-Only Dataset Lock Boundary v2

The v1 acquisition path is preserved as a fail-closed source-equivalence
result. Across 482 completed overlapping buckets for each asset, archive and
REST OHLC matched exactly, while volume and trade-count equality failed
extensively. V1 therefore produced no dataset and REST has no precedence,
tolerance or permission to enter the v2 historical lock.

`src/kraken_daily_dataset.py` now binds the upstream provider-audit hash and
the exact v2 lock-protocol hash to dataset identity
`kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`.
The production path accepts exactly the reviewed complete archive and Q1 2026
quarterly update, in fixed order, with frozen filename, role, byte size and
SHA-256 evidence. The final included bucket is 2026-03-31; the contract end is
2026-04-01 exclusive.

The existing archive inventory, Decimal OHLCVT parser, no-precedence duplicate
merge, gap segmentation, canonical writer, staging promotion and independent
hash lock remain controlling. The v2 build performs no network request and
writes no REST evidence. Its manifest must state
`OFFICIAL_OHLCVT_ARCHIVES_ONLY` and `network_requests_executed: false`.
Production source identity is independently rechecked during lock loading.

The completed Windows production attempt published manifest SHA-256
`8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`.
The archive inventory contains 34,325 members and independently reproduced
SHA-256
`cbfc0963b5966a5f94f97ff90a1bd52761167e9846515aad2abe7a85f27882b2`.
Canonical output retains 2,646 BTC rows with one explicit unavailable day,
2,647 ETH rows without a gap, and 2,645 XRP rows with two explicit unavailable
days. `KrakenDailyDatasetLock` independently revalidated the manifest,
contract documents, source evidence, inventory and all three canonical hashes.
The large source and dataset bytes remain external; Git retains only compact
lock evidence.

V2 changes data provenance only. Real replay, strategy, performance,
optimization, Candidate v2, PAPER, cloud and live authorization remain false.

## Kraken Bounded Blinded Replay Review Boundary v1

`src/kraken_blinded_replay_review.py` supersedes the historical Coinbase/XRP-
audit-required declaration only for the exact independently locked Kraken v2
dataset. It re-locks manifest SHA-256
`8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`,
reproduces the BTC/ETH/XRP gaps and continuous segments, and computes a sealed
three-episode schedule without consulting OHLCV values. Review and preflight
output expose counts and hashes only, never selected starts, endpoints or
remaining bars.

The first bounded catalog has one episode per asset. A candidate is 89
continuous rows: the first public view contains 30 bars and the episode then
records exactly 60 decisions including that context-ending bar. The selected
candidate index is a deterministic SHA-256 of protocol ID, manifest hash and
asset modulo the asset's chronologically enumerated continuous candidates.
Changing price or volume cannot change selection.

`BlindedDailyReplaySession` accepts an optional decision sink. It calls that
sink before changing position state or unlocking `advance()`, so durable-write
failure leaves the current bar closed. Visible-frame hashes now preserve exact
decimal evidence instead of coercing it through binary float serialization.

`src/blinded_replay_evidence.py` writes every decision exclusively under a
staging directory with a canonical JSON file, SHA-256 sidecar and prior-record
hash. Episode completion atomically promotes a compact manifest. A separate
`BlindedReplayEvidenceLock` revalidates canonical bytes, identity, order,
sequence, the full chain and all non-performance flags. Episodes start flat
and never carry positions; a terminal long remains explicitly unresolved
rather than receiving a synthetic exit.

The one Windows preflight independently re-locked the exact external v2
manifest and reproduced availability segments of `1916, 730` BTC rows, `2647`
ETH rows and `1226, 1419` XRP rows. Their price-independent candidate counts
were 2,470, 2,559 and 2,469. The selected one-per-asset schedule is bound by
SHA-256
`3e805044356777f0bdfa2901db267d714c1e14d11415dd4686acaaaed92f1042`.
Preflight output exposed no selected timestamp, persisted no schedule, built no
participant view and executed no network request or chart replay.

This boundary now records methodology and sealed-preflight evidence only. It
creates no strategy, P&L, ranking, Candidate v2, PAPER, cloud or live
authorization. One supervised real reconstruction requires a separate review
and explicit authorization.

## Kraken Supervised Blinded Replay Execution Boundary v1

`src/kraken_blinded_replay_runner.py` adds an execution boundary without
changing either frozen causal replay component. Its default review mode exact-
hash binds the dataset evidence, replay-review protocol, sealed-preflight
evidence, supervised execution protocol and both replay/evidence components;
it opens no dataset and creates no participant view.

Execution requires an exact one-episode operator phrase. The external evidence
root is a state machine: empty permits BTC, valid BTC permits ETH, and valid BTC
plus ETH permits XRP. The runner never accepts an asset argument. Existing
episodes are independently locked before progression; skipped assets,
unexpected files, tampering, incomplete staging or a completed catalog block
execution.

After reproducing the exact sealed schedule, the runner builds only the next
89-row frame and displays its rolling 30-bar OHLCV context in one in-memory
candlestick/volume chart. Each action and reason passes through
`BlindedDailyReplaySession` and `DurableBlindedReplayJournal`, preserving the
write-before-advance guarantee. Only one 60-decision episode can complete per
invocation, and no chart image or source OHLCV is written to evidence.

The third episode produces an atomic catalog linking all three independently
locked evidence hashes, decision counts and terminal resolutions. The catalog
lock revalidates exact identity, order and non-performance safety flags. This
boundary prepares supervised reconstruction only; real replay remains
unauthorized until a later explicit operator decision, and strategy,
performance, Candidate v2, PAPER, cloud and live remain separate boundaries.

## Kraken AI-Driven v2 Layer Boundary

The supervised replay v1 execution layer is retained unchanged as historical
infrastructure and evidence. Its one completed BTC episode is bound by
aggregate SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`.
ETH and XRP participant views remain unopened. V2 uses a new protocol identity
and will use a separate schedule and evidence root; it cannot append automated
decisions to v1 evidence.

The first V2 dependency direction is:

`locked OHLCV -> continuous segment -> causal measurements -> future state machine -> future risk/execution -> future durable decision evidence`.

`src/kraken_ai_driven_v2_features.py` owns only the causal-measurement layer.
It validates exact daily OHLCV, rejects crossing known gaps, excludes the
current bar from rolling comparison baselines and returns unavailable warm-up
or zero-denominator measurements instead of creating a signal. Its output has
no action, position, performance or optimizer field.

The future state-machine layer must be a versioned deterministic program with
explicit `FLAT`, `ARMED` and `LONG` transitions. A language model may assist
offline research and code review but cannot improvise runtime rules. The
future risk/execution adapter may reuse neutral `RiskEngine` sizing and
`ProtectiveExitPolicy` stop-first semantics only after it binds V2-specific
columns and next-open timing through new tests. Rejected trend-pullback and
Alpha signal conditions remain historical and are not dependencies of V2.

The source dataset does not require an update for initial development. Any new
Kraken quarterly bytes create a new immutable dataset ID instead of changing
manifest
`8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`.
Before any performance runner, the architecture must freeze development,
calibration and genuinely untouched evaluation partitions. The inspected BTC
v1 window is permanently ineligible for unseen-validation claims. Candidate
v2, PAPER, cloud and live authorization remain false.

## AI-Driven v2 Signal-State Layer

`src/kraken_ai_driven_v2_state_machine.py` consumes the exact causal feature
component and owns only signal state. Reference identity
`kraken-ai-v2-ccvr-reference-a-v1` is hash-bound to its protocol. The inspected
BTC supervised evidence remains separately identified by SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`.

The state component is sequential and prefix-causal. It keeps one immutable
event timestamp and evolving setup low while `ARMED`, then fixes that low if
confirmation changes signal state to `LONG`. Re-arm, invalidation, expiry and
confirmation have explicit priority; structural and bearish-volume exits have
explicit priority. Every row retains state before/after, reason code, intent,
condition flags and causal anchors.

`LONG` means an active research signal, not an executed position. The component
does not import the backtester, broker, `RiskEngine` or `ProtectiveExitPolicy`,
and it stores no fill, quantity, equity or P&L. `ENTER_NEXT_OPEN` and
`EXIT_NEXT_OPEN` cross a future adapter boundary where next-open gaps and real
fill semantics must be resolved. That adapter must never reinterpret an intent
as an already completed trade.

The state layer uses synthetic test frames only and opens neither the locked
Kraken data nor the sealed ETH/XRP v1 episodes. A future risk/execution layer
may reuse neutral sizing and stop-first primitives through new adapters, but
Candidate v2, optimization, performance, PAPER, cloud and live remain blocked.

## AI-Driven v2 Risk and Synthetic Execution Layer

`src/kraken_ai_driven_v2_risk_execution.py` is the only current bridge from a
completed-bar state intent to a synthetic research position. It accepts exact
`CONFIRMATION_LONG` / `ENTER_NEXT_OPEN` evidence and the next consecutive UTC
daily open under policy `kraken-ai-v2-risk-execution-reference-a-v1`. The BTC
supervised evidence remains context-only under SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`.

The layer separates four objects that must never be conflated: a state intent,
an approved synthetic entry plan, a synthetic research position and an exit
decision. No object is a broker order or venue fill. The entry gate rejects
stop gaps, excessive upward gaps, unavailable portfolio capacity and less than
net cost-aware `3R` room to the prior 30-bar close high. Size is the minimum of
cost-aware stop-risk size, one-third equity notional and available-cash size,
within `0.50%` per-position and `1.50%` total open-risk ceilings.

`RiskEngine` remains the neutral deterministic size primitive.
`ProtectiveExitPolicy` remains the neutral stop-first OHLC ordering primitive.
The adapter owns every V2-specific binding: fixed setup-low stop, causal
resistance target, following-open timestamp, adverse Kraken taker cost model,
gap ordering, 20-bar maximum hold and state-scheduled exit. Entry-bar
protection is mandatory, the structural stop cannot widen and target gaps gain
no favorable price improvement.

Cost profile `kraken-tier1-taker-adverse-20260829-v1` freezes `0.80%` taker
commission per side from the reviewed official schedule and research-only
`0.15%` slippage per side plus `0.30%` full spread. It does not verify the
operator's account tier, pair minimum, order-book depth, partial fills or
outages and therefore cannot produce a real order.

This layer has no P&L field and opens no external market data. After Windows
integration, a separately hash-bound partition layer must freeze development
and truly untouched evaluation identities before any complete-data runner is
permitted. Optimization, Candidate v2, PAPER, cloud and live remain blocked.

## AI-Driven v2 Partition Boundary

`src/kraken_ai_driven_v2_partition.py` freezes protocol
`kraken-btc-eth-xrp-ai-driven-v2-partition-v1` against the exact archive-only
dataset manifest. It is a metadata and timestamp-index validator, not a data
loader or strategy runner. Its constructor exposes only the reference plan, so
different dates cannot silently retain the same identity.

The half-open path is `DEVELOPMENT` from `2019-01-01T00:00:00Z` to
`2024-04-01T00:00:00Z`, `CALIBRATION` through
`2025-04-01T00:00:00Z`, then sealed `EVALUATION` through
`2026-04-01T00:00:00Z`. Calendar counts are `1917/365/365`; observed counts
are BTC `1916/365/365`, ETH `1917/365/365` and XRP `1915/365/365` after the
exact provider gaps are preserved.

The inspected BTC episode bound by SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
lies in calibration and is explicitly not unseen. Evaluation begins at
`2025-04-01T00:00:00Z` and remains genuinely untouched. No rolling feature
history, event anchor, state, position, risk, cash mutation or pending intent
may cross a partition boundary or provider gap.

The hash-bound review verifies the risk/execution protocol and component plus
the partition protocol and component. It reports no dataset access, no real
partition materialization and no performance. A later development runner must
be separately reviewed and must read only development timestamps. Calibration
and one-time evaluation require later protocols; optimization, Candidate v2,
PAPER, cloud and live execution remain unauthorized.

## AI-Driven v2 Development-Only Evidence Runner

`src/kraken_ai_driven_v2_development_runner.py` implements protocol
`kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1`. It does not reuse the
complete-value `KrakenDailyDatasetLock` load path. Instead it exact-hash checks
the manifest, inventory and full canonical files as opaque bytes, then parses
only timestamps strictly before `2024-04-01T00:00:00Z`. The first excluded
timestamp must equal that boundary and both calibration/evaluation parsed-row
counts must remain zero.

The execution graph is a daily multi-asset portfolio rather than three
independent capital accounts. Existing open exits run first. Pending entries
then consume shared USD 5,000 research cash and total risk in fixed
BTC-USD/ETH-USD/XRP-USD order. Intrabar stop-first protection follows, then
completed-bar scheduling and an adverse net-liquidation close mark. The frozen
state parameters, risk policy and cost profile are reused without a sweep.

Every continuous segment receives a new feature warmup and signal machine. A
missing following open cancels a pending entry. An active position at a known
gap halts the whole path as inconclusive before later data can be processed.
Terminal positions are marked diagnostically but remain unresolved; no force-
close trade or realized P&L is fabricated.

The runner writes canonical one-shot evidence under an external staging/final
pair only after the exact operator phrase. Existing final or incomplete
staging evidence blocks repeat. The separate nonexecuting review hash-binds
all feature, state, risk, partition and development artifacts. Review opens no
dataset and grants no run authorization. Results cannot automatically promote
calibration, evaluation, Candidate v2, PAPER, cloud or live execution.

Development Attempt 1 established one additional representation boundary.
Canonical CSV text is validated with `Decimal` so malformed or non-finite
input fails before the state path, then stored as `float64` for the existing
feature, state and risk/execution contracts. The original implementation
retained `Decimal` objects and failed closed at the first eligible signal before
evidence-root creation. Recovery changes no strategy, partition, risk, cost or
execution semantic and requires a newly hash-bound runner plus separate retry
authorization.

Recovery Attempt 2 produced canonical report SHA-256
`f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`.
The read-only closure joins that report hash to execution commit `1f040e2` and
the successful hash-bound preflight, then requires the exact complete outcome.
All 13 `CONFIRMATION_LONG` transitions became risk/execution rejections: two
had no resistance above entry and eleven lacked net adverse-cost `3R` room.
With zero approved plans, positions or trades, status
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH` closes the
mechanism without interpreting zero P&L as performance. Calibration,
evaluation, Candidate v2 and deployment remain separate blocked boundaries.

## AI-Driven v2 Hybrid Strategy Discovery and Learning Boundary

After Reference A closure, `src/kraken_ai_driven_v2_strategy_discovery.py` implements nonexecuting
protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`.
The architecture is hybrid: a shared family/regime vocabulary governs all
three assets, while each immutable hypothesis explicitly owns an ordered asset
subset, eligible causal regimes, permitted indicators, signal identity,
family-specific execution identity and development-gate identity. `HOLD_CASH`
is the required fallback for an unclassified regime or an asset without an
eligible route.

The bounded catalog contains capitulation recovery, trend-pullback
continuation, range mean reversion and volatility breakout. It permits no more
than six hypotheses per round, two variants per family, four routes per asset,
two separately authorized rounds and twelve hypotheses over protocol v1. The
component validates future JSON-compatible manifests and returns canonical
content plus SHA-256; it has no market-data reader, signal calculation,
backtester, optimizer or execution method.

Every future family adapter must preserve the common USD 5,000 cash-only
safety envelope: `0.50%` position risk, `1.50%` total open risk, three
positions, one-third notional, completed-bar/next-open causality, entry-bar
protection, stop-first ordering and the frozen adverse Kraken cost profile.
It must separately define a causal stop and exit/target path. The closed
Reference-A prior-resistance adapter is not a generic policy and cannot be
reused simply to alter its failed `3R` gate.

`src/kraken_ai_driven_v2_strategy_discovery_review.py` exact-hash binds the
Reference-A closure, risk/execution and partition protocol/components plus the
new protocol and manifest-validator. Review opens no data and registers no
hypothesis. Runtime learning, parameter grids, ranking, strategy selection and
automatic promotion are prohibited; feedback can only produce a separately
reviewed version after an immutable round is closed. Candidate v2, calibration,
sealed evaluation, PAPER, cloud and live remain unauthorized.

## AI-Driven v2 Hybrid Discovery Round 1 Registration Boundary

`src/kraken_ai_driven_v2_hybrid_discovery_round_1.py` implements protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1` as configuration
and evidence identity only. Its four hypotheses cover capitulation recovery,
trend-pullback continuation, range mean reversion and volatility breakout in
fixed order. All initially register BTC/ETH/XRP routes; the later evaluation
unit is one asset-family pair, not a forced universal strategy.

Every hypothesis binds its economic thesis, family/regime vocabulary,
two-to-five indicators, exact numeric regime and confirmation parameters,
following-open gap rule, structural stop, net `3R` target/room, scheduled exit
and maximum hold. Rolling baselines exclude the current bar. The capitulation
member cites Reference A evidence but uses new signal/execution identities and
explicitly removes prior-resistance gate reuse.

The lock also freezes baseline and doubled-slippage/spread stress profiles,
five chronological Development slices and absolute route-interest gates:
minimum sample and time coverage, baseline/stress expectancy and profit factor,
marked drawdown, outlier concentration and zero unresolved positions. A round-
level gate requires at least two assets and two routes. Same-asset multiple
passes require a separate portfolio review; the configuration exposes no
ranking or selection function.

`src/kraken_ai_driven_v2_hybrid_discovery_round_1_review.py` hash-binds the
parent hybrid protocol/component/review and the complete Round-1
protocol/component. Neither module imports market-data or backtesting code.
Regime, signal and execution components remain absent, so Development access
and execution remain structurally unavailable. Candidate v2, Calibration,
Evaluation, PAPER, cloud and live remain blocked.
