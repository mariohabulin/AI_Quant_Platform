# ROADMAP

# AI Alpha Engine Development Roadmap

## Purpose

This document defines the long-term development plan of the AI Alpha Engine.

Its purpose is not to describe individual Python implementations, but to present the logical evolution of the system from a quantitative research platform into a fully autonomous AI Alpha Trading Agent.

Each development phase introduces new capabilities while preserving the stability of previously validated modules.

Every phase must be completed, validated and documented before development proceeds to the next stage.

---

# Phase 1 — Data Foundation

## Objective

Build a reliable foundation for collecting, validating and visualising market data.

## Core Components

- Data Collection
- Data Storage
- Data Cleaning
- Data Visualization

## Status

🟢 Completed

## Result

The system can reliably collect, validate, store and visualise historical market data.

---

# Phase 2 — Research Engine

## Objective

Build a modular quantitative research platform capable of developing, executing, backtesting and objectively evaluating independent trading strategies.

## Completed Components

### Feature Engine

- Dynamic feature generation
- EMA generation
- RSI generation
- Return calculation
- Volatility calculation
- Volume moving average
- Input validation

### Strategy Library

- Strategy registration
- Strategy validation
- Duplicate protection
- Strategy lookup

### Strategy Engine

- Common strategy contract
- Strategy execution
- Required feature integration
- Signal validation

### Trading Strategies

Validated strategies:

- EMA Strategy
- RSI Strategy

Both strategies execute through the same architecture.

### Backtesting Engine

- Trade simulation
- Portfolio management
- Trade history
- Equity curve
- Stateless execution

### Performance Analyzer

- Performance metrics
- Strategy evaluation
- Deterministic performance analysis

---

## Research Engine Validation

Successfully validated:

- Dynamic Feature Engine
- Parameterized strategies
- Required Features contract
- Common Strategy contract
- Strategy-independent execution pipeline
- End-to-End Research Pipeline

Current automated test status:

✅ **112 / 112 automated tests passing**

---

## Status

🟢 Completed

The Research Engine is now a stable modular platform capable of supporting multiple independent trading strategies through a single reusable execution pipeline.

Future strategies should integrate without requiring architectural changes.

---

# Phase 3 — Strategy Optimization

## Objective

Develop the optimisation layer responsible for discovering robust strategy configurations while reducing overfitting.

## Planned Components

- Strategy Optimizer
- Parameter Search
- Strategy Ranking
- Walk Forward Analysis
- Robustness Testing

## Completion Criteria

The system can objectively compare parameter combinations and identify statistically robust strategies.

## Status

⬜ Planned

---

# Phase 4 — Risk & Portfolio Management

## Objective

Protect capital through systematic risk and portfolio management.

## Planned Components

- Risk Engine
- Position Sizing
- Portfolio Engine
- Capital Allocation

## Completion Criteria

The system manages risk and capital independently from trading strategies.

## Status

⬜ Planned

---

# Phase 5 — Market Intelligence

## Objective

Understand current market conditions and identify the most appropriate trading opportunities.

## Planned Components

- Market Scanner
- Market Regime Detection
- Opportunity Detection
- Strategy Recommendation

## Completion Criteria

The system recognises changing market conditions and recommends appropriate trading strategies.

## Status

⬜ Planned

---

# Phase 6 — Alpha Decision Engine

## Objective

Combine research, market intelligence and risk management into a unified decision-making system.

## Planned Components

- Strategy Selection
- Strategy Confidence Evaluation
- Market Regime Integration
- Risk Validation
- Portfolio Validation
- Trade Decision

## Completion Criteria

The system autonomously selects the most appropriate strategy based on statistical evidence.

## Status

⬜ Planned

---

# Phase 7 — AI Learning Engine

## Objective

Enable continuous improvement through learning from historical performance.

## Planned Components

- Performance Learning
- Strategy Ranking
- Adaptive Optimization
- Continuous Improvement

## Completion Criteria

The system continuously improves decision quality using historical research results.

## Status

⬜ Planned

---

# Phase 8 — Live Trading

## Objective

Deploy the AI Alpha Engine to real financial markets.

## Planned Components

- Execution Engine
- Broker Integration
- Live Monitoring
- Safety Controls

## Completion Criteria

The AI Alpha Trading Agent operates safely and autonomously on live financial markets.

## Status

⬜ Planned

---

# Long-Term Objective

When completed, the AI Alpha Engine will:

- research financial markets
- generate market features
- develop trading strategies
- optimise strategy parameters
- evaluate statistical robustness
- manage portfolio risk
- understand market regimes
- recommend appropriate strategies
- select the highest-confidence opportunity
- learn from historical performance
- continuously improve decision quality
- power the AI Alpha Trading Agent

---

# Development Principle

Every phase follows the same development process:

- Architecture Review
- Design
- Test Driven Development
- Validation
- Documentation
- Git Integration

Progress is measured by architectural quality, deterministic behaviour and automated validation rather than implementation speed.

---

# Development Evolution

```text
Phase 1
Data Foundation

↓

Phase 2
Research Engine

↓

Phase 3
Strategy Optimization

↓

Phase 4
Risk & Portfolio Management

↓

Phase 5
Market Intelligence

↓

Phase 6
Alpha Decision Engine

↓

Phase 7
AI Learning Engine

↓

Phase 8
Live Trading
```
---

# Deferred / Post-Paper-Trading Enhancements

These items are intentionally deferred, **not rejected**. They remain on the roadmap so the project can reach evidence-producing paper trading without uncontrolled scope growth. Their priority will be reassessed using backtest and forward/paper-trading evidence.

## Risk and Portfolio

- portfolio correlation and concentration risk controls
- aggregate multi-position / multi-asset exposure limits
- portfolio allocation and weighting policies
- volatility targeting
- Value at Risk (VaR) and Expected Shortfall where evidence shows they add decision value
- Kelly sizing or a deliberately conservative fractional-Kelly variant
- Monte Carlo drawdown evidence as a possible hard risk gate after acceptable drawdown policy is empirically defined
- broker-aware authorization, margin/leverage constraints and live buying-power checks
- emergency forced liquidation / live execution kill-switch path

## Strategy Intelligence

- regime-based strategy selection only after regime-conditioned evidence is sufficiently robust
- additional strategies only when backtesting or paper trading demonstrates a real coverage gap
- Strategy Optimizer / adaptive parameter optimization only after the validation stack can control overfitting risk and evidence shows optimization is necessary

## Research / Validation Extensions

- portfolio-level cross-asset correlation and diversification validation
- richer stress/scenario testing if paper-trading discrepancies justify it
- recalibration of Validation Policy and Multi-Asset Policy thresholds from accumulated evidence rather than arbitrary expansion

## Deferral Principle

The current objective is not to build every institutional risk feature before the first forward test. The objective is to enter paper trading with a deterministic, testable and conservative core, measure where simulation and reality diverge, and use that evidence to decide which deferred capabilities earn implementation priority.

---

# Deferred Paper / Live Execution Backlog

These items are intentionally deferred to protect the current objective: validate a deterministic Paper Broker and then a deterministic Paper Trading Engine before introducing external connectivity or execution complexity. They are **not rejected**.

## Deferred to Later Paper-Trading Milestones

- **Real streaming market-data adapter** — deferred until deterministic Paper Trading Engine orchestration is proven, so API/network failures are not debugged at the same time as strategy/risk/execution logic.
- **Persistent account/order state and restart recovery** — deferred until the in-memory lifecycle is stable; required before unattended or long-duration paper trading so a process restart cannot lose broker state.
- **Operational monitoring, alerts and heartbeat/watchdog controls** — deferred until the continuous paper loop exists; required before unattended paper or live operation.
- **Order/event audit persistence** — in-memory evidence is sufficient for Broker v1 unit validation; durable audit storage is required before extended forward testing and live deployment.
- **Limit and stop order types** — deferred until market-order lifecycle is validated because adding order-type branching now would expand execution complexity without proving the basic boundary first.
- **Partial-fill and liquidity simulation** — deferred until paper results show that simple deterministic fills materially overstate execution quality; implementation priority should be evidence-driven.
- **Latency, queue position and richer market-microstructure models** — deferred because they are venue/timeframe dependent and should be added only if paper/live discrepancies show that the simpler slippage/spread model is insufficient.

## Deferred Until After Stable Paper Trading

- **Live broker/exchange adapter** — deferred until Paper Broker and Paper Trading Engine demonstrate stable order lifecycle, risk authorization, state handling and auditability. Live connectivity must replace the broker boundary, not force changes into Strategy or Risk Engine.
- **Broker-specific margin/leverage/buying-power rules** — deferred until a real broker/exchange target is selected because rules differ materially by venue and account type.
- **Emergency forced-liquidation execution path** — deferred until the live/paper execution state machine and broker adapter exist; Risk Engine currently blocks new risk but does not secretly become an execution engine.
- **Advanced broker reconciliation** — deferred until live connectivity exists; later required to compare internal state against broker/exchange positions, fills and balances.

## Existing Post-Paper Research / Risk Backlog

The previously documented deferred portfolio, risk and strategy-intelligence items remain active: portfolio correlation/concentration risk, aggregate exposure, portfolio allocation/weighting, volatility targeting, VaR/Expected Shortfall, fractional Kelly, Monte Carlo drawdown hard-gate policy, regime-based strategy selection, evidence-justified additional strategies and Strategy Optimizer/adaptive optimization.

## Deferral Rule

A deferred capability moves into active development only when one of three conditions is met: it is required for safe unattended paper/live operation; forward evidence exposes a material model gap; or the next architectural boundary cannot be completed safely without it. This prevents forgotten work without allowing the backlog to become uncontrolled scope creep.
