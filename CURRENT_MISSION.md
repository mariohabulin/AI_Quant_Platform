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

### Risk/Reward Decision Diagnostics v1
The Hybrid 60-Bar gate exposed a false boundary rejection on a live BUY at `63850.18`. The live bridge constructed an exact 3R target, but binary floating-point arithmetic recomputed the ratio as `2.9999999999999885`, causing the strict `< 3.0` comparison to reject a policy-compliant trade. Preserve the 3R policy while applying only a tightly bounded numerical-equality tolerance at the threshold; genuinely sub-threshold trades must remain rejected. Paper events and the forward report now retain planned entry, stop, target, computed reward/risk and required minimum evidence for every evaluated BUY. This milestone does not force trades, tune strategy signals, change stop/target construction, alter position sizing or weaken Risk Engine policy.

Local milestone validation is complete with 553/553 automated tests passing on Windows/Python 3.14.6. Next boundary: continue supervised longer-duration paper trading and operational-readiness work. Cloud transport validation plus monitoring remain mandatory before unattended 24/7 deployment.

### Operational Monitoring & Alerting v1
Promote monitoring from deferred observability into an explicit operational-readiness boundary before cloud soak testing. A new read-only monitor evaluates the latest forward audit and continuity state without importing or mutating Strategy, Risk, Feed Health, recovery or execution decisions. It classifies operator state as `OK`, `WARNING` or `CRITICAL`, emits stable alert codes and exposes process exit codes `0/1/2` for later cloud watchdog integration.

V1 covers missing/corrupt/stale audit and checkpoint state, fatal backfill/transport/runtime termination, REST recovery failure, non-zero REAL-order evidence, active Risk Engine kill switch, current transport disconnect/exhaustion and pending post-recovery reconciliation. New audit and continuity writes carry explicit `recorded_at` / `saved_at` timestamps. External notification delivery (email/Slack/SMS), process supervision and cloud scheduling remain separate adapters/deployment concerns; they must consume this evidence boundary rather than enter trading logic.

Operational Monitoring & Alerting v1 is locally validated with 572/572 automated tests passing on Windows/Python 3.14.6. The monitor classified the retained 60-bar runtime evidence as `OK / COMPLETED / MAX_BARS`, with matching audit/checkpoint age, `REAL_orders=0` and zero alerts. Next boundary: define Cloud Runtime Readiness and controlled cloud transport validation before multi-hour/overnight soak testing.

### Cloud Runtime Readiness v1
Define a provider-neutral, fail-closed pre-deployment gate before selecting or provisioning a paid cloud host. The gate validates an explicit PAPER-only execution lock, a positive bounded session, monitoring cadence below the stale-evidence threshold, colocated absolute audit/state paths on persistent writable storage, required runtime imports and the validated Python compatibility range. It performs only a temporary write/read/cleanup storage probe and never starts the trading runtime, places an order or provisions cloud infrastructure.

Local Windows/Python 3.14.6 validation is complete: 13/13 focused tests and the complete 585/585 repository suite pass. The real CLI readiness probe also passed all seven checks with explicit PAPER mode, real execution disabled, a five-bar bound, 30-second monitor cadence, 180-second stale threshold, absolute colocated paths, writable storage and importable runtime components. Next evidence boundary: choose a controlled cloud runtime and run a bounded transport/monitoring validation before any overnight or 24/7 soak test.

### Controlled Cloud Deployment Baseline v1
A Hetzner CPX22 paper-validation host is provisioned in Nuremberg with Ubuntu 24.04 LTS on x86, 2 vCPU, 4 GB RAM and 80 GB local SSD. Public IPv4/IPv6 networking is protected by a Hetzner Cloud Firewall that permits SSH and ICMP inbound while leaving required outbound connectivity available. Account 2FA, a passphrase-protected SSH key, package security updates and a controlled reboot/reconnect have been validated. No exchange credentials or real-order capability are present on the host.

Pre-deployment clean-clone validation exposed four Strategy Engine tests that depended on the locally retained but Git-ignored `data/AAPL.csv`. The tests now use a deterministic in-memory OHLCV fixture; production Strategy Engine and trading behavior are unchanged. Validation is complete with 9/9 focused Strategy Engine tests and 585/585 full-suite tests passing both in the isolated repository without local data artifacts and on Windows/Python 3.14.6.

Exact commit `6095960` is deployed at `/opt/ai-alpha` and passes 9/9 focused plus 585/585 full-suite tests on Ubuntu/Python 3.12.3. Root-only persistent storage at `/var/lib/ai-alpha` passed all seven Cloud Runtime Readiness checks. The first systemd-backed bounded PAPER smoke session completed 5/5 bars with process result `success/0`; the deterministic report returned `PASS`, `audit_complete=True`, zero rejected bars, zero transport disconnects, `observed_gap=0.0m` and `REAL=0`. Operational Monitoring returned `OK / COMPLETED / MAX_BARS` with zero alerts. The deployment baseline is closed; next boundary is controlled service supervision, restart/resume evidence and progressively longer cloud paper soak testing before any unattended 24/7 claim.

### Cloud Service Supervision & Restart Validation v1
Promote the proven transient systemd smoke path into a reviewed, repeatable PAPER-only service boundary without changing Strategy, Risk Engine, Feed Health, recovery or execution policy. The service must run as a passwordless/non-login `ai-alpha` identity, pass Cloud Runtime Readiness before every start, use fixed ten-bar and real-execution-disabled settings, write only to `/var/lib/ai-alpha`, restart only after failure with rate limiting, and stop through `SIGINT`. A separate persistent one-minute timer consumes the existing read-only Operational Monitoring exit-code contract and records evidence in journald; it cannot control the trading service.

Local implementation validation is complete: 10/10 supervision-contract tests, 22/22 combined supervision/report tests and the complete 595/595 suite pass both in the isolated clean repository and on Windows/Python 3.14.6. The broader focused supervision/readiness/monitor/runtime selection passes 72/72. systemd 255 offline security analysis classifies the paper and monitor services as `OK` with exposure scores 3.0 and 2.7. The forward report now exposes `resumed=True/False` as restart evidence.

Exact commit `accedf0` is installed on CPX22 and passes 22/22 focused plus 595/595 full-suite tests on Ubuntu/Python 3.12.3. Native `systemd-analyze verify` passed, installation activated nothing, the process runs under the non-login `ai-alpha` identity and `/var/lib/ai-alpha` remains private mode `0700`. Every start passed all seven Cloud Runtime Readiness checks. After three fresh durable bars, one controlled systemd restart stopped the process through `SIGINT`, then restored it with `resumed=True`; the provider replay at the watermark was safely dropped. The restarted session completed 10/10 bars with process `success/0`, report `PASS`, complete audit, zero rejected bars, zero disconnects, `observed_gap=0.0m`, `MAX_BARS` and `REAL=0`. The PAPER service is inactive and boot-disabled. The enabled one-minute read-only monitoring timer continues to report `OK / COMPLETED / MAX_BARS`, `REAL_orders=0` and zero alerts. This milestone is closed; next boundary is a bounded multi-hour cloud PAPER soak with the same supervision and evidence gates.

### Bounded Multi-Hour Cloud PAPER Soak v1 — PASS WITH ORDERING/RESTART WARNING
Exact commit `0d5477c` was installed on CPX22 with root-owned `AI_ALPHA_SESSION_BARS=180`. Native unit verification, the full 597/597 Ubuntu/Python 3.12.3 suite and all seven pre-start Cloud Runtime Readiness checks passed. The PAPER service remained boot-disabled while the independent read-only monitor timer remained enabled.

The first process safely rejected an out-of-order Coinbase trade after four separately recovered WebSocket disconnects. It exited with status 1 and systemd restarted it after ten seconds with `resumed=True`. The second process completed 180/180 fresh bars with zero rejected bars, complete audit, `MAX_BARS`, `observed_gap=0.0m`, two of two transport reconnects, 11.2 seconds total outage, zero recovery failures, one 3R PAPER fill, `REAL_orders=0` and final monitoring `OK / COMPLETED / MAX_BARS`. The final open PAPER position was `0.01971055`; its `+1.70` mark-to-market change is operational evidence, not a profitability conclusion.

Functional continuity and safety passed, but the complete gate is classified `PASS WITH ORDERING/RESTART WARNING`. The append-only forward audit did not retain the unexpected process exit, so the new healthy `SESSION_START` caused Operational Monitoring to hide the previous failed attempt. The strict late-trade rejection, two-second reorder bound, Strategy, Risk Engine, recovery and PAPER execution behavior remain unchanged.

### Restart Incident Visibility v1 — PASS
Exact commit `7d3a203` passes 39/39 focused tests and the complete 605/605 suite on both Windows/Python 3.14.6 and CPX22 Ubuntu/Python 3.12.3. Native target-unit verification passed, the non-activating installer deployed the new post-stop recorder, PAPER remained boot-disabled and the independent one-minute monitor timer remained enabled.

A controlled `SIGKILL` proved the complete lifecycle in real cloud supervision. systemd supplied `service_result=signal`, `exit_code=killed` and `exit_status=KILL`; the adapter durably appended `PROCESS_INCIDENT`; Operational Monitoring immediately reported `CRITICAL / FAILED / PROCESS_FAILURE`; systemd restarted once after ten seconds; all seven Cloud Runtime Readiness checks passed again; and the restored process started with `resumed=True`. The independent timer then retained `WARNING PREVIOUS_PROCESS_FAILURE` throughout the restarted attempt.

The restarted attempt completed 180/180 fresh bars with zero rejected bars, complete audit, `MAX_BARS`, `observed_gap=0.0m`, zero transport disconnects, zero recovery failures and `REAL_orders=0`. It recorded two exact-3R BUY evaluations reduced only by the exposure cap, one SELL, three filled PAPER orders, final equity `5002.09` and final open PAPER position `0.01963061`. The `+4.56` session equity change includes open-position mark-to-market movement and is not profitability evidence. After completion, both direct monitoring and the recurring timer continued to report `WARNING / COMPLETED / MAX_BARS` with the exact previous process failure visible. PAPER finished `inactive/dead/disabled`; monitoring remained `active/waiting/enabled`.

Restart Incident Visibility v1 is closed. The recorder remains evidence-only and Strategy, Coinbase ordering, Feed Health, recovery, Risk Engine, PaperBroker and the structural `REAL_orders=0` lock remain unchanged.

### Next Boundary — Overnight Cloud PAPER Soak v1 (Not Yet Activated)
The multi-hour functional gate and restart-incident visibility gate now authorize preparation for a bounded overnight PAPER soak. Before activation, define one reviewed root-owned overnight bar bound in the repository, reproduce focused/full tests, deploy the exact commit and rerun native unit plus Cloud Runtime Readiness verification. The PAPER service remains boot-disabled and no ad hoc host duration edit is authorized. Overnight evidence remains an operational endurance gate, not profitability evidence or permission for 24-hour, multi-day or real execution.
