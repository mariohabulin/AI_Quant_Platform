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


### Extended Forward Run Readiness + Session Report v1
Move from 3-bar probes to supervised 30-60 bar forward evidence without expanding execution scope. Add a read-only report over the latest JSONL session so every extended run is judged by processed/rejected/rebase counts, signals, risk outcomes, paper fills, equity/P&L, max drawdown, final position, audit completeness and explicit `REAL_orders=0`. Longer unattended/cloud operation remains deferred until repeated supervised reports are clean.

### Coinbase Late-Trade Ordering Robustness v2
Extended forward observation exposed event-time reordering across separate Coinbase websocket messages. Add a bounded 2-second event-time reorder buffer before strict minute aggregation, persist the pending buffer in forward continuity state, and keep truly late trades fail-closed after the watermark. This adds a small intentional bar-finalization delay to preserve OHLCV correctness rather than silently dropping late trades.

- Completed-Bar Freshness Semantics hotfix: validate finalized Coinbase 1m bars against interval close so the 2s reorder watermark does not falsely mark healthy bars stale.

## Coinbase Transport Resilience v1
- Extended forward observation exposed a connection-boundary failure pattern after a healthy run.
- Review showed heartbeats and bounded reconnect already existed; the important gap was reconnect semantics and observability, not missing heartbeat subscription.
- Added explicit DISCONNECTED/RECONNECTED transport-control evidence, per-outage reconnect budgeting, partial-aggregator reset across disconnect, and a non-tradable reconnect rebase before normal trading resumes.
- Corrected session-end diagnosis so a Feed Health safety halt is recorded as `RUNTIME_HALTED` rather than `TRANSPORT_ENDED`.
- Next evidence gate: short live reconnect probe, then repeat the supervised 30-bar forward-paper run. Real execution remains structurally unavailable.

### Transport Failure Recovery v2
Validate bounded reconnect backoff and complete-audit fail-closed shutdown under real network/DNS failure before repeating the 30-bar extended forward-paper run.


## Reconnect Replay Reconciliation v1
- Completed Coinbase bars at or behind the already-accepted feed watermark are classified as provider replay and dropped before the trading/Feed Health pipeline.
- Replay drops remain audit-visible (`PROVIDER_REPLAY_DROPPED`) but do not consume the operational runtime consecutive-failure budget.
- Fresh forward bars still pass through strict freshness, ordering and missing-gap validation; real execution remains impossible.
- This change targets the observed 10:25 -> 10:23 -> 10:24 replay sequence that previously caused a false `RUNTIME_HALTED` during the supervised 30-bar run.

### Forward Operational Diagnostics v1
Instrument the proven 30-bar forward path before increasing duration. Report transport disconnect/reconnect quality, provider replay drops, market-time continuity/gap minutes, actionable signal rate and grouped Risk Engine rejection reasons. This is observability only; do not weaken Feed Health, Risk Engine or execution locks. Next gate after validation: supervised 60-bar forward run judged by both functional completion and operational quality.

### Transport Stability v1
Reduce dependence on recovery during long-lived Coinbase sessions without weakening fail-closed behavior. Keep the application-level `heartbeats` subscription, add protocol-level WebSocket PING keepalive for intermediaries, classify disconnect causes (`RESET`/`DNS`/`TIMEOUT`/`CLOSED`/`OTHER`), and record measured outage duration on reconnect/exhaustion. Extend the session report with total/max outage seconds and grouped disconnect causes. This milestone changes transport observability/keepalive only; strategy, Risk Engine, Feed Health and execution policy remain unchanged.

### Hybrid WS + REST Recovery v1
The 60-bar operational-quality run completed functionally but exposed persistent WebSocket resets and 144 minutes of observed market-time gap. The current objective is therefore to make continuity independent of a perfect socket: keep WebSocket as the low-latency primary feed, use Coinbase public 1-minute REST candles to reconstruct exact missing minutes after restart/reconnect, and resume trading only after complete continuity is proven. REST backfill is state catch-up only and must never create retroactive paper or real orders. If any required minute cannot be recovered exactly, the session fails closed with `BACKFILL_FATAL` and preserves continuity state.

### Startup Historical Catch-up v1
Hybrid recovery exposed a separate restart boundary: a supervised session resumed after an 896-minute offline gap, correctly refusing to treat it as a normal <=300-minute reconnect backfill. Add a startup-only bounded historical catch-up path (default maximum seven days) that uses the existing chunked Coinbase REST candle client, requires exact minute coverage, updates feed/strategy/risk/account state without retroactive trading, and resumes decisions only on a fresh live bar. The normal reconnect recovery limit remains 300 minutes and unchanged. Oversized or incomplete startup recovery remains fail-closed.
### Exact One-Minute Boundary Recovery
The first 60-bar Hybrid gate completed 60/60 with `BACKFILL failures=0` but diagnostics exposed one remaining minute of continuity loss: accepted `11:33`, reconnect, then live `11:35` with no `11:34` recovery record. Root cause: reconnect recovery was triggered only when the timestamp delta exceeded normal Feed Health `max_gap` (2m), so a 2m delta could hide exactly one missing 1m bar. At restart/reconnect boundaries, require exact timeframe continuity instead: any delta greater than 1m invokes REST recovery before trading resumes. Normal live Feed Health tolerance remains unchanged.



### Signal Activity & Strategy Behavior Analysis v1
Current diagnostic milestone: explain live-paper signal behavior before changing any strategy threshold. Persist read-only per-bar strategy diagnostics (including EMA relationship/spread for the active EMA crossover strategy) and summarize decision reasons in the forward-session report. This milestone must not alter Strategy Engine decisions, Risk Engine policy, Feed Health, PaperBroker execution, or the structural `REAL_orders=0` lock.

### Hybrid 60-Bar Verification Gate — PASS WITH TRANSPORT WARNING
The fresh supervised 60-bar gate passed the continuity/safety acceptance criteria: 60/60 processed, `MAX_BARS`, `audit_complete=True`, hybrid recovery failures=0, `observed_gap=0.0m`, and `REAL_orders=0`. Across a 306-minute market span, Hybrid WS + REST Recovery reconstructed 191 reconnect backfill bars plus 56 startup catch-up bars without losing market-time continuity or creating retroactive recovery orders. Post-Recovery Position Reconciliation also executed a live-time paper SELL after a recovery-detected bearish transition, while a later bullish BUY was correctly rejected by Risk Engine for failing the minimum reward/risk requirement.

Transport quality remains a warning, not a production pass: the local Windows run recorded 16 disconnects, 12 reconnects (75% success), about 2697.2 seconds total outage and about 1967.4 seconds maximum single outage, with RESET and DNS causes. Do not treat local WebSocket stability as production-ready. Before unattended 24/7 live deployment, require controlled cloud transport validation plus operational monitoring/alerting. Next duration gates may progress toward multi-hour/overnight/24-hour/multi-day soak testing, but transport quality must remain an explicit acceptance dimension.

### Post-Recovery Position Reconciliation v1
Forward evidence proved a position-lifecycle gap: a live EMA-crossover BUY opened a long at 2026-08-10 11:20 UTC, while deterministic audit reconstruction showed the corresponding bearish EMA20/EMA50 crossover at 12:27 UTC inside `STARTUP_CATCHUP_BAR`. Recovery correctly prohibited retroactive execution, but the later live strategy state was already BELOW/HOLD, so the exit event could be lost. Recovery must therefore observe strategy transitions without trading, persist a pending long-exit reconciliation when an actionable bearish transition occurs while a long is open, and execute that exit only on the first fresh live bar at the current price/time. The recovery bar itself remains non-actionable and `REAL orders=0` remains invariant.

### Strategy Behavior Diagnostics v2
Extend observability without changing trading policy. The deterministic forward report must distinguish live EMA relation transitions from recovery-detected crossovers, measure consecutive ABOVE/BELOW runs, and summarize open-position versus flat observation bars plus mark-to-market equity change while the position is open. This is diagnostic evidence only: do not tune EMA thresholds, alter signal semantics, bypass Risk Engine, weaken recovery safety, or change the structural `REAL_orders=0` lock. The Pending Hybrid 60-Bar Verification Gate remains required. The current 1m feed is a fast infrastructure-validation clock; multi-timeframe swing decision architecture remains a later explicit milestone rather than an accidental 1m strategy commitment.
