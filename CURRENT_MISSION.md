# CURRENT MISSION — Phase 3 Risk Engine v3

## Objective

Complete the pre-paper-trading Risk Engine with an explicit, configurable Trade Risk Policy while preserving strategy, risk and execution boundaries.

## Current Priorities

- validate long stop and target structure before entry
- support configurable minimum reward/risk without hardcoding 1:3
- reject trades that fail the configured reward/risk policy
- preserve v1 sizing and v2 account-protection guards
- persist planned stop/target/R:R evidence in completed trade history
- keep execution costs and affordability inside Backtesting Engine
- document deliberately deferred post-paper-trading risk enhancements
- keep all automated tests passing

## Definition of Done

Risk Engine v1-v3 provides position sizing, exposure caps, account-protection guards and explicit pre-trade structural/R:R authorization with deterministic evidence and backward compatibility.

## Next Mission

Close the current Risk Engine scope and begin Paper Trading Engine design/integration. Deferred portfolio and advanced risk controls remain explicitly tracked in ROADMAP.md.
