# CURRENT MISSION

## Operational Safety / Paper Runtime v1

**Status:** IMPLEMENTED / VALIDATION PENDING

### Objective

Provide the minimum fail-safe process boundary required before the first controlled real-time `BTC/USD` paper session.

### Implemented

- `PaperOperationalRuntime` controlled event loop
- heartbeat and explicit `STARTING / HEALTHY / DEGRADED / HALTED / STOPPING` runtime health
- unhealthy market-data isolation before `PaperTradingSession`
- bounded consecutive feed-failure halt policy
- fail-closed handling for unexpected strategy/risk/execution errors
- graceful shutdown that refuses new events after stop is requested
- atomic JSON checkpoint persistence
- restore of open paper position/account continuity
- restore of Risk Engine drawdown/period/kill-switch state
- restore of session/feed timestamp continuity to prevent replay after restart
- provider transport interface plus Alpaca authentication/subscription and bounded reconnect/backoff
- deterministic tests with injected websocket factory; no live credentials or network required

### Definition of Done

- operational-runtime tests pass
- full regression remains green
- unhealthy feed data cannot become a paper-trading decision
- unexpected processing faults halt safely
- a process restart can recover the minimum paper account/risk/session continuity state
- network transport remains replaceable and provider details do not leak into Strategy/Risk/Paper layers

### Next after validation

Perform a pre-flight configuration/credential check and then the first short, supervised real-time `BTC/USD` paper session. Review feed health, runtime health, audit events, fills, account state and checkpoint recovery before increasing duration or autonomy.
