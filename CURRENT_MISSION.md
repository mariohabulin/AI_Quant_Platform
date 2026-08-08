# CURRENT MISSION — Phase 3 Risk Engine v2

## Objective

Add deterministic account-protection guards on top of proven risk-based position sizing, without allowing the Risk Engine to become a strategy or execution engine.

## Current Priorities

- track peak mark-to-market equity causally
- reject new risk after maximum drawdown is reached
- latch the drawdown kill switch for the remainder of the backtest run
- enforce configurable daily and weekly loss limits
- reset daily/weekly baselines at calendar boundaries
- reset all protection state between independent backtests
- preserve Risk Engine v1 sizing and legacy no-risk-engine behavior
- keep all automated tests passing

## Risk Engine v2 Boundary

Protection guards authorize or reject **new positions**. They do not generate BUY/SELL signals and do not force-liquidate existing positions. Portfolio correlation, multi-position aggregate exposure, broker authorization and live emergency liquidation remain later milestones.

## Next Mission

After account protection is proven, review portfolio-level risk requirements and prepare the research stack for paper-trading integration.
