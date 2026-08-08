# CURRENT MISSION — Phase 3 Risk Engine v1

## Objective

Replace all-in-only research execution with an optional, deterministic risk-based position-sizing foundation while preserving full backward compatibility.

## Current Priorities

- calculate risk budget from account equity and risk-per-trade
- size long positions from entry price and protective stop distance
- enforce a configurable maximum position fraction
- expose explicit ALLOW / REDUCE / REJECT risk decisions
- integrate approved sizing into Backtesting Engine execution
- retain all-in behavior when Risk Engine is disabled
- preserve realistic commission, spread and slippage handling
- keep all automated tests passing

## Risk Engine v1 Boundary

This milestone sizes one long position at a time. It does not yet implement portfolio exposure, drawdown guards, loss limits, kill switches, correlation controls, dynamic strategy allocation or live-broker authorization.

## Next Mission

After position sizing is proven, add account/portfolio protection guards before paper trading.
