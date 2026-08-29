# ROADMAP

# AI Alpha Engine Development Roadmap

## Purpose

This document is the project-level source of truth. Completed work, the current readiness gate, the next safe boundary and intentionally deferred work are kept explicit so implementation does not outrun evidence.

---

# COMPLETED

## Phase 1 — Data Foundation

Historical data collection, validation, storage and visualization foundation. **Status: COMPLETED.**

## Phase 2 — Research & Strategy Foundation

Feature Engine, Strategy Library, Strategy Engine, Backtesting Engine, Performance Analyzer and the validated strategy set (EMA, RSI, MACD, Bollinger Bands, Donchian, ATR, Supertrend, ADX and Stochastic). **Status: COMPLETED.**

## Phase 3 — Robustness / Validation Stack

Benchmarking, out-of-sample validation, walk-forward analysis, falsification, validation pipeline, multi-asset evidence and market-regime diagnostics. Strategy Optimizer itself is intentionally deferred; the evidence controls required before optimization are already in place. **Status: CORE VALIDATION COMPLETED.**

## Phase 4 — Risk Engine for Paper Trading

Risk Engine v1 position sizing, v2 account protection and v3 trade-risk policy: exposure cap, drawdown/daily/weekly guards, kill switch, stop/target validation and configurable minimum reward/risk. **Status: COMPLETED FOR PAPER TRADING.**

## Phase 5 — Deterministic Paper-Trading Foundation

Paper Broker v1, Paper Trading Engine v1, stateful Session v2, provider-neutral MarketDataEvent / HistoricalReplayFeed and Backtest ↔ Paper Replay Consistency Validator v1. **Status: COMPLETED.**

---

# COMPLETED READINESS GATE

## Objective

Turn replay-consistency diagnostics into explicit evidence before external real-time connectivity is introduced.

## Active milestone

**Paper Readiness Gate v1 — Representative Replay Consistency + Roadmap Reconciliation**

The gate classifies representative comparisons as `MATCH`, `INTENDED`, `DEFECT` or `CONFIGURATION_MISMATCH`. A divergence is never silently normalized: only an exact, explicitly allow-listed `INTENDED` semantic difference may pass. Defects, configuration mismatches, unexpected fields and stale allow-lists block readiness.

## Exit criteria

- representative consistency scenarios are green or explicitly classified as intended semantics
- no unresolved defect/configuration mismatch is hidden by the gate
- project documentation reflects actual implementation state
- full automated regression remains green

---

# NEXT — Real-Time Paper Trading Path

## Milestone 1 — Real-Time Market Data Adapter + Feed Health — COMPLETED

First provider contract: Alpaca crypto websocket bars, controlled `BTC/USD` 1-minute scope. Provider normalization plus stale/duplicate/out-of-order/future/missing-gap health gates emit only the existing `MarketDataEvent` contract. Authenticated network transport and reconnect/backoff stay in the runtime milestone so transport failure handling is tested at the operational boundary.

## Milestone 2 — Operational Safety / Paper Runtime — COMPLETED

Controlled runtime loop, graceful shutdown, exception isolation, heartbeat/health state, bounded feed-failure halt policy, Alpaca websocket authentication/subscription with reconnect/backoff, and minimal durable checkpoint/restart recovery are implemented and regression-validated. Basic restart recovery preserves broker/open-position, Risk Engine protection and session/feed continuity state so a restarted paper process does not wake up with trading amnesia.

## Milestone 3 — First Controlled Real-Time Paper Run — PRE-FLIGHT

Pre-Flight Gate v1 validates redacted credential presence, controlled BTC/USD 1-minute scope, explicit risk guards, paper-account state, writable checkpoint storage, hard-disabled execution, provider connectivity/subscription and runtime startability. Any failed check blocks progression.

After pre-flight passes, run the full chain on real market data with simulated money, conservative scope and explicit observability. Compare forward behavior against backtest/replay expectations before expanding assets, timeframes or autonomy.

---

# SHOULD HAVE DURING PAPER TRADING

- operational alerts and richer watchdog telemetry
- session performance reports and replay/forward comparison reports
- richer data-quality metrics and provider reconnect telemetry
- durable order/event audit storage for extended forward testing

These improve long-duration operations but do not block the first controlled real-time paper run once the minimum safe runtime exists.

---

# DEFERRED / POST-PAPER-TRADING ENHANCEMENTS

These items are intentionally deferred, **not rejected**. A deferred capability moves into active development when required for safe unattended operation, when forward evidence exposes a material model gap, or when the next architectural boundary cannot be completed safely without it.

## Risk and Portfolio

- portfolio correlation/concentration and aggregate multi-position exposure — wait for multi-position forward evidence
- portfolio allocation/weighting and volatility targeting — wait until multiple simultaneous opportunities are proven relevant
- VaR / Expected Shortfall — add only if they improve decisions beyond current drawdown/exposure controls
- conservative fractional Kelly — wait for sufficiently stable edge estimates
- Monte Carlo drawdown as a hard gate — wait until acceptable drawdown policy is empirically calibrated
- broker-specific margin/leverage/buying-power checks — wait until a broker/exchange target is selected
- emergency forced liquidation — wait for the execution state machine/live adapter; Risk Engine should not secretly become execution

## Strategy Intelligence

- regime-based automatic strategy selection — current regime evidence remains diagnostic until conditioned performance is robust
- additional strategies — add only when validation/paper evidence shows a real coverage gap
- Strategy Optimizer/adaptive parameter optimization — defer until evidence demonstrates need and overfitting controls can govern it
- AI Learning Engine / autonomous adaptation — defer until stable forward evidence and governance exist

## Execution / Market Microstructure

- limit/stop order lifecycle — market-order boundary first
- partial fills/liquidity simulation — add if paper/live evidence shows deterministic fills materially overstate execution
- latency, queue position and richer microstructure — venue/timeframe dependent; evidence must justify complexity
- live broker/exchange adapter — only after stable paper runtime and forward evidence
- advanced broker reconciliation — requires live connectivity

## Data / Runtime Scale

- bounded rolling-history/replay performance optimization — wait for measured session-duration and warm-up requirements
- broad provider/asset/timeframe expansion — first prove one provider + controlled scope
- large-scale consistency matrices — expand after the v1 readiness evidence contract is trusted on representative cases

---

# Long-Term Objective

Evolve the validated research/risk/paper foundation into a safely operated AI Alpha Trading Agent that can research, validate, manage risk, trade through replaceable execution/data boundaries and improve only when evidence justifies adaptation.

# Development Principle

Architecture Review → Design → TDD → Validation → Documentation → Git Integration. Progress is measured by evidence, deterministic behavior and safe boundaries rather than feature count.

## Provider Substitution — Coinbase Public Feed v1

- [x] Keep market-data provider replaceable; Alpaca is not a hard dependency.
- [x] Add public Coinbase `BTC-USD` market-trades transport without credentials.
- [x] Aggregate trades into completed 1-minute OHLCV bars before Feed Health.
- [x] Subscribe to heartbeats and bound reconnect attempts.
- [x] Allow pre-flight credential check to PASS explicitly for public providers.
- [ ] Run real network connectivity/subscription dry-run with execution hard-disabled.
- [ ] Observe completed real 1-minute bars through Feed Health and Operational Runtime.
- [ ] Only then authorize a supervised simulated-execution paper session.

- [x] Coinbase public market-data connectivity dry-run runner (bounded, execution OFF)

### Live Paper Bridge v1
- [x] Public Coinbase BTC-USD live market-data dry-run
- [x] Real-world trade-batch ordering regression protection
- [ ] Bounded live-data -> Operational Runtime -> PaperTradingSession -> Risk Engine -> PaperBroker proof
- Deferred until bounded proof: real exchange execution, API credentials, multi-asset live trading, long-running cloud deployment, production monitoring, calibrated transaction costs. These add operational/capital risk without helping prove the current boundary.

### Forward Paper Session v1
- [x] Prove bounded Coinbase live-data -> Operational Runtime -> PaperTradingSession -> Risk Engine -> PaperBroker path.
- [x] Add supervised longer-session runner with configurable healthy-bar bound.
- [x] Add append-only JSONL audit records for accepted/rejected bars, strategy/risk/order outcome, account snapshot and explicit real-orders=0 evidence.
- [ ] Prove a naturally occurring paper entry and exit over forward data; do not manufacture signals merely to demonstrate orders.
- [ ] Add crash-transparent strategy-history/aggregator recovery before claiming unattended restart continuity. Reason: existing checkpoint state restores broker/risk/feed/session continuity, but not the accumulating EMA history or an in-progress 1m trade bucket.
- [ ] Add unattended/cloud operation only after forward-session evidence, restart continuity and operational alerting are proven.

### Forward Paper Continuity / Recovery v1
- [x] Add atomic forward continuity state covering runtime checkpoint, EMA input history and in-progress Coinbase 1m aggregation bucket.
- [x] Add one-time bootstrap from the first v1 live audit so the existing open paper position is not forgotten.
- [x] Keep mutable `runtime/*.json` and `runtime/*.jsonl` artifacts out of Git; retain the first live audit as immutable milestone evidence under `docs/evidence/`.
- [ ] Prove continuity live: bootstrap the audited position, restart, and confirm cash/position/order sequence before processing additional bars.
- [ ] Longer unattended/cloud sessions remain deferred until live restart continuity is proven.

### Restart Gap Reconciliation v1
- [x] Distinguish an intentional process-restart gap from an in-session missing-data defect.
- [x] Make the first fresh excessive-gap boundary bar non-tradable and audit-visible.
- [x] Restore normal strict gap enforcement immediately after the boundary.
- [x] Bound resumed forward sessions by bars processed in the current invocation.
- [ ] Prove the reconciliation path on live Coinbase data while preserving the existing paper position and `REAL_orders=0`.


### Extended Forward Run Readiness + Session Report v1
- [x] Add deterministic latest-session JSONL reporting with fail-closed audit-boundary validation.
- [x] Report bars/rejections/rebases, signals, risk outcomes, paper fills, equity/P&L, max drawdown, final position and real-order evidence.
- [ ] Run the first supervised 30-60 bar Coinbase forward-paper session and review its report before increasing duration.
- [ ] Keep unattended/cloud execution deferred until repeated supervised runs are clean and operational alerting is defined.

### Coinbase Late-Trade Ordering Robustness v2
Extended forward observation exposed event-time reordering across separate Coinbase websocket messages. Add a bounded 2-second event-time reorder buffer before strict minute aggregation, persist the pending buffer in forward continuity state, and keep truly late trades fail-closed after the watermark. This adds a small intentional bar-finalization delay to preserve OHLCV correctness rather than silently dropping late trades.

- [x] Align Coinbase completed-bar freshness with interval-close semantics after late-trade reorder buffering.

### Coinbase Transport Resilience v1
- [x] Confirm Coinbase public transport already subscribes to heartbeats and has bounded reconnect.
- [x] Distinguish transport reconnect evidence from market-data/feed-health evidence.
- [x] Reset reconnect attempt budget after a successfully restored connection instead of accumulating transient outages for the life of the process.
- [x] Discard incomplete/pending 1m aggregation state across a disconnect; do not manufacture a bar from potentially missed trades.
- [x] Reconcile the first fresh excessive-gap bar after reconnect as a non-tradable boundary, then restore normal strict Feed Health checks.
- [x] Report repeated Feed Health safety shutdown as `RUNTIME_HALTED`, not `TRANSPORT_ENDED`.
- [ ] Prove reconnect/rebase behavior on live Coinbase data and then repeat the supervised 30-bar forward run.
- Deferred: multi-provider failover and distributed supervision. Reason: one-provider reconnect/recovery must first be proven repeatedly before adding redundant infrastructure.

- [x] Transport Failure Recovery v2: bounded reconnect backoff, fatal transport audit closure, continuity checkpoint.


## Reconnect Replay Reconciliation v1
- Completed Coinbase bars at or behind the already-accepted feed watermark are classified as provider replay and dropped before the trading/Feed Health pipeline.
- Replay drops remain audit-visible (`PROVIDER_REPLAY_DROPPED`) but do not consume the operational runtime consecutive-failure budget.
- Fresh forward bars still pass through strict freshness, ordering and missing-gap validation; real execution remains impossible.
- This change targets the observed 10:25 -> 10:23 -> 10:24 replay sequence that previously caused a false `RUNTIME_HALTED` during the supervised 30-bar run.

## Forward Operational Diagnostics v1
- Add transport-quality and market-time continuity metrics to the deterministic forward-session report.
- Add signal activity and Risk Engine rejection diagnostics without changing trading policy.
- Use the diagnostics to judge the next 60-bar supervised gate before multi-hour/overnight soak testing.

## Future Scale Milestone — 24/7 Market Universe Scanner and Orchestration

The current `BTC-USD` Coinbase path is a controlled proving ground for live-paper transport, continuity, Feed Health, risk and operational safety. It is **not** the intended final trading scope.

After single-symbol operational stability and extended forward evidence are proven, expand toward a 24/7 market-intelligence architecture:

1. **Universe Manager** — maintain a configurable universe across supported crypto, equities and other approved markets; understand venue/session calendars and which instruments are currently actionable.
2. **Lightweight Market Scanner** — continuously screen the broad universe using low-cost liquidity, volume, volatility, trend, momentum, breakout and regime criteria.
3. **Candidate Ranking** — rank/filter scanner output so only the strongest candidates enter expensive analysis.
4. **Deep Analysis** — run relevant Strategy Library / Market Regime / validation logic on shortlisted candidates rather than brute-forcing every strategy over every instrument continuously.
5. **Portfolio Gate** — apply aggregate exposure, concentration/correlation and capital-allocation controls across simultaneous opportunities.
6. **Execution Orchestration** — route only fully authorized opportunities to replaceable venue/broker execution boundaries.

### Activation gates

- Do not activate broad scanning while the one-symbol transport/runtime path is operationally unstable.
- First prove repeated supervised single-symbol forward runs, then multi-hour/overnight continuity and monitoring.
- Expand next to controlled multi-symbol live-paper data and scanner correctness before broad market-universe coverage.
- Keep real multi-market execution disabled until portfolio-level risk and venue/session handling are validated.

**Long-term operating principle:** the Agent may run 24/7 even though individual markets do not. It should continuously know which configured markets are open/relevant, scan the appropriate universe, rank opportunities, and trade only when the full strategy + risk + portfolio policy authorizes action.

### Hybrid WS + REST Recovery v1
- [x] Keep WebSocket as the primary low-latency Coinbase market-data path.
- [x] Add unauthenticated Coinbase public REST 1-minute candle client for continuity repair.
- [x] Detect exact missing minute range from the last accepted feed watermark to the first post-gap live bar.
- [x] Require exact REST coverage for every missing minute; never synthesize candles.
- [x] Catch up Feed/EMA/Risk/mark state without retroactively executing historical signals.
- [x] Audit every recovered bar and completed/failed recovery boundary.
- [x] Fail closed with `BACKFILL_FATAL` when verified continuity cannot be restored.
- [x] Enforce exact one-minute continuity at reconnect/restart boundaries so a 2m timestamp delta recovers the single missing 1m candle instead of passing via normal live `max_gap` tolerance.
- [x] Prove live hybrid recovery on supervised reconnect gaps; REST backfill restored missing history with zero recovery failures.
- [ ] Repeat the 60-bar operational-quality gate and require near-contiguous market-time coverage before increasing soak duration.
- Deferred: provider redundancy across independent venues, broad multi-symbol backfill orchestration and cloud 24/7 deployment. Reason: first prove one-symbol hybrid continuity end-to-end.

### Startup Historical Catch-up v1
- [x] Separate long restart/offline recovery from normal WebSocket reconnect recovery.
- [x] Preserve 300-minute reconnect safety limit.
- [x] Permit bounded startup catch-up (default 7 days) through chunked Coinbase REST 1m retrieval.
- [x] Require exact minute continuity and forbid retroactive orders during catch-up.
- [x] Audit startup catch-up separately and include it in continuity diagnostics.
- [x] Live evidence gate: recovered a 911-bar overnight gap with exact continuity, then completed the 60-bar Hybrid operational gate.


### Signal Activity & Strategy Behavior Analysis v1
- [x] Add read-only per-bar active-strategy diagnostics to forward audit evidence.
- [x] For EMA crossover, expose fast/slow relationship and spread in basis points without changing signal generation.
- [x] Summarize strategy relationship/spread and decision reasons in the deterministic forward-session report.
- [ ] Validate diagnostics on a short supervised live-paper probe.
- [ ] Do not tune strategy thresholds until observed behavior is explained with evidence.

### Hybrid 60-Bar Verification Gate — PASS WITH TRANSPORT WARNING
- [x] Run a fresh supervised 60-bar session after the exact one-minute recovery fix and diagnostics validation.
- [x] Require: 60/60 processed, `MAX_BARS`, `audit_complete=True`, hybrid failures=0, `observed_gap=0.0m`, `REAL_orders=0`.
- [x] Verify state continuity through reconnect/backfill and zero retroactive orders from recovery bars.
- [x] Record recovery evidence: 191 reconnect backfill bars + 56 startup catch-up bars across a 306-minute market span with zero observed market gap.
- [x] Record transport warning: 16 disconnects, 12 reconnects (75% success), ~2697.2s total outage, ~1967.4s max outage; causes included RESET and DNS.
- [x] Progress through multi-hour and overnight soak tests with transport quality as an explicit acceptance dimension.
- [x] Complete the reviewed 24-hour gate and authorize multi-day preparation only after it passes.
- [x] Validate transport in the controlled cloud runtime and add operational monitoring/alert classification before any unattended 24/7 live claim.

### Post-Recovery Position Reconciliation v1
- [x] Prove the lifecycle failure from forward evidence: LONG open before downtime; EMA20/EMA50 `ABOVE -> BELOW` occurs during startup catch-up; no retroactive SELL is allowed; later live bars are already BELOW/HOLD.
- [x] Detect actionable bearish strategy transitions while applying REST/startup recovery bars without executing orders on those bars.
- [x] Persist pending reconciliation state in the forward continuity checkpoint so a second process interruption cannot erase the required exit.
- [x] On the first fresh live bar, close the existing long at the current paper price/time through the existing broker/risk-observation path; never replay the historical fill.
- [x] Audit `RECOVERY_CROSSOVER_DETECTED` and `POST_RECOVERY_RECONCILIATION`; preserve `REAL orders=0`.
- [x] Add regression coverage for persistence, non-retroactive recovery, and first-live-bar exit execution.

### Strategy Behavior Diagnostics v2
- [x] Extend the read-only forward report with live ABOVE/BELOW transition counts and consecutive regime-run lengths.
- [x] Separate live strategy transitions from audited recovery crossovers so recovery evidence is not mistaken for executable live activity.
- [x] Summarize bars spent with an open position versus flat and mark-to-market equity change across observed open-position bars.
- [x] Validate v2 on a fresh supervised 60-bar forward-paper sample before any EMA threshold/timeframe tuning.
- [x] Complete the Hybrid 60-Bar Verification Gate before longer soak testing; result: PASS WITH TRANSPORT WARNING.
- [ ] Defer multi-timeframe swing decision architecture until infrastructure/continuity gates pass; 1m remains the fast infrastructure validation clock, not the final trading-policy commitment.

### Risk/Reward Decision Diagnostics v1
- [x] Reproduce the live BUY boundary rejection at entry `63850.18`: planned exact 3R recomputed as `2.9999999999999885` and was falsely rejected by strict floating-point comparison.
- [x] Add regression coverage for exact-threshold acceptance using the observed live price construction.
- [x] Add a separate guard proving a meaningfully sub-threshold ratio remains rejected.
- [x] Apply a narrowly bounded relative tolerance only to minimum reward/risk threshold equality; keep stop/target validation, sizing and rejection policy unchanged.
- [x] Persist planned entry, stop, target, computed reward/risk and required minimum in approved and rejected paper BUY events.
- [x] Summarize reward/risk evaluation counts, rejection counts, observed range and required thresholds in the read-only forward-session report.
- [x] Confirm the complete local Windows/Python 3.14.6 repository passes all 553 tests before milestone commit/push.

Next after local validation: longer supervised paper sessions, operational readiness and controlled cloud transport/monitoring validation before unattended 24/7 deployment.

### Operational Monitoring & Alerting v1
- [x] Add an independent read-only monitor over the append-only forward audit and continuity state.
- [x] Classify operational state as `OK`, `WARNING` or `CRITICAL` with stable machine-readable alert codes.
- [x] Detect missing, unreadable or stale audit/checkpoint evidence while an active session is expected to progress.
- [x] Detect `BACKFILL_FATAL`, `TRANSPORT_FATAL`, `RUNTIME_HALTED`, REST backfill failure and transport reconnect exhaustion.
- [x] Detect non-zero REAL-order evidence and an active Risk Engine kill switch as critical safety violations.
- [x] Warn on current transport disconnect and pending post-recovery position reconciliation.
- [x] Add `recorded_at` to new audit records and `saved_at` to new continuity checkpoints for deterministic freshness evaluation.
- [x] Provide operator-readable and JSON output plus exit codes `0=OK`, `1=WARNING`, `2=CRITICAL` for cloud watchdog integration.
- [x] Confirm the complete local Windows/Python 3.14.6 repository passes all 572 tests before milestone commit/push.
- [x] Run the monitor against retained real runtime audit/state artifacts; result: `OK / COMPLETED / MAX_BARS`, matching audit/checkpoint age, `REAL_orders=0`, zero alerts.

Deferred from v1: email/Slack/SMS delivery, automatic restart, service manager/container orchestration and cloud scheduler configuration. Reason: notification and supervision adapters must consume a proven deterministic monitoring decision boundary rather than duplicate operational policy inside provider-specific integrations.

### Cloud Runtime Readiness v1
- [x] Add a provider-neutral pre-deployment gate that does not start the trading runtime or provision infrastructure.
- [x] Require explicit `PAPER` mode and explicit real-execution disablement.
- [x] Require a positive bounded forward-session bar count.
- [x] Require a positive monitoring interval below the stale-evidence threshold.
- [x] Require distinct audit/state files inside one absolute persistent runtime directory.
- [x] Probe persistent storage with bounded write/read/cleanup and block the probe when path validation fails.
- [x] Verify forward-paper and operational-monitoring entrypoints are importable.
- [x] Require the validated Python 3.12-3.14 runtime range.
- [x] Provide readable/JSON evidence and deterministic exit codes `0=PASS`, `2=FAIL`.
- [x] Confirm 13/13 focused tests and the complete 585/585 local Windows/Python 3.14.6 repository suite before milestone commit/push.
- [x] Run the real CLI gate with safe PAPER configuration; result: all seven readiness checks PASS.

Deferred from v1: cloud-provider selection, paid resource creation, container/service-manager configuration, notification delivery and an actual cloud trading process. Next after local validation: select a controlled cloud runtime and execute a bounded paper-only transport/monitoring gate before longer soak testing.

### Controlled Cloud Deployment Baseline v1
- [x] Select a one-month controlled EU cloud host: Hetzner CPX22 in Nuremberg, Ubuntu 24.04 LTS, x86, 2 vCPU, 4 GB RAM and 80 GB SSD.
- [x] Protect the Hetzner account with 2FA and retain an offline recovery key.
- [x] Use a dedicated passphrase-protected ED25519 SSH key; do not create or distribute a server root password.
- [x] Attach a Hetzner Cloud Firewall with SSH and ICMP inbound rules and unrestricted required outbound connectivity.
- [x] Install available Ubuntu LTS security updates and prove controlled reboot plus SSH-key reconnection.
- [x] Remove the clean-clone dependency of four Strategy Engine tests on Git-ignored `data/AAPL.csv` by using deterministic in-memory OHLCV input.
- [x] Confirm the isolated clean repository passes all 585 tests without local CSV artifacts.
- [x] Confirm 9/9 focused Strategy Engine tests and the complete 585/585 local Windows/Python 3.14.6 suite before milestone commit/push.
- [x] Deploy exact commit `6095960` to CPX22 and pass 9/9 focused plus 585/585 complete tests on Ubuntu/Python 3.12.3.
- [x] Configure root-only `/var/lib/ai-alpha` persistent storage and pass all seven provider-neutral Cloud Runtime Readiness checks.
- [x] Complete a systemd-backed five-bar PAPER smoke session with `success/0`, report `PASS`, complete audit, zero rejected bars, zero disconnects, `observed_gap=0.0m` and `REAL=0`.
- [x] Run Operational Monitoring over the cloud audit/state evidence; result: `OK / COMPLETED / MAX_BARS`, zero alerts and `REAL_orders=0`.

### Cloud Operational Soak Progression v1
- [x] Define a repeatable non-root PAPER-only systemd service with pre-start Cloud Readiness, explicit real-execution lock, ten bounded bars, persistent audit/state paths, rate-limited failure restart and process hardening.
- [x] Define a persistent one-minute read-only Operational Monitoring timer that retains readable decisions in journald and cannot control trading.
- [x] Add deterministic `resumed=True/False` evidence to the existing forward-session report without changing trading behavior.
- [x] Prove the deployment contract with 10/10 focused infrastructure tests, 22/22 combined supervision/report tests, systemd 255 security scores `3.0 OK` / `2.7 OK`, and an isolated 595/595 full suite.
- [x] Confirm 22/22 combined supervision/report tests and the complete 595/595 local Windows/Python 3.14.6 suite before milestone commit/push.
- [x] Install exact commit `accedf0` on CPX22, pass 22/22 focused and 595/595 complete Ubuntu/Python 3.12.3 tests, native `systemd-analyze verify` and all seven pre-start Cloud Runtime Readiness checks.
- [x] Prove controlled process restart after durable checkpoints: `SIGINT` stop, clean systemd result, second readiness PASS, `resumed=True`, safe provider replay drop and no automatic crash restart.
- [x] Complete the restarted ten-bar session with report `PASS`, complete audit, zero rejected bars, zero disconnects, `observed_gap=0.0m`, `MAX_BARS`, `REAL=0` and process `success/0`.
- [x] Enable only the one-minute monitoring timer and verify recurring `OK / COMPLETED / MAX_BARS`, zero-alert journal evidence while the PAPER service remains boot-disabled and inactive after completion.
- [x] Replace duplicated ten-bar literals with one committed, root-owned `AI_ALPHA_SESSION_BARS` configuration consumed by both Cloud Runtime Readiness and the forward runner; current reviewed bound: 180 one-minute bars.
- [x] Confirm the bounded-soak configuration with 25/25 focused supervision/readiness tests and the complete 597/597 local Windows/Python 3.14.6 suite before implementation commit/push.
- [x] Deploy exact bounded-soak commit `0d5477c`, rerun the 597/597 cloud suite, native unit verification and all seven pre-start readiness checks.
- [x] Complete the 180-bar cloud PAPER gate: the recovered attempt passed 180/180, complete audit, `MAX_BARS`, `observed_gap=0.0m`, zero recovery failures and `REAL_orders=0`; classify the complete gate `PASS WITH ORDERING/RESTART WARNING` because an earlier out-of-order failure/restart was hidden by latest-session monitoring.
- [x] Implement append-only systemd `PROCESS_INCIDENT` evidence plus current-attempt `CRITICAL` and recovered-attempt `PREVIOUS_PROCESS_FAILURE` monitoring policy without changing restart ownership or trading behavior.
- [x] Validate Restart Incident Visibility locally with 39/39 focused tests, the complete 605/605 Python 3.12.13 suite and isolated native systemd 255 syntax verification.
- [x] Commit/push exact incident-visibility commit `7d3a203` and reproduce 39/39 focused plus 605/605 complete tests on Windows/Python 3.14.6.
- [x] Deploy exact commit `7d3a203`, reproduce 39/39 focused plus 605/605 complete cloud tests, pass native unit verification and install without activating PAPER.
- [x] Prove the controlled cloud lifecycle: `SIGKILL -> PROCESS_INCIDENT -> CRITICAL / PROCESS_FAILURE -> one ten-second systemd restart -> resumed=True -> PREVIOUS_PROCESS_FAILURE WARNING`, with all seven restart readiness checks passing and `REAL_orders=0` invariant.
- [x] Complete the restarted 180-bar attempt with report `PASS`, complete audit, zero rejected bars, zero disconnects, zero recovery failures, `observed_gap=0.0m`, `MAX_BARS`, three filled PAPER orders and `REAL=0`.
- [x] Prove direct and recurring timer monitoring retain `WARNING / COMPLETED / MAX_BARS` plus the exact previous process failure after healthy completion; PAPER ends inactive/boot-disabled and the monitor timer remains active/enabled.
- [x] Define the next reviewed root-owned overnight bound as 720 completed one-minute bars, approximately twelve hours and strictly below the separate 24-hour gate.
- [x] Define clean overnight acceptance: 720/720, zero rejected bars, complete audit, exact continuity, zero recovery failures/exhaustion, 100% reconnect success when needed, normal systemd completion with no automatic restart, final monitoring `OK` and `REAL_orders=0`.
- [x] Validate preparation locally with 13/13 supervision-contract tests, 26/26 combined supervision/readiness tests, the complete 605/605 Python 3.12.13 suite, clean whitespace and installer shell syntax.
- [x] Reproduce 26/26 combined supervision/readiness tests and the complete 605/605 suite on Windows/Python 3.14.6 with a clean patch-format check.
- [x] Commit and push exact overnight-preparation revision `d96c981`.
- [x] Deploy exact revision `d96c981` without activation; reproduce 26/26 focused and 605/605 complete cloud tests, native systemd verification and all seven Cloud Runtime Readiness checks.
- [x] Run the explicit overnight PAPER gate and classify it `FAIL WITH SAFETY PRESERVED`: seven out-of-order trade failures/restarts, no 720-bar terminal boundary and `REAL_orders=0` throughout.
- [x] Prove that most ordering failures were not immediately reconnect-bound, and retain exact process-incident timestamps without widening the two-second reorder policy.
- [x] Stop the final process safely and expose the missing controlled-stop `SESSION_END`: systemd success/130, but stale `RUNNING` monitoring and an intentionally refused incomplete forward report.
- [x] Implement typed late-trade timing evidence, durable `LATE_TRADE_REJECTED` plus `ORDERING_FATAL`, explicit `OPERATOR_STOP`, MAX_BARS-only report PASS semantics and a two-start supervision budget.
- [x] Validate the failure-closure implementation locally and from a detached clean overnight-base worktree with 97/97 focused tests, the complete 615/615 Python 3.12.13 suite, clean whitespace and installer shell syntax.
- [x] Apply the exact closure patch on Windows; reproduce 97/97 focused and 615/615 full-suite validation, then commit/push exact revision `93b7565`.
- [x] Deploy exact closure revision `93b7565` non-activating; reproduce 97/97 focused and 615/615 complete cloud tests, native systemd verification and all seven readiness checks.
- [x] Run a short bounded cloud PAPER diagnostic: six fresh contiguous bars after 121 startup catch-up bars, `NRestarts=0`, monitoring `OK / RUNNING`, then clean `OPERATOR_STOP`, `audit_complete=True`, no stale alerts, no new process incident, `observed_gap=0.0m` and `REAL_orders=0`. No live late-trade occurred; the typed `ORDERING_FATAL` path remains deterministic-test evidence rather than a live claim.
- [x] Reconcile the observed systemd garbage-collection case: when the inactive unit is explicitly reported not loaded, its start-limit counters are already absent; verify the installed unit is loadable before direct start, and abort activation for every other `reset-failed` error.
- [x] Review the second non-injected 720-bar attempt on `e0592ff`: two
  `ORDERING_FATAL` attempts after 266 and 46 fresh bars, exact 19.637/56.435s
  timing evidence, enforced two-start ceiling and `REAL_orders=0`.
- [x] Verify Coinbase's provider-message contract and add connection-local
  `market_trades.sequence_num` validation before trade-time aggregation.
- [x] Drop lower/equal provider envelopes whole as audit-visible
  `PROVIDER_MESSAGE_REPLAY_DROPPED`; never allow their trades into OHLCV, Feed
  Health, Strategy, Risk or PaperBroker.
- [x] Treat missing/invalid/forward-gap sequence evidence as a socket-integrity
  failure before payload consumption; reuse bounded reconnect plus exact
  non-tradable REST recovery and retain `TRANSPORT_FATAL` on exhaustion.
- [x] Prevent partial-minute leakage after sequence reconnect: audit-drop every
  completed bucket before the socket's first trusted full-minute boundary,
  recover it exactly through REST, and expose `sequence_boundary_drops`.
- [x] Keep sequence recovery genuinely bounded: heartbeat-only reconnects do
  not reset consecutive failures; only a valid `market_trades` payload does.
- [x] Preserve the strict two-second late-trade rule for correctly sequenced
  payloads and add `trade_id`, message sequence/time and event type to fatal
  evidence.
- [x] Pass 112/112 focused provider/forward/report/monitoring/supervision tests
  and the complete 630/630 local repository suite.
- [x] Reproduce the first provider-sequence patch on Windows, commit/push exact
  revision `066852b`, deploy it non-activating to CPX22 and reproduce 112/112
  focused plus 630/630 complete tests and all seven readiness checks.
- [x] Reject and safely stop the first sequence-aware diagnostic after it exposed
  false `0 -> 3/4/5` gaps; retain `success/0`, `NRestarts=0`, inactive/disabled
  PAPER and `REAL_orders=0` evidence.
- [x] Capture the public connection's exact sequenced interleaving through a
  read-only probe: market trades, subscription acknowledgements and heartbeats
  shared one consecutive envelope stream from 0 through 39.
- [x] Correct validation to observe all sequence-bearing envelopes before channel
  routing, retain the gap's provider channel and pass 114/114 focused plus
  632/632 complete local tests.
- [x] Reproduce the cross-channel correction on Windows with 114/114 focused and
  632/632 complete tests, commit/push exact revision `4ff9070`, deploy it
  non-activating to CPX22 and repeat both suites plus all seven readiness checks.
- [x] Pass the second short non-injected sequence-aware cloud diagnostic: 1559
  startup catch-up bars, 13 fresh bars, zero rejected/rebase/transport/replay/
  sequence-boundary/recovery failures, exact 1571-minute continuity,
  `NRestarts=0`, clean `OPERATOR_STOP` and `REAL_orders=0`.
- [x] Review the clean 720-bar attempt on `46ed877`: 603/720 fresh bars before
  one correctly sequenced `snapshot` carried a 58.912-second-old trade and
  triggered fail-closed `ORDERING_FATAL`; preserve complete audit and
  `REAL_orders=0` evidence.
- [x] Keep cross-channel sequence validation ahead of event routing, but prevent
  explicit market-trades snapshot history from entering the incremental reorder
  heap or OHLCV aggregation.
- [x] Convert every snapshot into an audit-visible provider boundary, reset the
  partial WebSocket minute, discard it explicitly, recover exact REST continuity
  without trading and preserve startup `RESTART` catch-up semantics.
- [x] Expose handled `snapshot_boundaries` / `snapshot_boundary_drops`, retain
  monitoring neutrality and enrich future ordering-fatals with event/trade/
  provider-message identity without widening the two-second update rule.
- [x] Pass 119/119 focused snapshot/provider/forward/report/monitoring/
  supervision tests and the complete 637/637 local suite.
- [x] Reproduce exact snapshot-boundary revision `370664d` on Windows and CPX22
  with 119/119 focused and 637/637 complete tests, non-activating install, all
  seven readiness checks and a 112-bar clean diagnostic after 204 catch-up bars.
- [x] Review the next 720-bar failure: 443-bar and 27-bar attempts ended on the
  exact in-band snapshot/update pairs `10784 -> 10786` and `7423 -> 7425`;
  retain complete fatal evidence, the two-start ceiling and `REAL_orders=0`.
- [x] Quarantine only post-snapshot provider history older than the trusted full-
  minute floor before aggregation, keep the floor after live processing resumes,
  preserve exact non-tradable REST recovery and expose audit/report evidence.
- [x] Prove both cloud incidents now continue safely while a genuinely late
  post-boundary trade remains `ORDERING_FATAL`; pass 124/124 focused and 642/642
  complete local tests without widening the two-second watermark.
- [x] Reproduce exact post-snapshot quarantine revision `e7a95ac` on Windows and
  CPX22 with 124/124 focused and 642/642 complete tests, non-activating install
  and all seven Cloud Runtime Readiness checks.
- [x] Pass the short live quarantine diagnostic: 630 snapshot-era trades safely
  filtered, one boundary bar dropped, 942 startup-catch-up bars, six fresh
  contiguous bars, exact 947-minute continuity, no transport/recovery failure,
  no ordering fatal, `NRestarts=0`, clean `OPERATOR_STOP` and `REAL_orders=0`.
- [x] Pass the clean 720-bar overnight gate on exact revision `db5615e`: normal
  `MAX_BARS`, 720/720 processed, zero rejected/rebased bars, complete audit,
  `NRestarts=0`, 20 PAPER fills, final flat position and `REAL_orders=0`.
- [x] Preserve exact live provider/recovery evidence across that gate: 13
  snapshot boundaries/drops, 5,777 quarantined snapshot-era trades, 29 startup
  catch-up plus 12 REST backfill bars, zero recovery/transport/replay failures
  and `observed_gap=0.0m` across 760 expected market minutes.
- [x] Finish the overnight gate with systemd `success/0`, final monitoring
  `OK / COMPLETED / MAX_BARS`, zero alerts and all cloud units safely parked.
- [x] Prepare a repository-reviewed 1,440-bar 24-hour PAPER gate through the
  committed root-owned bound, preserving non-activating installation, PAPER
  boot-disablement and all existing acceptance conditions.
- [x] Reproduce focused/full tests, non-activating deployment and all seven
  readiness checks on the exact committed 1,440-bar revision before activation.
- [x] Run and review the bounded 24-hour PAPER gate with all existing continuity,
  transport, supervision, monitoring and `REAL_orders=0` conditions.
- [x] Close the 24-hour gate as PASS: 1,440/1,440, complete audit, systemd
  `success/0`, `NRestarts=0`, 100% recovery across six disconnects, exact
  1,947-minute continuity, final monitoring `OK`, zero alerts and `REAL=0`.
- [x] Define the exact multi-day PAPER bound as 4,320 fresh one-minute bars
  (three days) with the existing safety/continuity gates plus explicit final
  CPU-time, memory-peak and swap/OOM review; do not edit the cloud host ad hoc.
- [x] Prepare the committed root-owned 4,320-bar configuration without changing
  runtime, Strategy, Risk, recovery, broker or monitoring behavior.
- [x] Reproduce tests, non-activating deployment and readiness before any
  multi-day activation.
- [x] Complete and review the bounded multi-day PAPER gate: 4,320/4,320,
  complete audit, `MAX_BARS`, systemd `success/0`, `NRestarts=0`, exact
  4,614-minute continuity, 100% recovery across 15 disconnects, final
  monitoring `OK`, zero alerts, `REAL=0` and clean resource/OOM review.
- [x] Prepare Strategy Evaluation Protocol v1 locally without touching the
  active cloud run: freeze candidate identity/scope, require reviewed baseline
  and cost-stress passes, minimum unseen evidence and explicit research-only
  outcomes.
- [x] Reproduce Strategy Evaluation Protocol v1 on Windows with 84/84 focused
  and 663/663 complete tests, commit/push exact revision `b69f5b1`, and leave
  the active cloud process untouched until the three-day gate closes.
- [x] Fast-forward the parked cloud repository non-activating to exact
  `9a063fa`; reproduce 20/20 standalone, 84/84 focused and 663/663 complete
  cloud tests, pass all seven readiness checks, and keep every trading and
  monitoring unit parked.
- [x] Close Research Execution Timing Integrity v1 before inspecting a first
  candidate result: require completed-close signals to execute only at the
  following Open, retain signal/execution provenance, align the benchmark,
  reproduce 130/130 focused and 684/684 complete tests on Windows and cloud,
  pass all seven readiness checks, and keep runtime units parked on exact
  closure revision `daf6c5d`.
- [x] Freeze the first candidate before inspecting results: existing long-only
  EMA 20/50, BTC-USD plus ETH-USD, native six-hour candles, next-Open causal
  execution, exact historical range, conservative baseline/stress costs and no
  optimization.
- [x] Add a read-only Coinbase historical builder with exact continuous-grid
  validation, canonical CSV/manifest bytes and per-file plus manifest SHA-256
  evidence; independently reject any data/manifest drift before candidate lock.
- [x] Validate pre-registration locally with 160/160 focused and 714/714 full
  tests using injected provider responses and without downloading or evaluating
  the historical dataset.
- [x] Reproduce 160/160 focused and 714/714 full Windows tests, close a test-only
  ASCII/LF portability issue, commit/push exact revision `27dacb3`, then
  reproduce both suites plus all seven readiness checks on parked CPX22 without
  activating any systemd unit.
- [x] Acquire the exact frozen BTC/ETH dataset and record its canonical manifest
  SHA-256 without inspecting strategy performance.
- [x] Execute the immutable first-candidate Strategy Evaluation Protocol once,
  classify its baseline/stress evidence, and prohibit post-result parameter
  mutation. Profitability evidence, bounded forward-PAPER promotion and live-
  money authorization remain separate gates.
- [x] Close candidate v1 as `REJECTED`: both baseline and stress aggregates
  rejected both assets, walk-forward persistence and statistical falsification
  failed, and worst-profile OOS drawdown exceeded the 20% ceiling for BTC and
  ETH. Retain PAPER, optimization and live authorization as false.
- [x] Prepare Timeframe Sensitivity Study v1 as research-only analysis across
  `1h`, `6h` and `1d` BTC/ETH evidence. Reuse the exact recorded 6h report,
  require new canonical 1h/1d locks, compare equal 720-day train and 180-day
  test durations, and generate neither ranking nor winner.
- [x] Reproduce the complete 740/740 suite on Windows, review the exact
  study/refactor scope, commit revision `c39fd7c` and push it before acquiring
  new data.
- [x] Acquire and independently lock the exact 2,769-row 1d BTC/ETH development
  dataset under manifest SHA-256
  `77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691`.
- [x] Record the first one-hour acquisition as a safe technical incident after
  Coinbase omitted 19 expected BTC buckets and the builder wrote no 1h files.
  Prepare bounded exact-gap recovery without filling or synthetic candles.
- [x] Reproduce the recovery patch with 23/23 focused and 746/746 full Windows
  tests, commit exact revision `0b3e5bd` and push it before retry.
- [x] Record acquisition attempt 2 as safe persistent provider gaps: two exact
  passes could not recover 19 BTC buckets, independent 1h/5m/Advanced checks
  found no in-range candle and no dataset or evaluation evidence was written.
- [x] Prepare sparse-native schema v2 locally with complete gap accounting,
  atomic two-asset persistence, no synthetic data and calendar-time validation;
  pass 216/216 focused and 760/760 complete tests.
- [x] Reproduce schema v2 on Windows with 30/30 focused and 761/761 complete
  tests, review the datetime-unit compatibility repair, commit exact revision
  `b61853f` and push before acquisition attempt 3.
- [x] Acquire and independently lock observed native 1h BTC/ETH data against all
  66,456 expected buckets; bind 19 BTC and 18 ETH gaps under manifest SHA-256
  `b9ba8126ca0612402919dd7f0f0096db2b2ef2f0a7d0669b6848276e88bc8157`,
  then commit/push only reviewed 1h/1d manifests and sidecars as `e07b93e`.
- [x] Record study attempt 1 as a pre-staging technical serialization incident:
  a defined positive-infinite daily `profit_factor` was not standard JSON, and
  no final/staging evidence or aggregate comparison was written.
- [x] Reproduce schema-v3 positive-infinite profit-factor encoding on Windows
  with 32/32 focused and 763/763 complete tests; commit/push exact revision
  `8042816` without changing frozen strategy/data/configuration.
- [x] Execute and record the deterministic exploratory comparison under report
  SHA-256
  `505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab`
  and evidence commit `cb43a74`.
- [x] Close Timeframe Sensitivity Study v1 as `COMPLETED_NO_ROBUST_EDGE`: all
  baseline/stress aggregates and 12 asset/profile views are rejected, with no
  ranking, selected timeframe, candidate-v2 or promotion authorization.
- [x] Prepare Strategy Research Inventory and Failure-Mode Analysis v1 locally:
  inventory nine implementations, retain eight as unevaluated components, audit
  only synthetic causal integration and accept only the exact closed study
  report for fact extraction; pass 10/10 focused and 773/773 complete tests.
- [x] Reproduce the inventory/audit boundary on Windows with 180/180 focused and
  773/773 complete tests, commit/push exact revision `53202c0`, then run its
  non-evaluating CLI against the recorded report.
- [x] Prepare locally a fixed standalone strategy-family development screening
  scope with no parameter sweep, automatic ranking, indicator combination or
  candidate-v2 authorization before producing new performance evidence; pass
  15/15 new, 233/233 focused and 788/788 complete tests with no performance
  runner.
- [x] Reproduce Strategy Family Screening Protocol v1 on Windows with 15/15 new
  and 788/788 complete tests, commit/push exact revision `c7fc411`, then validate
  the frozen six-hour manifest/11,076 rows per asset without performance.
- [x] Prepare locally a one-shot canonical screening runner that preserves the
  frozen descriptive multiple-comparison policy; pass 19/19 new, 37/37
  runner/timeframe regression and 807/807 complete tests.
- [x] Reproduce the screening runner on Windows with 37/37 focused and 807/807
  complete tests, commit/push exact revision `e8afe12`, then pass clean
  preflight with absent final/staging evidence.
- [x] Execute the frozen eight-strategy development screen exactly once and
  record canonical report SHA-256
  `9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f`
  under evidence revision `2973636`; all eight standalone default variants are
  `SCREEN_OUT`, with no ranking, selection or promotion.
- [x] Close screening interpretation at the exact-configuration boundary:
  reject the eight frozen standalone variants as deployable strategies without
  rejecting their indicator families as possible features or components.
- [x] Attribute gross signal versus cost/turnover, exposure, holding-period,
  drawdown and market-regime failure on inspected development data before
  designing another candidate.
- [x] Integrate and evidence-lock Failure Attribution and Volume Research
  Protocol v1: freeze zero/baseline/stress diagnostic views, causal signal-bar
  regime attribution and per-asset relative-volume/OBV semantics without
  replaying performance.
- [x] Add a separately reviewed one-shot attribution runner; report cost,
  turnover, exposure, holding, drawdown, market-regime, volume-regime and
  persistence evidence without ranking the rejected configurations.
- [x] Reproduce Failure Attribution Runner v1 on Windows, commit/push the exact
  implementation, pass an absent-evidence preflight and execute the frozen
  24-replay diagnostic matrix exactly once.
- [x] Record and close canonical Failure Attribution report SHA-256
  `e4193bff907a2121701e7ddc1d740894641c7bf427c9501fd4ecd4392a1f81f4`:
  retain nine positive zero-cost views, universal real-cost rejection,
  excessive turnover/drawdown and ADX high-volume cross-asset evidence without
  generating a winner or candidate.
- [x] Pre-register Alpha Development Protocol v2 around an exact three-variant
  ADX/market-regime/relative-volume ablation chain; freeze causal signal rules,
  risk/turnover boundaries and strict attribution-evidence locking without a
  performance runner or parameter leaderboard.
- [x] Freeze a venue/execution sensitivity boundary using dated Coinbase and
  Kraken taker assumptions, while blocking maker evidence until causal
  placement/non-fill/partial-fill semantics and actual account eligibility are
  independently verified.
- [x] Implement and locally validate active protective stop/target execution in the
  backtester. Include next-open sizing from lagged ATR, gap-through-stop and
  conservative same-bar stop/target ordering before Alpha v2 performance.
- [x] Reproduce Protective Exit Engine v1 on Windows with 166/166 focused and
  921/921 complete tests, commit/push revision `0f7c13b` and re-lock Alpha
  Development v2 without executing performance.
- [x] Build and locally validate a separately reviewed one-shot Alpha v2
  development runner that binds exact strategy, risk, protective-exit and
  permitted taker scenarios; retain no automatic ranking or promotion.
- [x] Reproduce Alpha Development Runner v2 on Windows with 203/203 focused and
  944/944 complete tests, commit/push revision `5a9018b` and pass an
  absent-evidence preflight before one explicit nine-evaluation development
  run.
- [x] Record and close canonical Alpha Development v2 report SHA-256
  `19627f7002fc3159729ea61d22ead0fa25deca455612764121ea96fd3eaf71a0`
  under evidence revision `b2a5e60`: all three variants are `SCREEN_OUT`, no
  mechanism retains development interest and no promotion is authorized.
- [x] Confirm that active risk/protective execution plus regime/volume filters
  bound baseline drawdown, turnover and cost while negative absolute return,
  36.36% walk-forward persistence and failed falsification remain the
  controlling signal-quality failures.
- [x] Reproduce and integrate Alpha Development Protocol v2 on Windows under
  revision `45a3e00`, pass 24/24 focused and 890/890 complete tests, then lock
  the exact development manifest and attribution report without executing
  joint performance.
- [x] Pre-register a bounded Alpha Discovery and Calibration Protocol covering
  exit/trade-path attribution, a residual zero-cost diagnostic and a small,
  hypothesis-led set of indicator combinations, regime filters, risk sizing and
  temporally separated parameter calibration; prohibit a result leaderboard.
- [x] Reproduce and integrate Alpha Discovery and Calibration Protocol v1 on
  Windows under revision `4132cf8`, verify its exact Alpha v2 evidence lock and
  retain every execution and promotion authorization as false.
- [x] Implement causal EMA trend structure, completed-bar +1R break-even
  transitions and MFE/MAE/holding-path evidence before any calibration runner.
- [x] Build, reproduce and integrate a separately reviewed one-shot nested
  calibration runner after its prerequisite components passed focused and
  complete regression.
- [x] Evaluate joint causal intersections rather than adding marginal regime,
  relative-volume and OBV summaries. Require turnover/cost and risk controls
  before a development mechanism may retain interest.
- [x] Run calibration only inside training/validation boundaries and test the
  complete adaptive procedure exactly as it would operate live.
- [x] Record and close Alpha Discovery v1 report SHA-256
  `2fc8f4d1a5d690c072408bc2d299516904feb58b2e2f40345983641bf26ed678`:
  select no configuration, hold cash in seven of seven outer windows and retain
  no promotion authorization.
- [x] Pre-register one structurally new trend-pullback plus causal volume
  contraction/re-expansion hypothesis without treating inspected results as
  unseen evidence or broadening the closed parameter grid.
- [x] Implement and separately review the causal pullback state machine and
  executable four-member strategy without running market performance.
- [x] Build a one-shot nested development runner only after the state machine,
  strategy identity, risk execution and exact evidence lock pass regression.
- [x] Reproduce and integrate Trend Pullback Volume Runner v1 on Windows, pass
  full regression and a clean absent-evidence preflight, then execute the
  frozen nested development procedure exactly once.
- [x] Record and close Trend Pullback Volume v1 report SHA-256
  `7598ea3616a60753d5be5b4d7af8c146f1bea881cb2d43ed71ea16cebdd685e3`:
  select no member, hold cash in seven of seven outer windows and identify
  signal scarcity plus failed persistence as the controlling failures.
- [ ] DEFERRED: retain exact pullback trade-path and exit attribution as
  inspected six-hour diagnostic work. Do not treat it as the active next
  boundary or transfer its observations into the new daily research sleeves
  without explicit pre-registration.
- [ ] Before formal candidate-v2 evaluation, freeze a new immutable identity
  and independently lock a genuinely unseen future-validation boundary.

## Selective Swing Trading Research Reset v1 — NEXT

- [x] Reproduce and integrate the documentation-only Selective Swing Trading
  Research Mandate v1 on Windows from a clean synchronized repository.
- [x] Reproduce and integrate the BTC/ETH/XRP Daily Data and Blinded Replay
  Protocol v1: exact existing BTC/ETH reference, explicit XRP provider-audit
  requirement, no synthetic gaps and no performance fields.
- [x] Reproduce and integrate Selective Swing Portfolio Construction Protocol
  v1: cash-first risk-limited `1/n`, three initial equity positions, winner-only
  pyramiding boundary, three isolated evidence books, first-class no-trade
  gates, offline-only AI improvement and separate rare intraday contingency.
- [ ] Freeze executable numeric position-risk, total-open-risk, portfolio
  loss-stop and gap/fill policies only after strategy/data evidence; current
  documented ranges are provisional research starting points.
- [x] Audit official provider/history evidence, reject Coinbase as the common
  three-asset source because of its 2021–2023 XRP suspension, and select
  Kraken's official spot OHLCVT archive path for BTC/USD, ETH/USD and XRP/USD.
- [x] Implement and locally validate a non-performance Kraken daily lock
  builder: full ZIP-member inventory, native 1440-minute pair extraction,
  exact duplicate/REST overlap, explicit gaps, atomic publication and
  independent hash re-lock without downloading market data.
- [x] Execute and close the v1 archive/REST acquisition path without
  publication: OHLC matched across 482 overlapping rows per asset, but volume
  and trade-count equality failed, so REST stitching remained blocked.
- [x] Acquire, byte-inventory and lock the v2 archive-only Kraken daily BTC,
  ETH and XRP dataset from the exact frozen complete and Q1 2026 ZIP bytes
  through 2026-03-31, with explicit gaps and no network, strategy or
  performance execution.
- [x] Build a blinded sequential chart-replay component that records
  entry, skip and exit decisions before future bars are revealed.
- [x] Review and prepare the Kraken-bound replay methodology: exact-decimal
  visible hashes, price-independent bounded episode selection, durable chained
  decisions, explicit unresolved terminal positions and independent evidence
  re-lock without executing a real chart replay.
- [x] Execute one sealed preflight against the exact external Kraken v2 lock,
  review only counts/hashes/safety flags and record compact evidence without
  exposing selected episode timestamps.
- [x] Review the compact sealed-preflight evidence and prepare a fail-closed,
  one-episode-at-a-time supervised runner without opening a participant view or
  authorizing real replay.
- [x] Integrate the one-episode-at-a-time supervised runner on Windows, verify
  review mode and explicitly decide to authorize only the first BTC episode.
- [x] Complete the 60-decision BTC reconstruction and retain aggregate evidence
  SHA-256
  `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
  without calculating performance or authorizing the following asset.
- [x] Pause supervised replay v1 with ETH/XRP unopened after confirming that
  unassisted discretionary labeling is too underspecified and cognitively
  expensive to serve as the strategy-construction engine.

## AI-Driven Crypto Research v2 — ACTIVE

- [x] Freeze the first deterministic causal feature contract around lagged
  decline, relative volume, true range/ATR expansion, close location and
  completed-bar return without signal thresholds or trading actions.
- [x] Implement the standalone causal feature engine with explicit window
  configuration, strict continuous-daily validation, unavailable warm-up
  values, prefix-causality tests and no real dataset execution.
- [ ] Reproduce the focused and complete Windows regression, inspect the
  nonexecuting V2 declaration, then commit and push this exact first milestone.
- [ ] Pre-register the smallest deterministic
  `FLAT -> ARMED -> LONG -> FLAT` capitulation/stabilization/confirmation state
  machine, including explanation fields, expiry and fail-closed missing-feature
  behavior before implementing it.
- [ ] Freeze next-open execution, structural stop, risk sizing, minimum causal
  reward room, protective exits and maximum-hold rules before any performance
  runner exists.
- [ ] Split reusable locked history into development/calibration and genuinely
  untouched evaluation identities before reading strategy performance; the
  inspected BTC v1 window can never be labeled unseen.
- [ ] Build a one-shot evidence-locked V2 development runner only after the
  state machine, risk adapter, execution semantics and full regression are
  separately reviewed.
- [ ] Audit point-in-time equity fundamentals, corporate actions, historical
  universe membership, delistings, industry groups and executable costs before
  implementing CAN SLIM.
- [ ] Pre-register a faithful CAN SLIM replication or explicitly named partial
  derivative; never claim replication when required components are absent.
- [ ] Evaluate crypto and equity sleeves independently before AI ranking,
  strategy combination or portfolio allocation is studied.

External notification delivery and any real execution capability remain deferred. The completed twelve-hour, 24-hour and three-day gates are bounded infrastructure-endurance evidence, not ad hoc activation, unattended 24/7 production readiness, profitability evidence or live-money authorization. First candidate v1, all eight standalone default screening variants, all three Alpha Development v2 variants and the exact four Trend Pullback Volume v1 variants are closed rejected configurations. The non-performance Kraken BTC/ETH/XRP archive-only v2 daily dataset is locked and independently revalidated. Supervised replay v1 is paused after the single BTC episode bound by SHA-256 `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`; ETH and XRP remain unopened. The active boundary is Windows reproduction and review of the AI-driven v2 causal feature contract—not strategy performance, optimization, Candidate v2, PAPER or live execution.
