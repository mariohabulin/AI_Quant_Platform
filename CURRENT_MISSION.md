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

### Current checkpoint — Coinbase Live Paper Bridge v1
Prove a bounded BTC-USD live-data path through Feed Health, Operational Runtime, Strategy Engine, Risk Engine and PaperBroker. Real order execution remains structurally unavailable. After the bounded probe is proven, evaluate observed behavior before expanding duration or execution scope.

### Forward Paper Session v1
Next controlled boundary: extend the proven live-paper bridge into a supervised bounded forward session with append-only JSONL audit evidence. The runner remains BTC-USD/1m, paper-only, and structurally unable to send real orders. Crash-transparent strategy-history recovery is intentionally deferred: current runtime checkpoints preserve account/risk/feed continuity but do not yet preserve the accumulating EMA history needed to claim exact strategy continuity after restart.

### Forward Paper Continuity / Recovery v1
Promoted to MUST-HAVE after the first live forward-paper BUY ended with an open paper position. Persist and restore broker/risk/feed/session state together with accumulated strategy history and the in-progress Coinbase 1m bucket. A one-time audited bootstrap migrates the proven v1 open position into the new continuity state. Runtime state/audit files are local operational artifacts and are no longer committed; the first live audit is retained under `docs/evidence/` as milestone evidence.

### Restart Gap Reconciliation v1
Validate restart/resume against live Coinbase data: restore the open paper position, rebase one fresh post-restart boundary bar without trading it, then require subsequent bars to pass the normal feed-health policy. Real execution remains structurally unavailable.
