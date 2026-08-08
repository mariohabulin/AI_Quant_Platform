# CURRENT MISSION

## First Controlled Real-Time Paper Run — Pre-Flight Gate v1

The deterministic research, validation, risk, paper-trading, real-time market-data and operational-runtime foundations are implemented and regression-tested.

Current objective: validate the final safety/configuration boundary before the first supervised BTC/USD 1-minute real-time paper session.

Pre-flight requires:
- Alpaca credentials present without exposing secret values
- controlled BTC/USD / 1-minute provider scope
- explicit conservative Risk Engine guards
- clean or intentionally reconciled paper-account state
- writable checkpoint/restart destination
- order execution hard-disabled during pre-flight
- successful injected connectivity/auth/subscription probe
- runtime not halted/stopping

A failed check is fail-closed. Passing pre-flight does not authorize live-money trading.

Next after validation: run a short supervised real-time dry-run, inspect feed/runtime/audit behavior, then explicitly enable simulated PaperBroker execution for the first controlled forward paper session.

## Current Provider Path — Coinbase Public Feed

Alpaca onboarding/MFA is parked after repeated provider-side setup failures. The first controlled real-time dry-run now uses Coinbase Advanced Trade public `BTC-USD` market trades with no account/API credentials. Trades are aggregated into completed 1-minute OHLCV bars before entering the existing Feed Health / MarketDataEvent boundary. Execution remains hard-disabled until public connectivity, subscription, bar completion and runtime health are observed successfully.

- Coinbase public connectivity dry-run runner added: bounded BTC-USD observation, Feed Health gated, execution hard-OFF.
