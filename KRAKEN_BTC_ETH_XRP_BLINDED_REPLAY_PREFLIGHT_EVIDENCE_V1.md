# Kraken BTC/ETH/XRP Blinded Replay Preflight Evidence v1

## Status

`KRAKEN_BLINDED_REPLAY_PREFLIGHT_PASS`

This is compact non-performance evidence for the one reviewed sealed preflight
executed on Windows on 2026-08-28. It records no selected episode timestamp,
future endpoint, chart view, participant decision, strategy result or market
performance.

## Frozen identity and reproduced validation

- implementation commit integrated and pushed before preflight: `8ed84c9`;
- focused Windows regression: `82 passed`;
- complete Windows regression: `1201 passed`;
- protocol ID:
  `kraken-btc-eth-xrp-bounded-blinded-replay-review-v1`;
- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- source mode: `OFFICIAL_OHLCVT_ARCHIVES_ONLY`;
- network requests executed: `false`.

The preflight independently reopened the exact external dataset lock and
reproduced the following availability-only catalog:

| Asset | Observed rows | Missing | Continuous segment rows | Candidate episodes | Selected |
| --- | ---: | ---: | --- | ---: | ---: |
| BTC-USD | 2646 | 1 | 1916, 730 | 2470 | 1 |
| ETH-USD | 2647 | 0 | 2647 | 2559 | 1 |
| XRP-USD | 2645 | 2 | 1226, 1419 | 2469 | 1 |

## Sealed schedule evidence

- asset order: `BTC-USD`, `ETH-USD`, `XRP-USD`;
- episode count: `3`;
- episodes per asset: `1`;
- rows per episode: `89`;
- initial context bars: `30`;
- decisions per episode: `60`;
- selection schedule SHA-256:
  `3e805044356777f0bdfa2901db267d714c1e14d11415dd4686acaaaed92f1042`;
- selection uses OHLCV: `false`;
- selected timestamps exposed: `false`;
- selection schedule persisted: `false`.

The schedule hash is evidence that the same price-independent three-episode
selection can be reproduced later. It does not reveal the selected starts or
ends and cannot be used to inspect the chosen price paths before a separately
authorized supervised replay.

## Authorization state after preflight

- preflight executed: `true`;
- real replay review eligible: `true`;
- real replay authorized: `false`;
- real chart replay executed: `false`;
- crypto strategy implemented: `false`;
- performance evaluation executed: `false`;
- optimization authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- live execution authorized: `false`.

`real replay review eligible` means only that the locked data and sealed
selection boundary passed preflight. The next boundary is a separate review of
whether one supervised, evidence-chained three-episode reconstruction may be
authorized. No replay, strategy, optimization or performance claim follows
from this pass.
