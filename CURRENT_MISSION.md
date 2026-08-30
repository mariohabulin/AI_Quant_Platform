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

### Overnight Cloud PAPER Soak v1 — FAIL WITH SAFETY PRESERVED
Exact commit `d96c981` was deployed to CPX22 with the reviewed root-owned 720-bar bound. Windows and cloud validation each passed 26/26 focused tests and the complete 605/605 suite; native unit verification and all seven Cloud Runtime Readiness checks also passed before activation. PAPER remained boot-disabled and `REAL_orders=0` remained structurally enforced.

The run started at 2026-08-13 17:37 UTC with `resumed=True`, but it did not reach one clean 720-bar `MAX_BARS` boundary. Seven distinct processes failed closed with `ValueError: Out-of-order Coinbase trade rejected.` and systemd automatically restarted each one. Only two WebSocket disconnects were observed, both followed by successful reconnection; most ordering failures therefore did not immediately follow a recorded transport reconnect. The service remained healthy enough to resume each time, but `NRestarts=7` and repeated process incidents make the endurance gate an unambiguous failure. Restarting also reset the per-process 720-bar counter, so the nominal twelve-hour bound did not bound the complete supervised activation.

The final process was deliberately stopped at 2026-08-14 07:56 UTC. systemd delivered SIGINT and recorded a clean result; the final durable account evidence was flat with equity `4977.59` and `REAL_orders=0`. That controlled stop exposed a second lifecycle defect: `main()` returned the accepted status 130 without appending `SESSION_END`, so the monitor later mislabeled the parked session as stale `RUNNING` and the deterministic report correctly refused the incomplete audit. PAPER and both monitoring units are now inactive; PAPER remains disabled, the monitor timer remains enabled but stopped, and all retained journal/audit evidence is preserved.

This gate is classified **FAIL WITH SAFETY PRESERVED**. No 24-hour or multi-day progression is authorized. The failure is operational, not a profitability conclusion: real execution remained impossible, late data was rejected rather than silently traded, continuity survived all restarts, and process incidents remained visible.

### Overnight Soak Failure Closure v1 — PASS
Exact closure revision `93b7565` passed 97/97 focused tests and the complete 615/615 suite on Windows/Python 3.14.6 before commit/push. CPX22 then fast-forwarded to that exact revision and reproduced 97/97 focused plus 615/615 complete Ubuntu/Python 3.12 tests. The installer remained non-activating, native unit verification passed, the installed service exposed the reviewed two-start envelope, and all seven Cloud Runtime Readiness checks passed with the root-owned 720-bar bound. PAPER remained boot-disabled and real execution remained impossible.

The short cloud diagnostic started at 2026-08-14 09:57 UTC with `resumed=True`, reconstructed 121 startup catch-up bars without retroactive execution and processed six fresh contiguous PAPER bars. systemd remained `active/running` with `NRestarts=0`; direct Operational Monitoring returned `OK / RUNNING`, fresh audit/checkpoint evidence, zero alerts and `REAL_orders=0`.

The controlled stop at 10:02 UTC delivered SIGINT and completed with systemd `Result=success`, `ExecMainStatus=0` and `NRestarts=0`. The attempt durably closed as `SESSION_END reason=OPERATOR_STOP`; Operational Monitoring returned the intended `WARNING / STOPPED / OPERATOR_STOP` without stale-running alerts, and the forward report returned the intended non-gate `FAIL` with `audit_complete=True`. No new `PROCESS_INCIDENT` followed the new session, continuity reported `observed_gap=0.0m`, and the final position remained flat. The typed `ORDERING_FATAL` branch did not occur during this short live probe; its timing evidence, persistence and root-cause behavior remain covered by the deterministic focused tests rather than being claimed as live evidence.

Activation preparation also exposed a systemd lifecycle detail: a successful inactive unit may be garbage-collected, causing `reset-failed` to report `Unit ai-alpha-paper.service not loaded`. In that exact state no retained start-limit counter exists. The runbook now uses a guarded branch that verifies the installed unit is loadable before a direct explicit start and aborts on every other reset error; it never hides failures with `|| true`. The two-start policy, PAPER configuration and runtime code are unchanged.

Final parked state is PAPER `inactive/dead/disabled`, monitor timer `inactive/dead/enabled`, repository clean on `93b7565`, last terminal audit reason `OPERATOR_STOP` and `REAL_orders=0`. Overnight Soak Failure Closure v1 is closed. The next authorized evidence boundary is one clean 720-bar PAPER soak with no injected restart or failure; 24-hour, multi-day, unattended production and real execution remain gated until that run reaches `MAX_BARS` with every existing acceptance condition satisfied.

### Coinbase Provider Message Sequence Integrity v1 — PASS
The next non-injected 720-bar attempt on exact revision `e0592ff` again failed
safely before `MAX_BARS`. It processed 266 fresh bars before a 19.637-second
late-trade fatal, recovered through the one allowed automatic process start,
then processed 46 fresh bars before a second 56.435-second late-trade fatal.
systemd blocked a third process start at the reviewed two-start boundary.
Operational Monitoring retained `CRITICAL / FAILED / ORDERING_FATAL`, the
deterministic report remained structurally complete but non-passing, and
`REAL_orders=0` remained invariant. No transport disconnect immediately
preceded either late trade, so the retained evidence did not justify widening
the two-second event-time window.

The root evidence gap was provider-envelope ordering: Advanced Trade documents
that most messages carry increasing per-product `sequence_num` values, that a
larger jump identifies a dropped message, and that a lower value can be ignored
or can represent an out-of-order message. The prior transport ignored this
field and passed every envelope into trade-time aggregation, so a replayed whole
message could be misclassified as a genuinely late new trade. The old audit did
not retain message sequence or `trade_id`, preventing a definitive distinction
after the incident.

The first local implementation validated every real `market_trades` envelope
before OHLCV aggregation. Lower/equal messages are wholly discarded and audited
as `PROVIDER_MESSAGE_REPLAY_DROPPED`; gaps or missing/invalid sequence close the
untrusted socket and use the existing bounded reconnect/exact-REST-continuity
path. A partial minute that began before the reconnected socket's trusted
full-minute boundary is audit-dropped and REST-reconstructed before a later
fully observed live bar may trade; the report counts these boundary drops.
Heartbeats cannot reset the sequence-recovery budget; a valid market-trades
payload is required. Reconnect exhaustion remains terminal. A late trade in a correctly
sequenced envelope still fails closed under the unchanged two-second watermark,
now with message sequence/time, event type and `trade_id` evidence. The forward
report separately counts message replay drops, and handled replay evidence does
not create a monitoring alert.

That first implementation passed 112/112 focused and 630/630 complete tests on
Windows and CPX22, was committed as `066852b`, and passed all seven readiness
checks. Its short cloud diagnostic was deliberately stopped after the transport
repeatedly reported false gaps `0 -> 3/4/5`; systemd closed cleanly with
`success/0`, `NRestarts=0`, PAPER inactive/disabled and `REAL_orders=0`.

A separate read-only raw WebSocket probe then captured the missing contract
detail: the single connection emitted `market_trades` sequence 0,
`subscriptions` sequences 1 and 2, `market_trades` sequence 3, `heartbeats`
sequence 4 and an uninterrupted cross-channel stream through 39. Filtering by
channel before validation had hidden legitimate intervening envelopes.

The correction now validates every sequence-bearing provider envelope before
channel routing while allowing only `market_trades` into OHLCV aggregation.
Forward gaps on any sequenced channel remain fail-closed and now retain the
observed provider channel. Missing sequence remains fatal for a market payload;
non-market control envelopes without the optional field remain transparent.
Cross-channel cloud-fixture regression plus all existing behavior passes
114/114 focused tests and the complete 632/632 local suite. Windows committed
the exact correction as `4ff9070`; CPX22 fast-forwarded to that revision and
reproduced 114/114 focused plus 632/632 complete Ubuntu/Python 3.12 tests. The
non-activating installer left PAPER inactive/disabled, and all seven Cloud
Runtime Readiness checks passed with the reviewed 720-bar bound.

The second short diagnostic started at 2026-08-15 18:24 UTC with
`resumed=True`, reconstructed 1559 startup-catch-up bars without retroactive
execution and processed 13 fresh contiguous bars. It recorded one intended
post-recovery SELL that flattened the inherited PAPER position, then 12 HOLDs.
The report retained zero rejected bars, zero rebases, zero disconnects,
reconnects, exhaustion, bar replays, message replays, sequence-boundary drops or
recovery failures; market continuity covered 1571 expected minutes with
`observed_gap=0.0m` and `REAL_orders=0`.

The controlled SIGINT stop closed the audit as `OPERATOR_STOP`; systemd retained
`success/0`, `NRestarts=0` and PAPER `inactive/dead/disabled`. Operational
Monitoring returned only the intended `WARNING / STOPPED / OPERATOR_STOP`; the
forward report was structurally complete and intentionally non-passing because
only `MAX_BARS` may pass an endurance gate. Final position was flat, no process
incident was created and the timer remained inactive/dead/enabled.

Cross-channel provider sequence integrity is now locally and cloud verified.
The next authorized boundary is one clean non-injected 720-bar PAPER soak on the
documented closure revision. It must still reach `MAX_BARS` with every existing
continuity, transport, supervision, monitoring and `REAL_orders=0` acceptance
condition. The 24-hour, multi-day, unattended-production and real-execution
gates remain closed.

### Coinbase Market-Trades Snapshot Boundary v1 — LOCAL IMPLEMENTATION READY
The clean 720-bar attempt on exact revision `46ed877` ran from 2026-08-15
19:11 UTC until 2026-08-16 05:13 UTC and completed 603 fresh bars before one
automatic restart. The fatal attempt retained complete audit evidence, six
filled PAPER orders, exact 635-minute market continuity, zero rejected bars,
zero disconnects/reconnects/exhaustion/replays/sequence-boundary drops/recovery
failures, final flat position and `REAL_orders=0`. It therefore validated the
cross-channel sequence correction but failed the endurance gate at 603/720.

The decisive record was a correctly sequenced `market_trades` envelope at
`sequence_num=102964`, message time `05:13:56.580642159Z`, with
`event_type=snapshot`. It carried trade `1070883132` from
`05:12:54.738994Z`, 58.912 seconds behind the two-second event-time watermark.
This is provider snapshot history, not evidence that the live update tolerance
should be widened.

The local correction validates the full cross-channel envelope first, converts
every explicit market-trades snapshot into audit-visible
`PROVIDER_SNAPSHOT_BOUNDARY`, and prevents its trades from entering incremental
OHLCV. The in-progress bucket is reset, the partial boundary minute is recorded
as `PROVIDER_SNAPSHOT_BOUNDARY_BAR_DROPPED`, and exact REST continuity is applied
without retroactive orders before the next full live minute. Startup snapshots
preserve `RESTART` catch-up semantics. The report adds `snapshot_boundaries` and
`snapshot_boundary_drops`; handled boundaries remain monitoring-neutral, while
a truly late `update` remains fatal under the unchanged two-second rule.

Local TDD validation passes 119/119 focused provider/forward/report/monitoring/
supervision tests and the complete 637/637 repository suite. Next boundary:
apply the exact patch on Windows, reproduce both suites, commit/push, deploy
without activation, reproduce cloud tests/readiness, then run a short snapshot-
aware diagnostic before authorizing another clean 720-bar attempt. PAPER and
monitoring remain parked; 24-hour, multi-day, unattended-production and real
execution gates remain closed.

### Coinbase Post-Snapshot Trade Quarantine v1 — CLOUD DIAGNOSTIC VERIFIED
Snapshot Boundary v1 was reproduced on Windows and CPX22 as exact revision
`370664d`, with 119/119 focused and 637/637 complete tests, a non-activating
install and all seven Cloud Runtime Readiness checks passing. A controlled live
diagnostic then processed 112 contiguous fresh bars after 204 startup-catch-up
bars. It observed one snapshot boundary/drop, no transport or recovery failure,
`observed_gap=0.0m`, clean `OPERATOR_STOP` and `REAL_orders=0`.

The next non-injected 720-bar attempt did not pass. Its first process completed
443 fresh bars before an in-band snapshot at sequence `10784` was followed by a
correctly sequenced update `10786` carrying trade `1071015409` from
`21:33:09.501792Z`; the trade was 57.988 seconds behind the live watermark.
The single allowed recovery process completed 27 bars before snapshot `7423`
was followed by update `7425` carrying trade `1071026960` from
`22:02:55.664795Z`, 6.013 seconds behind the watermark. Both attempts closed
with complete `ORDERING_FATAL` evidence, systemd enforced the two-start ceiling,
and `REAL_orders=0` remained invariant. PAPER and both monitoring units are now
inactive; PAPER remains disabled and the timer remains enabled but stopped.

The local correction gives every snapshot—including nonzero in-band
snapshots—a persistent trusted event-time floor. Subsequent trades older than
that floor are removed before the reorder heap and audited as
`PROVIDER_SNAPSHOT_QUARANTINE_TRADES_DROPPED`; the report totals them as
`snapshot_quarantine_trades`. The boundary minute remains non-tradable and exact
REST recovery restores it before the first complete live minute reaches the
decision pipeline. A true late trade at or after the floor remains fatal under
the unchanged two-second policy.

TDD reproduces both exact cloud sequence/trade pairs, verifies the quarantine
continues after PAPER processing resumes, preserves startup REST recovery,
proves invalid timestamps are not hidden and proves a genuine post-boundary late
trade still closes `ORDERING_FATAL`. Windows/Python 3.14.6 reproduced 124/124
focused and 642/642 complete tests, then committed and pushed exact revision
`e7a95ac`. CPX22 fast-forwarded to that revision and reproduced the same 124/124
focused and 642/642 complete Ubuntu/Python 3.12 suites. The installer activated
nothing, and all seven Cloud Runtime Readiness checks passed with the reviewed
720-bar bound.

The controlled cloud diagnostic encountered one provider snapshot and proved
the new boundary against live traffic: 630 snapshot-era trades were quarantined
before aggregation, one partial boundary bar was explicitly dropped, and exact
recovery completed 942 startup-catch-up bars before PAPER resumed. Six fresh
contiguous bars then completed as HOLD with zero rejected bars, zero PAPER or
REAL orders, zero transport disconnects/reconnects/exhaustion/replay drops,
zero recovery failures and exact 947-minute market continuity
(`observed_gap=0.0m`). The process remained healthy with `NRestarts=0`; no
`LATE_TRADE_REJECTED`, `ORDERING_FATAL` or new process incident occurred.

Controlled SIGINT closed the audit as `OPERATOR_STOP`, so the short report is
intentionally `FAIL` rather than an endurance `MAX_BARS` pass. Monitoring
reported only the historical `PREVIOUS_PROCESS_FAILURE` and expected
`OPERATOR_STOP` warnings; safety remained `REAL_orders=0`. Final position was
flat, all three units are inactive, PAPER remains boot-disabled, the timer
remains enabled but stopped, and the cloud repository is clean on `e7a95ac`.

Coinbase Post-Snapshot Trade Quarantine v1 is closed. The next authorized
boundary is one clean non-injected 720-bar PAPER soak with `NRestarts=0` and all
existing acceptance conditions. No 24-hour, multi-day, unattended-production
or real-execution progression is authorized.

### Clean 720-Bar Cloud PAPER Soak v1 — PASS
Exact revision `db5615e` was cleanly reproduced on Windows and CPX22 with 17/17
supervision tests and the complete 642/642 repository suite. Before activation,
the cloud repository was clean, all units were parked, PAPER remained
boot-disabled, and all seven Cloud Runtime Readiness checks passed under the
`ai-alpha` identity with the reviewed 720-bar bound and real execution disabled.

The non-injected gate started on 2026-08-17 at 14:19 UTC and completed normally
on 2026-08-18 at 02:32 UTC. systemd reported `Result=success`,
`ExecMainStatus=0`, `NRestarts=0` and final PAPER state
`inactive/dead/disabled`. The deterministic report returned `PASS`,
`audit_complete=True` and `MAX_BARS` with exactly 720 processed bars, zero
rejected bars and zero rebases. All 20 PAPER orders filled, no REAL order was
possible, and the final position was flat.

Provider and recovery evidence remained exact throughout the run: 13 snapshot
boundaries produced 13 explicit boundary drops, 5,777 snapshot-era trades were
quarantined before aggregation, 29 startup-catch-up bars and 12 exact REST
backfill bars were consumed without retroactive execution, and recovery
failures remained zero. There were no transport disconnects, reconnects,
exhaustion, provider replay drops, message replay drops or sequence-boundary
drops. Market continuity covered all 760 expected minutes with
`observed_gap=0.0m`.

Operational Monitoring independently returned
`OK / COMPLETED / MAX_BARS`, `REAL_orders=0` and zero alerts. The final PAPER
equity moved from 4,983.17 to 4,986.83 (`net_pnl=+3.66`, maximum drawdown
0.1610%), but this single bounded run is operational evidence, not a
profitability claim. After review, PAPER, the monitor service and the monitor
timer were all parked; the timer remains enabled but stopped, and the cloud
repository remains clean on `db5615e`.

The clean overnight gate is closed. The next authorized repository change is
reviewed preparation for a bounded 24-hour PAPER gate, expected to use 1,440
fresh one-minute bars while preserving every current safety, continuity,
supervision and monitoring condition. At closure, the installed bound remained
720 pending that separate repository change and non-activating deployment
review. Multi-day soak, unattended production and real execution remained
closed.

### Bounded 24-Hour Cloud PAPER Soak v1 — PREPARATION
The successful clean 720-bar gate authorizes the next bounded duration step.
The committed root-controlled configuration now sets
`AI_ALPHA_SESSION_BARS=1440`, exactly 24 hours of fresh one-minute bars. Cloud
Runtime Readiness and the forward runner still consume the same installed
value, so validation and execution cannot drift. This preparation changes no
market-data, Strategy, Risk, recovery, broker or monitoring logic; PAPER stays
boot-disabled and real execution remains structurally disabled.

The reviewed run is non-injected: do not restart the process or introduce a
failure. Acceptance requires 1,440/1,440 processed bars, zero rejected bars,
zero rebases, `audit_complete=True`, normal `MAX_BARS`, exact expected market
continuity with `observed_gap=0.0m`, zero recovery failures, zero reconnect
exhaustion and 100% reconnect success if any disconnect occurs. All provider
snapshot, quarantine, replay, recovery and transport counters remain reviewable
rather than being hidden by successful continuity repair.

The service must finish with systemd `Result=success`, `ExecMainStatus=0` and
`NRestarts=0`. Final Operational Monitoring must be `OK / COMPLETED / MAX_BARS`
with zero alerts and `REAL_orders=0`. Any process incident, automatic restart,
`PREVIOUS_PROCESS_FAILURE`, `WARNING` or `CRITICAL` decision blocks the gate
pending explicit review. The final PAPER position and P&L remain reportable
observations, not acceptance targets.

Next, reproduce the focused and complete suites on Windows, commit and push the
exact revision, deploy it through the non-activating installer, repeat the same
tests and all seven readiness checks on CPX22, then explicitly start one
reviewed bounded run. A pass will be operational endurance evidence, not a
profitability claim or live-money authorization. Multi-day soak, unattended
production and real execution remain closed until later reviewed gates.

### Bounded 24-Hour Cloud PAPER Soak v1 — PASS
Exact preparation revision `f0a7ea8` was reproduced on Windows and CPX22 with
31/31 combined supervision/readiness tests and the complete 643/643 repository
suite. The installer remained non-activating, the committed and installed bound
was `AI_ALPHA_SESSION_BARS=1440`, native unit verification was clean, and all
seven Cloud Runtime Readiness checks passed before the explicit start. PAPER
remained boot-disabled and real execution remained structurally impossible.

The non-injected gate started at 2026-08-18 10:44 UTC and ended normally at
2026-08-19 11:00 UTC. One process completed all 1,440 fresh bars with systemd
`Result=success`, `ExecMainStatus=0` and `NRestarts=0`; the deterministic report
returned `PASS`, `audit_complete=True`, `resumed=True`, zero rejected bars, zero
rebases and `MAX_BARS`. It recorded 12 BUY, 12 SELL and 1,416 HOLD signals,
23/23 filled PAPER orders and `REAL=0`.

The 24-hour transport evidence included six genuine disconnects and six
successful reconnects: 100% recovery, 34.9 seconds total outage and 5.8 seconds
maximum outage, with zero exhaustion or replay drops. Provider boundaries
remained explicit: 15 snapshot boundaries/drops and 4,126 quarantined
snapshot-era trades. Exact non-tradable recovery consumed 493 startup-catch-up
and 15 REST backfill bars with zero failures. Continuity covered all
1,947/1,947 expected market minutes with `observed_gap=0.0m`.

Operational Monitoring independently returned
`OK / COMPLETED / MAX_BARS`, `REAL_orders=0` and zero alerts. Equity moved from
4,986.83 to 4,992.03 (`net_pnl=+5.20`, maximum drawdown 0.2289%). The final
PAPER position remained open at 0.01938861 BTC; this is valid report evidence,
not a gate failure or live position. Neither P&L nor final position is treated
as a profitability conclusion.

After review, PAPER, the monitor service and the timer were all parked. PAPER
is `inactive/dead/disabled`; the timer is `inactive/dead/enabled`; every unit
retains `Result=success`, and CPX22 is clean on `f0a7ea8`. The bounded 24-hour
gate is closed as PASS. The next authorized change is repository-reviewed
multi-day PAPER-soak preparation with an explicit duration and acceptance
contract. Unattended production and all real execution remain closed.

### Bounded Three-Day Cloud PAPER Soak v1 — PREPARATION
The successful 1,440-bar gate authorizes one further infrastructure-duration
step. The committed root-controlled configuration now sets
`AI_ALPHA_SESSION_BARS=4320`, exactly three days of fresh one-minute bars. Cloud
Runtime Readiness and the forward runner continue to consume the same installed
value. This preparation changes no provider validation, aggregation, Strategy,
Risk, recovery, broker, persistence or monitoring behavior; PAPER remains
boot-disabled and real execution remains structurally impossible.

The reviewed run is non-injected. Acceptance requires 4,320/4,320 processed
bars, zero rejected bars, zero rebases, `audit_complete=True`, normal
`MAX_BARS`, exact expected market continuity with `observed_gap=0.0m`, zero
recovery failures, zero reconnect exhaustion and 100% reconnect success if any
disconnect occurs. Snapshot boundaries, quarantined trades, replay counters,
backfills, outage causes and durations remain explicit evidence even when
continuity is successfully repaired.

The service must finish with systemd `Result=success`, `ExecMainStatus=0` and
`NRestarts=0`. Final Operational Monitoring must be `OK / COMPLETED / MAX_BARS`
with zero alerts and `REAL_orders=0`. Any incident, automatic restart,
`PREVIOUS_PROCESS_FAILURE`, `WARNING` or `CRITICAL` result blocks a clean pass.
Final systemd CPU time, memory peak and swap/OOM evidence must be captured and
reviewed for unexpected resource growth; no arbitrary profitability or final-
position target is added to this infrastructure gate.

Next, reproduce focused/full Windows tests, commit and push the exact revision,
deploy it through the non-activating installer, repeat the tests and all seven
readiness checks on CPX22, then explicitly start one bounded run. A pass will
authorize Strategy Evaluation v1 preparation, not unattended production or
live-money execution. Those remain separately reviewed future boundaries.

### Bounded Three-Day Cloud PAPER Soak v1 — RUNNING
Exact preparation revision `62e517c` was reproduced with 31/31 focused and
643/643 complete tests, installed through the non-activating path and verified
by all seven Cloud Runtime Readiness checks with the committed
`AI_ALPHA_SESSION_BARS=4320` bound. The operator then explicitly started one
non-injected run at 2026-08-19 15:14 UTC; PAPER remains boot-disabled and real
execution remains structurally impossible.

The reviewed 2026-08-20 12:45 UTC progress snapshot retains systemd
`Result=success`, `ExecMainStatus=0`, `NRestarts=0` and PAPER
`active/running`. The monitor timer is `active/waiting`; three recent one-shot
cycles independently returned `OK / RUNNING / RUNNING`, fresh audit/checkpoint
ages, `REAL_orders=0` and zero alerts. Recent PAPER bars remained current with
equity 5,081.14, final observed position flat and 27 PAPER orders. These are
interim operational observations only. The process must remain untouched until
normal completion or a genuine safety event, and only the complete final report
plus systemd/resource evidence can decide the three-day gate.

### Bounded Three-Day Cloud PAPER Soak v1 — PASS
The untouched non-injected process ran on exact revision `62e517c` from
2026-08-19 15:14 UTC to normal completion at 2026-08-22 15:55 UTC. systemd
retained `Result=success`, `ExecMainStatus=0` and `NRestarts=0`; the final
report returned `PASS`, `audit_complete=True`, `resumed=True` and `MAX_BARS`
with all 4,320 fresh bars processed, zero rejected bars and zero rebases. It
recorded 44 BUY, 47 SELL and 4,229 HOLD signals, 89/89 filled PAPER orders,
zero Risk rejects, 44 exact 3R evaluations, a flat final PAPER position and
`REAL=0`.

The real transport evidence exercised recovery without losing continuity:
15 disconnects recovered 15 times for 100% success, 88.2 seconds total outage
and 6.0 seconds maximum outage, with zero exhaustion, bar replay, message replay
or sequence-boundary drop. Thirty-nine provider snapshot boundaries produced
39 explicit boundary-bar drops and quarantined 18,200 snapshot-era trades
before aggregation. Exact non-tradable recovery consumed 255 startup-catch-up
and 40 REST backfill bars with zero failure or retroactive order. Continuity
covered all 4,614/4,614 expected market minutes with `observed_gap=0.0m`.

Operational Monitoring independently returned `OK / COMPLETED / MAX_BARS`,
zero alerts and `REAL_orders=0`. Equity moved from 5,037.72 to 5,134.30
(`net_pnl=+96.58`, maximum drawdown 1.1202%); this remains infrastructure and
strategy-behavior evidence rather than a profitability claim. Final systemd
resource evidence was 59 minutes 43.025 seconds CPU time, 97.0 MB memory peak,
0 B swap peak and no kernel OOM/killed-process evidence.

After review, PAPER, the monitor service and the timer were parked. PAPER is
`inactive/dead/disabled`; the monitor service is `inactive/dead/static`; the
timer is `inactive/dead/enabled`; every unit retains `Result=success`, and the
cloud repository remains clean on `62e517c`. The bounded three-day
infrastructure gate is closed as PASS. This authorizes controlled Strategy
Evaluation Protocol integration and first-candidate preparation only;
unattended production and all live-money execution remain unauthorized.

### Strategy Evaluation Protocol v1 — CLOUD INTEGRATION PASS
Repository-only preparation now freezes the strategy-research decision before
any candidate is tested. A candidate declaration binds identity, hypothesis,
parameter-set ID, data version, timeframe and exact asset scope. The existing
Multi-Asset Validator is then run twice with identical chronological,
walk-forward and statistical settings: once with reviewed nonzero baseline
costs and once with a component-wise equal-or-higher cost-stress profile.

Promotion requires both aggregate results to be `VALIDATED`, at least five
non-overlapping walk-forward windows and 30 unseen completed trades per asset,
and no unseen OOS drawdown above the configured 20% research ceiling. A hard
edge or evidence-integrity failure is `REJECTED`; incomplete but non-rejected
evidence is `RESEARCH_HOLD`; complete evidence is `PAPER_CANDIDATE`. Every
report fixes `live_execution_authorized=False`; even `PAPER_CANDIDATE` means
only eligibility for a separately bounded forward-PAPER gate.

The implementation is isolated in `strategy_evaluation_protocol.py` and adds
no cloud/runtime, provider, Strategy, Risk, broker, persistence or systemd
behavior. TDD passes 84/84 focused validation/protocol tests and the complete
663/663 suite. Windows/Python 3.14.6 reproduced both suites and committed the
implementation as exact revision `b69f5b1`; the three-day closure followed as
`9a063fa` without changing protocol behavior.

After the external three-day gate passed, the parked CPX22 repository
fast-forwarded non-activating from `62e517c` through both revisions to exact
`9a063fa`. Ubuntu/Python 3.12 reproduced 20/20 standalone protocol tests,
84/84 focused protocol/validation tests and the complete 663/663 suite. The
standard installer explicitly started or enabled nothing, and all seven Cloud
Runtime Readiness checks passed with PAPER mode, real execution disabled and
the committed 4,320-bar bound.

Final cloud state remains deliberately parked: PAPER is
`inactive/dead/disabled`, the monitor service is `inactive/dead/static`, the
timer is `inactive/dead/enabled`, every unit retains `Result=success`, and the
repository is clean on `9a063fa`. Strategy Evaluation Protocol v1 cloud
integration is closed as PASS. The next authorized action is pre-registration
and offline execution of the first strategy candidate evaluation. No protocol
result can authorize live execution.

### Research Execution Timing Integrity v1 — LOCAL PREPARATION

The first candidate has not been pre-registered or evaluated. Architecture
review found that the legacy Backtesting Engine calculates a signal from the
current completed close and, by default, can fill on that same close. Such a
fill is not attainable after the close becomes known and could manufacture an
optimistic research edge.

The candidate protocol now requires causal `next_bar_open` execution while the
general Backtesting Engine keeps `same_bar_close` only as an explicit legacy
default. Each completed trade records its originating signal indexes separately
from its entry/exit execution indexes. Final-bar signals are never executed;
open terminal positions retain the frozen `force_close_at_final_close` policy
without receiving a synthetic strategy exit signal. The benchmark is aligned
to first-bar Open entry and final-bar Close exit.

The timing choice flows through OOS, walk-forward, Strategy Validation and
Multi-Asset Validation for both baseline and cost-stress passes. Protocol v1
rejects any other execution timing or terminal policy and includes all
assumptions in its report. The change does not alter Strategy logic, candidate
parameters, Risk policy, provider/runtime behavior, PaperBroker, systemd or the
structural real-execution lock.

Local evidence passes 130/130 focused research-stack tests and the complete
684/684 suite, plus direct divergent Open/Close execution checks and clean
syntax/diff validation. Windows reproduction, Git integration and cloud
non-activating verification remain required before candidate pre-registration.
The next research step after closure is an immutable first-candidate/data/cost
declaration, not parameter optimization.

### Research Execution Timing Integrity v1 — CLOUD INTEGRATION PASS

Windows/Python 3.14.6 reproduced 130/130 focused research-stack tests and the
complete 684/684 suite. The exact 19-file change was committed as `daf6c5d`
(`Add Research Execution Timing Integrity v1`), pushed to `origin/main`, and
left the local repository clean.

The parked cloud repository then fast-forwarded from exact `7f2e7fc` to
`daf6c5d` without activating PAPER or monitoring. Ubuntu/Python 3.12 reproduced
the same 130/130 focused and 684/684 complete suites. The standard installer
again confirmed that it started and enabled nothing.

One manual readiness invocation omitted the systemd environment and therefore
failed transparently with unset configuration values. It did not start a
service, change persistent state or create a process incident. Repeating the
gate as the `ai-alpha` service identity with the installed 4,320-bar bound and
the exact PAPER/runtime/monitoring/real-execution environment produced all
seven `PASS` checks, including the persistent-storage probe.

Final cloud state remains parked and clean on `daf6c5d`: PAPER is
`inactive/dead/disabled`, monitor service is `inactive/dead/static`, monitor
timer is `inactive/dead/enabled`, all unit results are `success`, and retained
restart counts are zero. Research Execution Timing Integrity v1 is closed as
PASS. The next authorized action is immutable pre-registration of the first
strategy candidate, dataset evidence and reviewed cost profiles; optimization,
bounded forward PAPER and live-money execution remain separate later gates.

### First Strategy Candidate Pre-registration v1 — LOCAL PREPARATION

The first candidate is now declared but deliberately unevaluated:
`ema-crossover-20-50-btc-eth-native-6h-v1`, using the existing long-only EMA
20/50 implementation on exact `BTC-USD` and `ETH-USD` native six-hour candles.
Completed-close signals execute only at the following Open, terminal reporting
uses the already frozen final-Close policy, initial research capital is 5,000,
and no leverage or optimization is allowed.

The data contract is frozen before acquisition: public Coinbase Exchange REST,
`2019-01-01T00:00:00Z` inclusive through `2026-08-01T00:00:00Z` exclusive,
21,600-second candles and exactly 11,076 continuous rows per asset. A separate
read-only builder performs finite retry/chunk handling, strict grid/OHLCV
validation, canonical CSV serialization and SHA-256 evidence for every asset
plus the canonical manifest. The candidate lock independently verifies those
bytes and binds the manifest digest into `data_version`; it cannot evaluate the
strategy or place any order.

Baseline research costs are frozen at 0.60% commission, 0.05% slippage and
0.10% full spread. The adverse profile retains the commission and raises
slippage to 0.15% and full spread to 0.30%. Evaluation remains blocked until
the two data files, canonical manifest and checksum sidecar exist and pass all
lock checks.

Injected, network-free TDD passes 160/160 focused candidate/data/research-stack
tests and the complete 714/714 suite locally. No historical dataset was
downloaded, no performance result was calculated or viewed, and no parameter
was selected from outcomes. Next: reproduce focused/full suites on Windows,
commit/push and perform non-activating cloud integration. Only then acquire the
frozen data and record its SHA-256 lock as a separate evidence step.

### First Strategy Candidate Pre-registration v1 — CLOUD INTEGRATION PASS

Windows/Python 3.14.6 applied the frozen candidate patch on exact closure base
`5168dd8`. The first focused run exposed two Windows-only test-helper failures:
the helper rewrote `manifest.sha256` through text mode and therefore produced
`CRLF`, while the canonical lock correctly requires exact ASCII bytes with
`LF`. Production acquisition already used byte writes and was unaffected. The
helper was corrected to use `write_bytes`; focused validation then passed
160/160 and the complete suite passed 714/714.

The reviewed nine-file scope passed staged whitespace validation, was committed
as `27dacb3` (`Add First Strategy Candidate Preregistration v1`), pushed to
`origin/main` and left the Windows repository clean. No historical dataset was
downloaded, no strategy result was calculated or inspected, and no runtime was
started.

CPX22 was first confirmed parked and clean on `5168dd8`: PAPER and monitoring
were inactive, all unit results were `success` and restart counts were zero.
The repository fast-forwarded non-activating to exact `27dacb3`; Ubuntu/Python
3.12 reproduced 160/160 focused and 714/714 complete tests. The standard
installer explicitly started and enabled nothing, and all seven Cloud Runtime
Readiness checks passed using the installed 4,320-bar PAPER configuration,
persistent storage and explicit real-execution lock.

Final cloud state remains clean on `27dacb3`: PAPER is
`inactive/dead/disabled`, monitor service is `inactive/dead/static`, monitor
timer is `inactive/dead/enabled`, all results are `success` and retained restart
counts are zero. First Strategy Candidate Pre-registration v1 is closed as a
cross-platform PASS. The next authorized action is acquisition and independent
SHA-256 locking of the exact frozen dataset. Evaluation, optimization, forward
PAPER and live-money execution remain unauthorized.

### First Candidate Evaluation v1 — REJECTED AND CLOSED

The exact Coinbase BTC/ETH native six-hour dataset was acquired and locked
under manifest SHA-256
`6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`.
The one-shot runner then evaluated the immutable EMA 20/50 candidate under its
frozen baseline and cost-stress profiles. An initial post-evaluation
serialization failure produced no persisted or printed result; timestamp
normalization was documented, regression-tested and committed before one
deterministic recovery execution.

The recovered canonical report was recorded in commit `8978c72` with SHA-256
`6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c`.
Both baseline and stress aggregates are `REJECTED`, with two of two assets
rejected in each pass. Identity, scope, 11 walk-forward windows per asset and
75/74 unseen walk-forward trades passed. Statistical falsification and the 60%
walk-forward persistence threshold failed for both assets under both profiles;
worst-profile OOS drawdown reached 44.36% for BTC and 57.22% for ETH, exceeding
the frozen 20% ceiling.

Candidate v1 is permanently closed. Bounded forward PAPER eligibility,
bounded forward PAPER authorization, optimization and live execution remain
false. The next authorized milestone is a research-only Timeframe Sensitivity
Study v1 across 1h, 6h and 1d BTC/ETH evidence. It must not mutate or rescue v1;
any formal candidate v2 requires a new frozen identity and a separately locked
unseen final-validation boundary.

### Timeframe Sensitivity Study v1 — WINDOWS INTEGRATION AND 1H ACQUISITION INCIDENT

The next research tool now has an explicit exploratory boundary. It keeps the
existing long-only EMA 20/50 logic, BTC/ETH scope, historical date range,
baseline/stress costs, causal next-Open execution, 70/30 OOS split, seed and
falsification settings while comparing native `1h`, `6h` and `1d` evidence.
Calendar-equivalent windows use 720 training days and non-overlapping 180-day
test/step durations at every timeframe.

Candidate v1 remains closed: the six-hour path accepts and reuses only report
SHA-256
`6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c`.
It is never reacquired or reevaluated. The daily contract requires 2,769
continuous rows per asset. The revised one-hour schema-v2 contract requires
complete accounting for 66,456 expected buckets while storing only actual
provider-observed candles and every explicit missing UTC timestamp.

The one-shot study hashes each complete in-memory evaluation, then writes
bounded compact evidence through fail-closed staging without duplicating large
equity/trade arrays. It reports fixed-order comparable metrics without a score,
ranking, winner or promotion decision. Candidate-v1 reopening, automatic
selection, formal candidate evaluation, v2 authorization, optimization,
bounded forward PAPER and live execution are all explicitly false.

Windows/Python 3.14.6 reproduced the complete 740/740 suite, reviewed and
committed the implementation as `c39fd7c`, pushed it to `origin/main` and left
the repository clean before acquisition. The native daily dataset then locked
2,769 rows per asset under manifest SHA-256
`77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691`.

The first one-hour acquisition failed closed on 19 missing BTC buckets. Windows
then reproduced 23/23 focused and 746/746 complete tests, committed exact
recovery revision `0b3e5bd` and pushed it before attempt 2. That attempt made
two exact requests for every gap; all 19 persisted. An independent diagnostic
found no in-range native 1h candle, no native 5m sub-candle and no Advanced
Trade 1h candle for the first gap. No dataset or evaluation evidence was
written in either attempt.

The local schema-v2 amendment permits at most 50 explicit missing buckets and
24 consecutive gaps per asset after exact recovery. It writes no synthetic,
interpolated, forward-filled or resampled row, fetches both assets before atomic
persistence and locks every missing timestamp. Calendar-aware validation keeps
the 70/30 boundary plus exact 720-day train and 180-day test windows independent
of observed row counts; next-Open is always the next real candle. Local evidence
passes 216/216 focused research-stack tests and the complete 760/760 suite.
Windows reproduction, reviewed commit/push and a clean tree remain mandatory
before attempt 3. All candidate-v2, optimization, PAPER and live authorizations
remain false.

### Timeframe Sensitivity Study v1 — DATASETS LOCKED AND SERIALIZATION RECOVERY

Windows reproduced schema v2 after a Pandas datetime-unit compatibility repair:
30/30 focused and 761/761 complete tests passed. The reviewed implementation was
committed and pushed as `b61853f`. Acquisition attempt 3 then atomically locked
66,437 observed BTC one-hour rows with 19 explicit gaps and 66,438 ETH rows with
18 explicit gaps; each asset's longest gap is five hours. The one-hour manifest
SHA-256 is
`b9ba8126ca0612402919dd7f0f0096db2b2ef2f0a7d0669b6848276e88bc8157`.
Both dataset manifests and sidecars were independently rehashed, committed and
pushed as clean revision `e07b93e` before evaluation.

Study attempt 1 revalidated the frozen inputs and ran the exploratory profiles
in memory, but failed closed before final or staging persistence when one daily
walk-forward performance record contained the engine's defined
`profit_factor=inf` state. JSON cannot represent infinity as a standard number.
No aggregate classification or comparison was printed or persisted, and the
error may not be used for tuning.

Local schema-v3 recovery encodes only positive infinite `profit_factor` as
`POSITIVE_INFINITY_NO_LOSING_TRADES`, with an occurrence count in each compact
evaluation. All other non-finite evidence remains fatal. Strategy, parameters,
datasets, costs, calendar windows, seed and no-ranking policy are unchanged.
Focused/full Windows reproduction plus reviewed commit/push are mandatory
before one deterministic recovery execution. Candidate-v2, optimization,
PAPER and live authorizations remain false.

### Timeframe Sensitivity Study v1 — COMPLETED, NO ROBUST EDGE

Windows reproduced schema-v3 recovery with 32/32 focused and 763/763 complete
tests, committed it as `8042816` and pushed before deterministic execution. The
canonical study report was then recorded under SHA-256
`505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab`
and committed/pushed as evidence revision `cb43a74`.

Baseline and stress aggregates are `REJECTED` for 1h, recorded-reference 6h and
1d. Every asset/profile falsification gate failed. One-hour OOS losses reached
93.06%-97.90% with zero/near-zero walk-forward persistence. Six-hour BTC was
positive only at baseline and became negative under stress while drawdown
remained above 44%. Daily ETH outperformed its declining benchmark and reached
7/11 baseline positive-excess windows, but lost 17.77%/20.99% absolutely,
dropped below persistence under stress and failed falsification.

The study is closed as `COMPLETED_NO_ROBUST_EDGE` with no ranking or selected
timeframe. All history through 2026-08-01 is inspected development evidence and
cannot serve as candidate-v2 unseen validation. The next authorized milestone
is research-only failure-mode analysis and design of one new falsifiable
hypothesis, followed by a new immutable identity and separately locked unseen
boundary. Candidate-v2, optimization, PAPER and live authorizations remain
false.

### Strategy Research Inventory and Failure-Mode Analysis v1 — INTEGRATED

The post-study boundary now inventories all nine existing standalone strategy
implementations. EMA remains the rejected/closed candidate-v1 component; ADX,
ATR breakout, Bollinger, Donchian, MACD, RSI, Stochastic and Supertrend are
explicitly unevaluated research components rather than latent candidates.

A deterministic 720-row synthetic audit checks default construction, Strategy
Engine feature integration, input preservation, repeatability, signal domain,
buy/sell activity and prefix causality. All nine pass locally, but no Backtest,
market dataset, performance metric or ranking is involved. A separate loader
accepts only closed Timeframe Study report SHA-256
`505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab`
and extracts recorded failure facts without reevaluation.

The next hypothesis must address turnover/cost survival, drawdown control,
market-regime mechanism and genuinely unseen validation. This inventory does
not select a strategy family, authorize combinations or permit parameter
sweeps. Windows reproduced 180/180 focused strategy/inventory tests and the
complete 773/773 suite, committed/pushed exact revision `53202c0`, then ran the
non-evaluating audit against the exact recorded report. All nine integrations
passed; EMA alone remains market-rejected and the other eight remain unknown.

### Strategy Family Screening Protocol v1 — INTEGRATED AND DATA-LOCKED

The next bounded artifact pre-registers one descriptive screen for the eight
unevaluated default implementations on the existing native BTC/ETH six-hour
development dataset. Six hours is fixed for balanced evidence density, not as a
winner. The canonical manifest SHA-256 is
`6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`;
all history through 2026-08-01 remains inspected development evidence.

Each strategy receives one parameter fingerprint and the unchanged candidate-v1
windows, seed, causal timing, baseline/stress costs, evidence-volume gates and
drawdown limit. Multiple-comparison interpretation is descriptive and permits
only `SCREEN_OUT`, `MECHANISM_RETAINS_INTEREST` or `INCONCLUSIVE`, with no
ranking, tie-break, winner or formal validation claim.

The declaration/data-lock patch contains no screening runner and reports
`screening_executed=false`. Windows reproduced 15/15 new and 788/788 complete
tests, committed/pushed exact revision `c7fc411`, then printed the declaration
and revalidated the canonical manifest plus 11,076 rows for each asset. No
performance evaluation or file write occurred.

### Strategy Family Screening Runner v1 — LOCAL PREPARATION

The separate one-shot runner now evaluates the frozen eight-strategy order only
under baseline then stress costs, for 16 exact multi-asset calls. It validates
manifest/configuration/scope/engine/declaration identity, produces only the
three pre-registered descriptive outcomes and generates no score, ranking,
tie-break or automatic selection.

A reusable evidence compactor hashes each complete evaluation while persisting
bounded OOS, benchmark, drawdown, walk-forward, unseen-trade and falsification
evidence. It retains the proven positive-infinite profit-factor encoding and
rejects every other non-finite value before staging. Timeframe Study now uses
the same helper with unchanged schema/test behavior.

All evidence completes and serializes before atomic staging/final rename.
Existing final or staging evidence prevents repetition. Local TDD adds 19 new
runner tests, passes 37/37 runner/timeframe regression tests and the complete
807/807 suite. Windows reproduction and reviewed commit/push remain mandatory
before one explicit screening execution. Candidate v2, optimization, PAPER and
live authorization remain false.

### Strategy Family Screening v1 — CLOSED AS STANDALONE-DEFAULT BASELINE

Windows reproduced 37/37 focused runner/timeframe tests and the complete
807/807 suite, committed/pushed runner revision `e8afe12`, then passed the clean
one-shot preflight. The exact eight-strategy development screen completed and
recorded canonical report SHA-256
`9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f`;
evidence revision `2973636` is pushed and matches `origin/main`.

All eight exact standalone default configurations are `SCREEN_OUT`: baseline
and stress multi-asset classifications are `REJECTED`, all 32 asset/profile
views have negative absolute OOS return, every statistical falsification gate
is false and every strategy exceeds the frozen 20% OOS-drawdown limit. No
mechanism retained interest and no ranking, selection, candidate-v2, PAPER or
live authorization was generated.

This result closes only the frozen standalone variants as production-ready
strategies. It does not reject ADX, ATR, Bollinger, Donchian, MACD, RSI,
Stochastic or Supertrend as indicators, regime features or components of a
new combined/adaptive system. `SCREEN_OUT` must therefore be read as
`SCREEN_OUT_AS_STANDALONE_FROZEN_CONFIGURATION`, not as proof that a strategy
family has no possible edge or that systematic trading is impossible.

The current mission now moves to controlled alpha discovery. First attribute
gross signal, cost/turnover, exposure, holding-period and market-regime failure
on inspected development data. Then pre-register a bounded combination and
calibration procedure whose complete train/validation/recalibration behavior
matches intended live use. Any resulting candidate v2 requires a new immutable
identity and genuinely unseen final validation; the existing history may form
a hypothesis but may not become confirmatory evidence.

### Failure Attribution and Volume Research Protocol v1 — LOCAL PREPARATION

The next research boundary now includes volume as a mandatory causal feature,
not as an assumed standalone edge. A frozen 20-bar prior-median baseline
produces per-asset relative volume, relative dollar volume, OBV and explicit
LOW/NORMAL/HIGH participation regimes. Raw BTC and ETH volume is never compared,
warm-up evidence remains unknown and trade context is taken from the completed
signal bar rather than the following execution bar.

The protocol binds only the exact closed six-hour manifest and exact canonical
screening report. A future separate runner may replay each default strategy
under zero, baseline and stress costs solely to attribute gross signal,
cost/turnover, exposure, holding, drawdown, market regime, volume regime and
window persistence. Zero cost is explanatory, not deployable.

The current patch contains declaration, evidence locking and the reusable
volume layer only. It performs no performance replay, combination, ranking,
parameter sweep or strategy selection. Windows reproduction, reviewed
commit/push and a clean evidence lock are required after local 36/36 focused
and 843/843 complete tests before a separately reviewed attribution runner may
exist. Candidate v2, optimization, PAPER and live authorization remain false.

### Failure Attribution Runner v1 — LOCAL PREPARATION

The separate runner now implements the exact eight-strategy by three-profile
diagnostic matrix, producing 24 multi-asset replays and 48 asset/profile views.
It derives raw-signal, cost/turnover, exposure/holding, drawdown concentration,
walk-forward, market-regime and mandatory volume/OBV evidence before compacting
and hashing each complete evaluation.

Cost arithmetic and signal-bar provenance fail closed. Final/staging evidence
prevents repetition, and every evaluation must finish before atomic staging.
The canonical report has no rank, winner, automatic selection or new hypothesis.
Local 59/59 focused and 866/866 complete tests pass. Windows reproduction,
reviewed commit/push and an absent-evidence preflight remain required before
the single explicit run. Candidate v2, optimization, PAPER and live
authorization remain false; cloud services remain parked.

### Strategy Failure Attribution v1 — EXECUTED AND CLOSED

Windows reproduced 59/59 focused and 866/866 complete tests, committed/pushed
runner revision `334ceba`, then passed clean preflight against the exact frozen
manifest and screening evidence. The 24-replay matrix completed exactly once
and recorded canonical report SHA-256
`e4193bff907a2121701e7ddc1d740894641c7bf427c9501fd4ecd4392a1f81f4`;
evidence revision `f189689` is pushed and matches `origin/main`.

Nine of sixteen strategy/asset views have positive zero-cost OOS return, but
all baseline/stress views remain negative. Baseline cumulative modeled cost is
1,488.68 to 5,274.93 on 5,000 initial capital, with 42.53x to 150.71x
round-trip turnover. Every view still exceeds the 20% drawdown limit and fails
walk-forward persistence plus statistical falsification. The closed diagnosis
is therefore contextual raw signal combined with excessive unfiltered
turnover/cost, drawdown and temporal instability, not universal absence of
indicator information.

The strongest coherent development lead is ADX conditioned on `HIGH`
per-asset relative volume: 25 BTC trades retain 1,850.49 baseline P/L and 21
ETH trades retain 763.89. ADX in `BULLISH_NORMAL` market regime also retains
positive baseline P/L for both assets. Rising OBV is positive after costs only
for ETH and is not a cross-asset standalone gate. Regime, relative volume and
OBV are marginal summaries; their joint conjunction has not yet been tested.

The current mission moves to Alpha Development Protocol v2. It must pre-freeze
a small hypothesis-led joint-condition scope with causal direction/regime,
mandatory volume, risk sizing, exits, turnover/cost budget, bounded temporal
calibration and reviewed venue/execution scenarios. Existing BTC/ETH history
is inspected development evidence only. No strategy is selected, and candidate
v2, optimization, PAPER and live authorization remain false. Cloud services
remain parked.

### Alpha Development Protocol v2 — INTEGRATED; PROTECTIVE EXIT LOCAL PREPARATION

The next hypothesis is now limited to three ordered, non-ranked ADX ablations:
high relative volume; high relative volume plus `BULLISH_NORMAL`; and that same
joint condition plus rising OBV. All features use completed bars, entries occur
at the following open, volume is mandatory, and OBV remains an optional
interaction rather than an assumed cross-asset gate.

The patch freezes 0.50% risk per position, 50% maximum position size, two-ATR
risk distance, 3:1 reward/risk, four-bar cooldown and explicit annual
turnover/cost budgets. Coinbase baseline/stress and a dated Kraken taker
sensitivity are declared; maker economics remain blocked pending a causal
fill/non-fill model and actual account tier verification.

Windows reproduced 24/24 focused and 890/890 complete tests, committed/pushed
revision `45a3e00`, and locked the exact manifest plus Failure Attribution
evidence without running joint performance. The declaration and lock both
retain Candidate v2, optimization, PAPER and live authorization as false.

Protective Exit Engine v1 now executes signal-bar ATR-based stops and 3R targets
through the normal costed sell path. Stop gaps fill at the first available Open,
target gaps receive no favorable Open improvement, ambiguous stop/target bars
choose stop first and entry bars are protected. The optional policy propagates
through OOS, walk-forward, validation-pipeline and multi-asset research while
legacy defaults remain unchanged.

Windows reproduction and reviewed integration of this engine cleared the
prerequisite for constructing a separate Alpha v2 development runner. No joint
performance, calibration or candidate selection has run. Candidate v2,
optimization, PAPER and live authorization remain false; cloud services remain
parked.

### Alpha Development Runner v2 — LOCAL PREPARATION

The separate runner now binds the three fixed joint variants to the exact Risk
Engine, active Protective Exit Policy and three reviewed taker scenarios. It
will execute exactly nine multi-asset evaluations after Windows integration;
the Kraken profile is sensitivity only and the maker scenario is structurally
blocked.

The report derives annualized executed-notional turnover, modeled-cost burden,
drawdown and protective/signal exit counts from raw OOS trades before bounded
compaction. Coinbase baseline and stress control all outcome gates. The fixed
ablation order is not a leaderboard and no parameter calibration, winner or
automatic selection can be emitted.

This local preparation has not executed development performance. The next
boundary follows local 203/203 focused and 944/944 complete PASS: Windows
reproduction, commit/push, exact evidence preflight and only then one explicit
run. Candidate v2, optimization, PAPER and live authorization remain false;
cloud services remain parked.

### Alpha Development v2 — CLOSED SCREEN_OUT

Windows reproduced the reviewed runner with 203/203 focused and 944/944 full
tests, committed/pushed implementation revision `5a9018b`, passed the exact
absent-evidence preflight and executed the frozen nine-evaluation matrix once.
Canonical report SHA-256
`19627f7002fc3159729ea61d22ead0fa25deca455612764121ea96fd3eaf71a0`
was verified and recorded under evidence revision `b2a5e60`.

All three frozen variants are `SCREEN_OUT`. Baseline and stress multi-asset
validation fail, every baseline asset return remains negative, walk-forward
positive-excess persistence is 36.36% and statistical falsification fails.
No mechanism retains development interest and Kraken taker sensitivity cannot
rescue the signal.

The study nevertheless resolves the former controlling risk/cost failure.
Every variant passes evidence-volume, drawdown, annual-turnover,
annual-baseline-cost and protective-policy gates. Baseline annual turnover is
2.59x to 5.59x and annual modeled cost is 1.81% to 3.91%; baseline drawdown is
5.19% to 13.60%. Regime filtering materially reduces trades, cost, drawdown and
loss magnitude, while rising OBV adds only a small ETH improvement.

Alpha Development v2 is immutable and may not be tuned or rerun. Candidate v2,
optimization, PAPER and live authorization remain false; cloud services remain
parked. The next mission is a separately pre-registered bounded Alpha Discovery
and Calibration Protocol covering exit attribution, residual zero-cost signal,
small train-only calibration and regime-specific strategy roles before any
genuinely unseen final validation.

### Alpha Discovery and Calibration Protocol v1 — INTEGRATED

The next research boundary is now pre-declared without executing diagnostics,
calibration or performance. It locks the exact closed Alpha v2 report, its three
`SCREEN_OUT` outcomes and the inspected six-hour BTC/ETH dataset.

Phase one requires zero-cost replay of the exact v2 variants plus causal
trade-path MFE, MAE, realized-R, holding-time and exit-reason attribution. That
diagnostic may explain residual gross signal but cannot select parameters.

Phase two freezes an eight-member catalog: two ADX hysteresis bands, two ATR
risk distances and static-versus-completed-bar +1R break-even management. Every
member retains mandatory high relative volume, `BULLISH_NORMAL`, causal EMA
trend structure, the 3R target and the existing hard risk boundary.

Selection is nested and chronological. Only four prior inner-validation windows
may choose one shared BTC/ETH configuration for each outer test. Hard
baseline/stress, persistence, trades, drawdown, turnover, cost and protective
gates apply; when nothing qualifies the required action is hold cash. Outer
test evidence is structurally unavailable to selection and no global hindsight
leaderboard exists.

Local TDD covers the immutable catalog, exact fingerprint, seven-window planner,
inner-only selection, hold-cash behavior and strict canonical evidence lock.
Windows reproduced 41/41 protocol, 127/127 focused alpha/risk and 985/985 full
tests, then committed and pushed revision `4132cf8`. Declaration and evidence
lock remain non-evaluating; Candidate v2, optimization, PAPER and live
authorization remain false and cloud services remain parked.

### Alpha Discovery prerequisites — LOCAL PREPARATION

The three non-runner prerequisites are now implemented. Completed Close values
produce prefix-causal EMA trend structure. Optional +1R management observes a
surviving completed-bar High and activates the entry-price stop only from the
following Open; it cannot retroactively exit the trigger bar or activate on the
terminal bar. Static Alpha v2 behavior remains the default.

Protected trades now expose bounded post-entry path evidence: MFE/MAE in initial
R, net and gross realized R, holding bars, bars to MFE, initial risk and the
observation policy. Surviving bars may contribute full extrema; stop-first and
other exit bars contribute only their conservative executable path.

Focused prerequisite/protocol/protective/backtest tests pass 125/125 and the
complete repository passes 999/999 locally. No diagnostic replay, calibration,
parameter selection or runner has executed. The next boundary is Windows
reproduction and integration of these components before constructing the
separate nested one-shot runner.

### Alpha Discovery prerequisites — WINDOWS INTEGRATED

Windows reproduced 126/126 focused prerequisite tests and 1000/1000 complete
tests, then committed and pushed revision `c705e95`. The exact declaration and
evidence-lock boundary remain non-evaluating. No zero-cost replay, calibration,
selection or outer test exists yet.

### Alpha Discovery Runner v1 — LOCAL PREPARATION

The complete eight-member catalog is now executable with causal ADX, ATR,
market-regime, mandatory high-relative-volume and EMA trend structure. Each
evaluation retains historical feature warm-up but resets trading state at the
exact window boundary.

The one-shot runner implements the seven outer windows, complete-catalog
baseline/stress evaluation on only prior inner windows, deterministic
selection and mandatory `HOLD_CASH` when no member passes. Every window result
is bound to exact asset, parameter, profile and positions plus a canonical raw
partition hash.

The zero-cost diagnostic cannot select parameters, raw trade paths are not
persisted and there is no global outer hindsight ranking. Atomic final/staging
evidence cannot overwrite or repeat a completed study. Local focused and full
regression must pass before a Windows patch is delivered. No market evaluation
has run; Candidate v2, optimization, PAPER and live authorization remain false
and cloud services remain parked.

### Alpha Discovery and Calibration v1 — CLOSED SCREEN_OUT

Windows reproduced 55/55 focused and 1014/1014 complete tests, committed and
pushed runner revision `d9f74f0`, passed a clean absent-evidence preflight and
executed the one-shot adaptive procedure. Canonical report SHA-256
`2fc8f4d1a5d690c072408bc2d299516904feb58b2e2f40345983641bf26ed678`
was verified and recorded under evidence revision `58fb939`.

All seven outer decisions are `HOLD_CASH`; zero catalog members were selected.
Across 56 parameter/boundary decisions, protective execution, minimum trades,
drawdown, turnover and cost budgets pass universally. Stress median return and
baseline/stress persistence fail universally; baseline two-asset median return
passes only five times. BTC stress median is negative at every boundary.

The zero-cost diagnostic retains only weak, statistically unsupported gross
tendencies. Wider 2 ATR risk and stricter ADX reduce operational burden, while
+1R break-even behavior is mixed; none is a candidate or winner. The exact
impulse-entry catalog is closed and immutable.

The next mission is a new pre-registered trend-pullback and volume
re-expansion mechanism with a small causal ablation set. Candidate v2,
optimization, PAPER and live execution remain false; cloud services remain
parked.

### Trend Pullback and Volume Re-expansion Protocol v1 — LOCAL PREPARATION

The structurally new hypothesis is now pre-registered without a strategy or
performance runner. It replaces developed-impulse entry timing with a causal
sequence: bullish EMA structure, prior ADX strength, a pullback toward EMA 50
on contracting/normal relative volume, then completed-bar price recovery and
volume re-expansion followed by next-Open execution.

The catalog has exactly four members and varies only 0.5-versus-1.0 ATR
pullback distance and 1.2-versus-1.5 recovery relative volume. It preserves
ADX 25/20/15 hysteresis, lagged 20-bar volume, static 2 ATR risk, 3R target,
0.50% equity risk, no leverage and the existing nested chronological gates.
Its canonical fingerprint is
`952046ddb7a9f9a85a8976f3ccafe43a017a745c887e592a44c39c2146ba8e00`.

The evidence loader revalidates the exact canonical Alpha Discovery report,
its `SCREEN_OUT`, seven `HOLD_CASH` decisions and all 56 inner gate records.
It accepts the recorded report SHA-256
`2fc8f4d1a5d690c072408bc2d299516904feb58b2e2f40345983641bf26ed678`.

The setup state machine, executable strategy and nested runner remain separate
review prerequisites. No performance, calibration or selection has run;
Candidate v2, optimization, PAPER, cloud and live authorization remain false.

### Trend Pullback Volume Strategy v1 — LOCAL PREPARATION

The causal state machine and complete four-member executable strategy are now
implemented without market evaluation. Prior ADX strength uses the preceding
eight completed bars. A low/normal-volume EMA-50 pullback arms the setup; only
a later price recovery with ADX/directional confirmation and frozen relative-
volume expansion may trigger a following-Open entry.

Setup state cannot cross an evaluation boundary, form during an open signal
position or survive cooldown. It expires after eight subsequent bars and is
invalidated by lost EMA trend structure. Completed-bar signal exits preserve
EMA-50, ADX-15 and directional failure semantics; active static 2 ATR / 3R
protection remains delegated to the reviewed Protective Exit Engine.

Market-regime and OBV gates are intentionally absent rather than silently
inherited from the closed impulse family. The nested runner remains the only
unimplemented prerequisite. No performance, selection or evidence has been
created; all deployment authorizations remain false.

### Trend Pullback Volume Strategy v1 — WINDOWS INTEGRATED

Windows reproduced 28/28 focused strategy tests and 1062/1062 complete tests,
then committed and pushed revision `feaf08b`. The declaration confirms that
the causal state machine and exact four-member strategy are implemented and
reviewed while performance, selection, Candidate v2, PAPER and live execution
remain false.

### Trend Pullback Volume Runner v1 — LOCAL PREPARATION

The separately reviewed one-shot runner now binds the exact dataset manifest,
closed Alpha Discovery evidence and immutable four-member catalog in the same
process before evaluation. Ten unique inner validation windows produce 80
complete catalog/profile evaluations. Selection sees only prior inner BTC/ETH
evidence; ineligible boundaries hold cash without executing an outer strategy.

Only an inner-selected member may be evaluated in each of seven outer windows.
Every compact result is bound to exact identity, profile, phase and positions
plus a canonical raw-partition hash. Final canonical JSON and SHA-256 evidence
are promoted atomically from staging and cannot be overwritten or repeated.

No development performance has run. Windows reproduction, commit/push and an
absent-evidence preflight remain mandatory before an explicit one-shot run.
Candidate v2, optimization, PAPER, cloud and live authorization remain false.

### Trend Pullback Volume Development v1 — CLOSED SCREEN_OUT

Windows reproduced 59/59 focused and 1073/1073 complete tests, committed and
pushed runner revision `f8f9c42`, passed the exact clean absent-evidence
preflight and executed the frozen one-shot procedure. Canonical report SHA-256
`7598ea3616a60753d5be5b4d7af8c146f1bea881cb2d43ed71ea16cebdd685e3`
was verified and recorded under evidence revision `8b1560c`.

Zero configurations were selected and all seven outer decisions are
`HOLD_CASH`; therefore no selected strategy was evaluated in an outer window.
Across 28 parameter/boundary decisions, active protection, drawdown, turnover
and baseline-cost gates pass universally. Minimum trades, positive two-asset
baseline median return and baseline/stress persistence fail universally;
nonnegative two-asset stressed median return passes only two decisions.

Four recent inner windows contain only 1–11 completed trades per asset versus
the frozen minimum of 12. Positive-window rates never exceed 50% versus the
60% gate. Deeper 1 ATR pullbacks create more trades but generally worse
returns; shallow 0.5 ATR pullbacks lose less, and late ETH evidence turns
positive while BTC remains flat or negative. Maximum observed window drawdown
remains approximately 2.04%, so signal scarcity and persistence—not cost,
turnover or uncontrolled risk—are the controlling failures.

The exact four-member catalog is closed without rejecting the broader
trend-pullback family. The next boundary is a bounded trade-path attribution
of these exact signals and exits, including MFE, MAE, realized R, exit reason,
holding time and BTC/ETH asymmetry. No gate will be lowered and no Candidate
v2, optimization, PAPER, cloud or live authorization exists.

### Selective Swing Trading Research Mandate v1 — LOCAL PREPARATION

The active next mission is now a documentation-only research reset. Listed
equities become the primary long-term market, beginning with a faithful point-
in-time CAN SLIM replication path. Crypto remains an active secondary sleeve,
beginning with a separate BTC/ETH/XRP one-day capitulation-volume reversal
hypothesis reconstructed through blinded sequential chart replay.

The operating style is selective swing trading: continuous observation, cash
by default, completed daily decisions and no trading-frequency target. The two
sleeves share validated infrastructure but must retain separate hypotheses,
data contracts, protocols, evidence and closures.

The exact Trend Pullback Volume v1 catalog and every prior rejection remain
closed historical evidence. Its planned six-hour trade-path attribution is
deferred rather than erased, but it is no longer the active research boundary.

This milestone adds no market data, strategy, runner, parameter selection or
performance evidence. The next implementation boundary after Windows
integration is the BTC/ETH/XRP daily data and blinded-replay protocol; the
equity point-in-time data audit follows before any CAN SLIM implementation.
Candidate v2, optimization, PAPER, cloud and live authorization remain false.

### BTC/ETH/XRP Daily Data and Blinded Replay Protocol v1 — LOCAL PREPARATION

The first implementation milestone under the Selective Swing Trading mandate
now binds its normalized hash to the exact recorded BTC/ETH one-day manifest
and introduces a provider-neutral replay boundary. The replay shows only a
rolling 30-bar completed-daily prefix, requires a reasoned `ENTER`, `SKIP`,
`HOLD` or `EXIT` decision before advancing, and binds every decision to the
visible-frame SHA-256.

Missing candles are never synthesized. Provider-unavailable intervals split
replay segments, and raw volume remains venue-specific with only causal per-
asset relative normalization permitted. XRP is deliberately not assigned to a
provider until historical listing, availability, candle/volume semantics,
liquidity and cost evidence are audited.

This package contains protocol and synthetic component regression only. It
acquires no data, executes no real chart replay or performance, defines no
strategy and authorizes no Candidate v2, optimization, PAPER, cloud or live
operation. After Windows reproduction and integration, the next boundary is
the BTC/ETH/XRP provider and historical-availability audit.

### Selective Swing Portfolio Construction Protocol v1 — LOCAL PREPARATION

The user's shared crypto/equity capital philosophy is now formalized before
market results can influence it. Only independently eligible signals enter the
raw `1/n` capital envelope; stop-based risk, position, portfolio, cash, sector
and correlation limits may always reduce actual exposure. Cash is the required
outcome when no signal is eligible or risk capacity is unavailable.

Listed-equity research begins with no more than three simultaneous positions.
Five remains a future research ceiling. Exiting a loser does not automatically
move capital to prior winners. A survivor requires a fresh causal add-on signal
before winner-only, smaller-tranche pyramiding may later be considered;
averaging down remains prohibited.

The rare 20–30% or larger explosive move from a sideways stock base is retained
as `Exceptional Sideways Breakout Contingency v1`, not general day trading. It
is unimplemented and requires a separate point-in-time intraday data, halt,
liquidity, spread/slippage, confirmation, no-chase, stop, smaller-risk and same-
session-exit protocol before performance research.

Professional review now strengthens the same declaration with three isolated
evidence books, a shared future risk-engine boundary, a first-class
`NO_TRADE_HOLD_CASH` outcome, provisional rather than authorized risk ranges,
`3R` as an entry screen rather than a forced take-profit, executable gap/fill
requirements and offline-only versioned AI learning. The daily crypto setup is
recorded as decline, relative-volume event, stabilization, confirmation,
structural invalidation and predefined-exit reconstruction. XRP decoupling
remains a diagnostic hypothesis, not an automatic rotation rule.

No allocation, candidate ranking, pyramiding, intraday strategy or performance
has executed. After Windows integration, active work returns to the BTC/ETH/XRP
provider and historical-availability audit. Candidate v2, optimization, PAPER,
cloud and live authorization remain false.

### BTC/ETH/XRP Provider and Historical Availability Audit v1 — LOCAL PREPARATION

Official provider evidence has now been reviewed for the exact 2019-01-01
inclusive through 2026-08-01 exclusive daily reconstruction boundary.
Coinbase's existing BTC/ETH manifest remains immutable cross-venue reference
evidence, but Coinbase is rejected as the common three-asset provider because
its XRP trading was suspended from 2021-01-19 until relisting on 2023-07-13.

Kraken Spot official OHLCVT archives are selected as the primary common source
for `BTC/USD`, `ETH/USD` and `XRP/USD`. Kraken announced XRP/USD in May 2017,
before the research start. The future acquisition must combine the official
complete archive and all required quarterly updates, then use the 720-entry
REST OHLC endpoint only for recent same-venue overlap/bridge validation while
removing its final uncommitted candle.

No missing day may be synthesized, forward-filled or inserted as zero volume.
Every gap becomes an explicit `NO_TRADE_UNAVAILABLE` boundary and splits replay
segments. Archive hashes, members, first/last observed buckets, exact gaps and
archive/REST equality remain the next byte-level acquisition gate.

The documentary provider/availability audit is complete, but no data has been
downloaded or locked and no real replay, strategy or performance has executed.
The active next mission is a fail-closed Kraken daily acquisition and immutable
three-asset manifest. Candidate v2, optimization, PAPER, cloud and live
authorization remain false.

### Kraken BTC/ETH/XRP Daily Dataset Lock Protocol v1 — LOCAL PREPARATION

The fail-closed acquisition implementation is now prepared against the exact
provider-audit hash. It accepts one official complete Kraken OHLCVT ZIP and only
reviewed quarterly updates, hashes every source byte, inventories every archive
member and selects exactly the native 1440-minute `XBTUSD`, `ETHUSD` and
`XRPUSD` members.

Archive duplicates have no silent precedence. Equal rows are recorded;
conflicts block publication. The bounded REST bridge removes its final
uncommitted candle, preserves raw-response hashes and must match at least one
completed archive bucket exactly for each asset. Missing UTC days remain
explicit `NO_TRADE_UNAVAILABLE` gaps and split continuous replay segments.

All evidence is written to staging first. Only a completely valid three-asset
manifest, archive inventory, raw REST evidence and canonical files are promoted
atomically, and an independent lock revalidates every hash. The currently
published quarterly directory was reviewed through `Q1 2026`; no nonexistent
`Q2 2026` URL or unofficial substitute is assumed.

This local preparation performs no download or REST request and locks no real
dataset. After Windows integration, the active next action is the bounded
official Kraken acquisition. Real replay, strategy, performance, Candidate v2,
optimization, PAPER, cloud and live authorization remain false.

### Kraken Daily Dataset Lock v1 — ACQUISITION FAILED CLOSED

The bounded Windows acquisition inspected the official complete archive and
performed a 482-row archive/REST overlap audit for BTC-USD, ETH-USD and
XRP-USD. All 1,446 OHLC comparisons matched exactly, confirming pair and daily
UTC-bucket alignment. Full OHLCVT equality nevertheless failed: exact rows were
156 for BTC, 119 for ETH and 94 for XRP; volume mismatches were 326, 363 and
388, while each asset had 299 trade-count mismatches.

The mismatch was systematic across the overlap rather than confined to one
source boundary. No tolerance, field removal or precedence was introduced.
REST stitching failed its frozen gate, staging was not promoted and no v1
dataset, replay, strategy or performance evidence was published.

### Kraken Daily Archive-Only Dataset Lock v2 — LOCKED AND INDEPENDENTLY REVALIDATED

The exact frozen complete archive and Q1 2026 update produced archive-only
dataset
`kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`.
The atomic Windows build published manifest SHA-256
`8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`
without a network request or REST artifact. Full member inventory completed for
both source ZIPs and its independently reproduced SHA-256 is
`cbfc0963b5966a5f94f97ff90a1bd52761167e9846515aad2abe7a85f27882b2`.

BTC contains 2,646 observed rows and preserves the unavailable
`2024-03-31T00:00:00Z` bucket. ETH contains all 2,647 expected rows. XRP
contains 2,645 observed rows and preserves unavailable buckets on
`2022-05-11T00:00:00Z` and `2022-05-12T00:00:00Z`. Each canonical file hash
matched its manifest, and `KrakenDailyDatasetLock` independently returned
`INDEPENDENT_RELOCK_PASS` for the same manifest and row counts.

Only compact evidence is retained in Git; source ZIPs and the published
dataset remain external. The next boundary is separate real blinded-replay
review. Strategy, performance, optimization, Candidate v2, PAPER, cloud and
live authorization remain false.

### Kraken BTC/ETH/XRP Bounded Blinded Replay Review v1 — SEALED PREFLIGHT PASS

The causal replay primitive was re-audited against the locked Kraken dataset
boundary. Its public view already exposes only the trailing completed 30-bar
copy, requires one reasoned state-valid decision before advancing and emits no
performance. Real replay nevertheless remained blocked because the older
declaration was Coinbase-bound, decisions existed only in memory, open
positions had no explicit episode-end policy and no bounded price-independent
episode selection was frozen.

The prepared review binds manifest SHA-256
`8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`
and all three Kraken availability structures. It selects one 89-row episode per
asset solely from protocol/manifest/asset hashes and continuous segment
positions. Each episode supplies 30 context bars and 60 decisions; CLI review
and preflight output retain only a sealed schedule hash and never reveal chosen
timestamps or future endpoints.

Every decision must now be written as canonical exclusive evidence with a
prior-decision hash before `advance()` unlocks. Episode completion atomically
promotes a final manifest and sidecar, while a separate evidence lock
revalidates every file and the complete chain. Every episode starts flat; a
terminal long state remains `OPEN_POSITION_UNRESOLVED_AT_EPISODE_END` without a
synthetic exit, position carry or performance result.

Windows reproduced 82/82 focused and 1,201/1,201 complete tests before commit
`8ed84c9` was pushed. One external-dataset preflight then independently
re-locked the exact manifest and returned
`KRAKEN_BLINDED_REPLAY_PREFLIGHT_PASS` without a network request. It reproduced
BTC segment rows `1916, 730` with 2,470 candidates, ETH segment rows `2647`
with 2,559 candidates and XRP segment rows `1226, 1419` with 2,469 candidates.
The one-per-asset selection is bound by sealed schedule SHA-256
`3e805044356777f0bdfa2901db267d714c1e14d11415dd4686acaaaed92f1042`.
No selected timestamp was exposed and the schedule was not persisted.

Compact preflight evidence is retained in
`KRAKEN_BTC_ETH_XRP_BLINDED_REPLAY_PREFLIGHT_EVIDENCE_V1.md`. The preflight
created no participant view, decision, replay, strategy or performance. The
next boundary is a separate review of whether one supervised, durably chained
three-episode reconstruction may be authorized. Real replay, Candidate v2,
optimization, PAPER, cloud and live authorization remain false.

### Kraken BTC/ETH/XRP Supervised Blinded Replay v1 — SUPERVISED REPLAY PREPARATION

The sealed preflight evidence is now an exact-hash prerequisite for a new
one-episode-at-a-time runner. Review mode opens no dataset and reports every
binding and authorization flag. Execution requires the exact external lock, a
fresh external evidence root and one explicit operator phrase that is consumed
by only the next asset episode.

The runner enforces BTC, ETH and XRP order without accepting an asset choice.
It independently re-locks completed episode evidence before another asset can
begin. Each invocation can show only one 89-row episode through an in-memory
30-bar candlestick/volume window, accepts exactly 60 state-valid reasoned
decisions and durably writes each decision before the next bar appears. The
chart is not persisted and contains no future endpoint, indicator, signal or
performance field.

An interrupted episode leaves exclusive staging evidence and blocks automatic
retry or resume. A completed episode is immediately re-locked; the third
completion atomically creates a three-episode catalog. Terminal longs remain
unresolved and never carry into the next asset. This preparation uses synthetic
tests only and does not authorize or execute a participant view. Windows
integration and nonexecuting review declaration are next. Real replay,
strategy, performance, optimization, Candidate v2, PAPER, cloud and live
authorization remain false.

### Kraken Supervised Replay v1 Closeout — PAUSED AFTER BTC

The first and only authorized supervised episode completed 60 BTC-USD
decisions from 2024-05-08 through 2024-07-06 and ended flat. Its external
aggregate evidence SHA-256 is
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`.
The evidence remains process and inspected hypothesis-reconstruction material;
no P&L, return, ranking, drawdown or parameter conclusion was produced.

The episode verified the causal and durable replay mechanics but also exposed
that unassisted human terms such as confirmation, normal pullback and strong
volume are not reproducible enough to define the strategy. Supervised v1 is
therefore paused. ETH and XRP remain unopened, and no additional v1 episode is
authorized.

### Kraken AI-Driven Crypto v2 — AI-DRIVEN V2 CAUSAL FEATURE CONTRACT

The active mission is now a deterministic AI-driven research agent, built one
reviewed layer at a time. The first layer is exact completed-bar measurement:
lagged prior-high drawdown, lagged-median relative volume, true range, lagged
ATR expansion, close location and one-bar close return. All rolling baselines
exclude the current bar and every recorded dataset gap splits the feature
history.

`src/kraken_ai_driven_v2_features.py` implements only these measurements. It
requires explicit lookback values and has no default production parameter set,
setup threshold, trading action, position state, P&L or optimization. The
existing locked Kraken dataset can be reused later without updating it; any
future quarterly extension must receive a new immutable dataset identity.

The next boundary is Windows reproduction and review of the feature contract,
followed by a separate pre-registration of the smallest deterministic
`FLAT -> ARMED -> LONG -> FLAT` state machine. Existing generic risk sizing and
conservative stop-first protective exits are reusable infrastructure only;
previously rejected Alpha/trend-pullback signals are not transferred. Strategy
performance, optimization, Candidate v2, PAPER, cloud and live authorization
remain false.

### Kraken AI-Driven v2 — STATE MACHINE IMPLEMENTED (LOCAL SYNTHETIC REVIEW)

The second V2 layer now converts the causal measurements into an explicit
signal-state path under reference set
`kraken-ai-v2-ccvr-reference-a-v1`. The prior supervised BTC episode remains
bound by SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
and is inspected context only.

`FLAT` arms only when prior-high drawdown, a negative completed-bar return,
relative volume, range expansion and low close location jointly pass their
frozen gates. `ARMED` can re-anchor on a new complete event, invalidate on a
close below its prior setup low, expire after five later bars or confirm when a
positive bar closes above the previous high with sufficient relative volume
and upper-range close location. `LONG` exits its signal state only on fixed-low
structural failure or frozen bearish-volume failure.

The component retains state before/after, canonical reason, setup/long age,
event timestamp, setup low, condition booleans and only
`ENTER_NEXT_OPEN`/`EXIT_NEXT_OPEN` intents. Those intents are not fills and no
brokerage position exists. The external Kraken dataset has not been opened and
no return, P&L, optimization or performance evaluation has run.

The immediate boundary is Windows reproduction of the state-machine tests and
hash-bound review. After integration, a new protocol must adapt next-open fill,
gap, structural stop, bounded risk, position size, minimum causal `3R` room,
protective exit and maximum-hold semantics. Candidate v2, PAPER, cloud and live
authorization remain false.

### Kraken AI-Driven v2 — RISK AND EXECUTION ADAPTER IMPLEMENTED (LOCAL SYNTHETIC REVIEW)

State milestone `1f73034` is now reproduced and pushed after 1,299 Windows
tests. The third V2 layer converts its unfilled intents into synthetic research
plans under exact policy `kraken-ai-v2-risk-execution-reference-a-v1`. The
prior supervised BTC episode remains immutable inspected context under SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`.

An entry can occur only at the following consecutive daily open and only when
the raw and cost-adjusted open remain above the fixed setup low, the upward gap
does not exceed one-half prior ATR and the already-known prior 30-bar close high
offers at least net cost-aware `3R`. Sizing risks at most `0.50%` of current
equity, respects `1.50%` total open crypto risk, three concurrent positions,
one-third notional and available cash.

Cost profile `kraken-tier1-taker-adverse-20260829-v1` uses the official Kraken
Tier-1 `0.80%` taker commission per side plus separate conservative research
assumptions of `0.15%` slippage per side and `0.30%` full spread. It asserts no
actual account tier. Stop gaps precede scheduled exits, target gaps receive no
optimistic improvement, same-bar stop/target conflicts choose the stop and a
20-completed-bar maximum hold exits only at the next open.

These are synthetic plans and fills, not orders, realized P&L or performance.
The locked Kraken dataset remains unopened. The immediate boundary is Windows
reproduction and hash-bound review, followed by a separate development and
genuinely untouched evaluation partition protocol. Optimization, Candidate
v2, PAPER, cloud and live authorization remain false.

### Kraken AI-Driven v2 — PARTITION PROTOCOL FROZEN (LOCAL SYNTHETIC REVIEW)

Risk/execution milestone `f8d2436` is now reproduced and pushed after
1,348/1,348 Windows tests. The next boundary is frozen as protocol
`kraken-btc-eth-xrp-ai-driven-v2-partition-v1` without opening the external
Kraken dataset or calculating performance.

`DEVELOPMENT` covers `2019-01-01T00:00:00Z` through
`2024-04-01T00:00:00Z` exclusive. `CALIBRATION` covers the following year and
is inspected, not unseen, because BTC supervised evidence SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
falls inside it. `EVALUATION` begins `2025-04-01T00:00:00Z` and preserves the
final 365 days as sealed one-time evidence.

The synthetic validator reconciles exact rows and provider gaps, rejects any
timestamp mismatch and splits continuous segments without carrying warmup,
signal state, positions or risk across a gap or partition. It does not locate
dataset files, read OHLCV or expose a performance field. All three real
partitions remain unopened.

The immediate boundary is Windows reproduction of the partition tests and
hash-bound nonexecuting declaration, followed by commit and push. Only then may
a separate development-only runner be designed. Calibration, evaluation,
optimization, Candidate v2, PAPER, cloud and live authorization remain false.

### Kraken AI-Driven v2 — DEVELOPMENT RUNNER IMPLEMENTED (LOCAL SYNTHETIC REVIEW)

Partition milestone `421de3f` is reproduced and pushed after 1,385/1,385
Windows tests. Protocol
`kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1` now prepares the one-
shot reference-A development boundary without opening the external dataset.

The new reader hash-checks complete canonical inputs as opaque bytes but parses
OHLCV only before `2024-04-01T00:00:00Z`. It must expose BTC `1916`, ETH
`1917` and XRP `1915` development rows while parsing zero calibration and zero
evaluation rows. This avoids the complete-value loader that would otherwise
materialize sealed observations.

One synthetic portfolio starts with USD 5,000 research notional. Existing
exits precede BTC/ETH/XRP ordered entries; cash, position count and total risk
are shared. Entry-bar protection, adverse costs, stop-first conflicts and
maximum hold remain frozen. A missing next open cancels an intent, an open
position at a gap halts the path and a terminal position remains unresolved.

Canonical external evidence is one-shot and requires exact phrase
`EXECUTE_KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_ONCE`. The implementation does
not grant that phrase or authorize execution. The immediate boundary is
Windows reproduction, hash-bound nonexecuting review, commit and push.
Development performance, calibration, evaluation, optimization, Candidate v2,
PAPER, cloud and live authorization remain false.

### Kraken AI-Driven v2 — DEVELOPMENT ATTEMPT 1 TECHNICAL INCIDENT

Windows reproduced 48/48 focused and 1,413/1,413 complete tests, then committed
and pushed development-runner milestone `5054da1`. A separate operator decision
authorized one reference-A development attempt on `2026-08-30`.

The runner validated the exact manifest and full-file hashes, parsed only the
development prefix and reached the first eligible entry. It then failed closed
with `TypeError: Signal close must be numeric.` The reader had validated CSV
numbers as `Decimal` but retained that representation in its Pandas frame;
synthetic tests had used `float`, and the frozen risk adapter accepts its
existing `numbers.Real` contract.

No canonical report, checksum or result was emitted. The exception preceded
evidence-root creation and atomic staging/final promotion. Calibration and
evaluation OHLCV remained unparsed, and no real order, sweep, ranking or
promotion occurred. Attempt 1 is not strategy evidence and its authorization
is consumed.

The active mission is limited to explicit `float64` normalization after exact
decimal validation, a real-reader-to-risk-adapter regression, renewed hash
binding, complete Windows regression, incident commit/push and explicit
absence checks for final/staging evidence. Only then may a new operator
decision consider one recovery attempt. All calibration, evaluation,
optimization, Candidate v2, PAPER, cloud and live authorization remain false.

### Kraken AI-Driven v2 — DEVELOPMENT REFERENCE A CLOSED HOLD CASH

Recovery commit `1f040e2` passed 50/50 focused and 1,415/1,415 complete Windows
tests. A new explicit operator decision authorized Attempt 2 after both Attempt
1 and Attempt 2 final/staging paths were confirmed absent. The runner completed
with no staging remainder and a clean repository.

Canonical report SHA-256
`f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`
passed its independent EvidenceLock. It parsed BTC `1916`, ETH `1917` and XRP
`1915` development rows in exact segments, while parsing zero calibration and
zero evaluation rows.

The state path produced 13 `CONFIRMATION_LONG` transitions. Risk/execution
approved none: two failed `CAUSAL_RESISTANCE_NOT_ABOVE_ENTRY` and eleven failed
`NET_THREE_R_CAUSAL_ROOM_NOT_AVAILABLE`. There were no positions, trades,
commissions or drawdown; cash remained USD 5,000 research notional. This is a
no-exposure result, not break-even performance.

Reference A is now
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`. It may not
be rerun or loosened after inspection and creates no calibration or Candidate
v2 authorization. The active decision is whether to stop or pre-register a
structurally new development-only hypothesis with an executable causal target.
Evaluation, optimization, PAPER, cloud and live remain blocked.

### Kraken AI-Driven v2 — HYBRID STRATEGY DISCOVERY PROTOCOL FROZEN (LOCAL REVIEW)

The continuation decision is now hybrid under protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`.
BTC, ETH and XRP share a four-family catalog and the same hard portfolio safety
envelope, but a future immutable hypothesis may route different strategy
families to different assets and causal regimes. No asset is forced to trade;
`HOLD_CASH` remains a valid output.

The catalog permits capitulation recovery, trend-pullback continuation, range
mean reversion and volatility breakout using two-to-five family-permitted
indicator primitives. One round is limited to six hypotheses, two variants per
family and four routes per asset. Protocol v1 is limited to two separately
authorized rounds and twelve cumulative hypotheses, with no parameter grid,
performance leaderboard or automatic winner.

The shared safety floor preserves USD 5,000 research notional, `0.50%`
position risk, `1.50%` total open risk, three positions, one-third notional,
adverse costs, completed-bar/next-open causality, entry-bar protection and
stop-first ordering. Each family must still define a new causal execution path;
Reference A remains closed and its exact signal, execution and run identities
cannot be reused.

Only a manifest validator and hash-bound nonexecuting review exist. No Round 1
hypothesis, signal component, execution adapter or runner exists; no market
data was opened. The immediate boundary is Windows focused/full regression and
review, commit/push, then a separate pre-registration of bounded Round 1.
Calibration, evaluation, Candidate v2, PAPER, cloud and live remain false.

### Kraken AI-Driven v2 — HYBRID DISCOVERY ROUND 1 PRE-REGISTERED (LOCAL REVIEW)

Parent hybrid milestone `20d6767` is the exact base for protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`. Round 1 now
contains four hypotheses: volatility-path capitulation recovery, trend-pullback
continuation, range mean reversion and volatility breakout. Each initially
registers BTC, ETH and XRP, but future interest is retained per asset-family
route, so an unsuccessful route remains `HOLD_CASH`.

All four freeze completed-bar, prior-baseline indicators and following-open
execution with a minimum net `3R` path. Family-specific regime, confirmation,
stop, exit and maximum-hold values are exact. The capitulation member uses
Reference A only as evidence lineage and cannot reuse its identities or failed
prior-resistance gate.

Baseline adverse Kraken costs and a doubled slippage/spread stress profile are
fixed. Five chronological Development slices and absolute route gates require
eight trades, time persistence, baseline/stress expectancy and profit factor,
bounded drawdown, bounded largest-trade contribution and no unresolved
position. At least two assets and two routes must pass before later portfolio
interest exists; multiple routes for one asset trigger a separate review, not
automatic selection.

Only canonical manifest/configuration locks and a hash-bound nonexecuting review
exist. Regime, signal, execution and runner components are not implemented, no
data was opened and no performance was calculated. The immediate boundary is
Windows regression/review, commit/push, then synthetic-only implementation of
the four causal components. Calibration, Evaluation, Candidate v2, PAPER,
cloud and live remain false.

### Kraken AI-Driven v2 — Round 1 Causal Signals (Local Review)

Exact parent milestone `b6ea2ab` is the base. A shared causal feature engine
now computes the frozen prior-only baselines and current completed-bar
measurements for all four Round 1 families. Prefix-causality, source
preservation, strict UTC/OHLCV geometry and gap rejection are synthetic-tested.

Four independent signal paths now emit evidence and `ENTER_NEXT_OPEN` intents
without producing an order or position. Capitulation uses its five-bar window;
trend and range confirm only on the immediate next completed bar; breakout
confirms on the same completed bar. Range freezes its signal-time Bollinger
midline anchor. No cost, fill, P&L, ranking or performance calculation exists.

The active mission is Windows focused/full regression and hash-bound review,
then commit/push of this exact signal-only milestone. After that, the next
separate task is synthetic family-specific execution adapters. Reference A is
still closed, no market dataset was opened and Calibration, Evaluation,
Candidate v2, PAPER, cloud and live remain false.
