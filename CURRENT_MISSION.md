# CURRENT MISSION

## Real-Time Market Data Adapter + Feed Health v1

**Status:** IMPLEMENTED / VALIDATION PENDING

### Objective

Open the first controlled external-market-data boundary without allowing provider schemas or unhealthy data to leak into Strategy, Risk, Paper Broker or PaperTradingSession.

### Selected first provider / scope

- provider contract: Alpaca Market Data websocket bars
- asset class: crypto
- controlled symbol: `BTC/USD`
- initial bar cadence: 1 minute
- rationale: Alpaca supports websocket market data across crypto and equities, while 24/7 crypto gives the cleanest first environment for validating continuous feed health without stock-session gaps

### Implemented

- `AlpacaCryptoBarAdapter` for provider-specific bar normalization
- provider-neutral output through the existing `MarketDataEvent` contract
- strict OHLCV and symbol validation
- stale and future-timestamp rejection
- duplicate and out-of-order rejection
- configurable missing-bar gap detection
- explicit `WAITING / HEALTHY / UNHEALTHY` feed-health state
- accepted cumulative history protected from consumer mutation
- deterministic unit tests with no network/API-key dependency

### Definition of Done

- adapter/feed-health tests pass
- full regression remains green
- malformed/unhealthy provider data cannot reach paper trading as a `MarketDataEvent`
- no provider-specific schema enters Strategy/Risk/Paper layers
- documentation records transport/runtime work that remains intentionally separate

### Next after validation

Build Operational Safety / Paper Runtime: authenticated websocket transport, reconnect/backoff, controlled runtime loop, graceful shutdown, exception isolation, heartbeat/structured logging and minimal durable checkpoint/restart recovery. Then perform the first controlled real-time paper run.
