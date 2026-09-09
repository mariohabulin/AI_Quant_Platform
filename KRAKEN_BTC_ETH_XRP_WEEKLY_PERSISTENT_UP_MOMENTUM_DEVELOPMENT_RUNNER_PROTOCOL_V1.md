# Kraken BTC/ETH/XRP Weekly Persistent-UP Momentum Development Runner Protocol v1

## Status

`KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_RUNNER_DESIGN_FROZEN_NO_DATA_OR_RUN`

Protocol ID:
`kraken-btc-eth-xrp-weekly-persistent-up-momentum-development-runner-design-v1`.

This milestone designs one future hash-bound Development runner for the frozen
Weekly Persistent-UP Momentum V1 hypothesis. It does not implement a filesystem
reader or evidence writer, open an archive or market value, aggregate a real
week, generate a real outcome, evaluate performance, fit a model or execute
Development.

The immutable parent is Git commit
`615cc8544aeeddda7163b59a343f099c96d49789`. Kraken 12h remains terminal
`HOLD_CASH`; the closed daily discovery rounds remain closed.

## Exact source boundary

The future runner may accept exactly one external source archive:

| Field | Frozen value |
| --- | --- |
| Filename | `Kraken_OHLCVT.zip` |
| Bytes | `7885068519` |
| SHA-256 | `e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d` |

The archive is already represented by locked dataset ID
`kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2` and
manifest SHA-256
`8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`.
The Q1 2026 archive is not an input because Development ends before it begins.
No network source, REST bridge, alternate archive, canonical CSV fallback or
filename substitution is permitted.

The ZIP must contain exactly one member with each basename:

| Asset | Provider pair | Required member basename |
| --- | --- | --- |
| `BTC-USD` | `XBT/USD` | `XBTUSD_1440.csv` |
| `ETH-USD` | `ETH/USD` | `ETHUSD_1440.csv` |
| `XRP-USD` | `XRP/USD` | `XRPUSD_1440.csv` |

Duplicate archive names, duplicate required basenames, encrypted members,
changed archive bytes or an absent required member fail closed. The future
runner records each selected member's full decompressed SHA-256, sizes and
CRC32. The whole member is hashed, but non-Development market-value fields are
opaque and may not be parsed.

## Development-only reader contract

The only permitted value interval is
`[2019-01-01T00:00:00Z, 2024-04-01T00:00:00Z)`. Calibration and Evaluation
timestamps may be identified only to exclude their rows; their Open, High,
Low, Close, Volume and Trades values remain unopened.

Every source row must contain exactly:

`Unix time, Open, High, Low, Close, Volume, Trades`.

The timestamp must be a strictly increasing unique integer aligned to UTC
midnight. In Development, OHLC must be finite positive exact decimals with
valid geometry, Volume must be finite and nonnegative, and Trades must be a
positive integer. Numeric tokens pass to the weekly engine as decimal text;
binary floating-point conversion is prohibited.

The complete 1,917-day Development grid has this immutable identity:

| Asset | Observed rows | First | Last | Exact missing timestamps |
| --- | ---: | --- | --- | --- |
| `BTC-USD` | 1,916 | `2019-01-01T00:00:00Z` | `2024-03-30T00:00:00Z` | `2024-03-31T00:00:00Z` |
| `ETH-USD` | 1,917 | `2019-01-01T00:00:00Z` | `2024-03-31T00:00:00Z` | none |
| `XRP-USD` | 1,915 | `2019-01-01T00:00:00Z` | `2024-03-31T00:00:00Z` | `2022-05-11T00:00:00Z`; `2022-05-12T00:00:00Z` |

The runner must derive missing timestamps by full-grid subtraction and require
exact equality with this table. Counts alone are insufficient. No missing row
is inserted, filled, shifted or replaced.

## Adapter and parity boundary

The reader maps source fields without transformation:

| Source | Engine fixture field |
| --- | --- |
| UTC Unix time | canonical `timestamp` |
| `Open` | `open` |
| `High` | `high` |
| `Low` | `low` |
| `Close` | `close` |
| `Volume` | `volume` |
| `Trades` | `trades` |

The existing synthetic authorization token is never valid for real data. A
future implementation must add a separate, non-public trusted adapter reached
only after authorization, source hashing and Development partition checks.
Synthetic parity tests must prove that the trusted adapter preserves the exact
complete-week validation, gap reset, rule actions and Decimal cost arithmetic
already implemented at the parent commit. It may not change the hypothesis.

The real aggregation contract remains Monday-to-Monday UTC with exactly seven
daily observations. The leading partial week beginning `2018-12-31`, the XRP
week beginning `2022-05-09` and the BTC week beginning `2024-03-25` are invalid
and diagnostic. A gap resets all market-state and asset-momentum history.

## Frozen rule, slices and event identity

Exactly three ordered rules are evaluated:

1. `PERSISTENT_UP_ASSET_MOMENTUM` — the only promotable hypothesis;
2. `CURRENT_UP_ONLY_ASSET_MOMENTUM_CONTROL` — diagnostic only; and
3. `PERSISTENT_UP_MARKET_ONLY_CONTROL` — diagnostic only.

Decisions are attributed to a slice by `decision_week_start`, never by entry
or exit week. The five frozen slices are D1 `[2019-02-04, 2020-01-06)`, D2
`[2020-01-06, 2021-01-04)`, D3 `[2021-01-04, 2022-01-03)`, D4
`[2022-01-03, 2023-01-02)` and D5 `[2023-01-02, 2024-04-01)`, all at Monday
`00:00:00Z` boundaries.

One valid event is one eligible asset/decision-week/rule with the exact Open
of week `t+1` and Open of week `t+2` both available inside Development. An
eligible signal missing either future boundary is recorded as invalid and does
not enter return means or support gates. Adjacent one-week events are retained;
there is no ranking, top-k rule or portfolio-cap filter.

## Exact Development gate evaluation

For every asset and rule, overall and slice means are unweighted arithmetic
means of valid event net returns. Empty means are `null`, not zero. Positive
contribution concentration is the largest strictly positive baseline event
divided by the sum of all strictly positive baseline events for that asset and
primary rule; no positive event produces `null` and fails the positive-mean
gate independently.

An asset passes the primary hypothesis only when all are true:

- at least 30 valid primary events overall;
- at least four events in at least four of five slices;
- overall baseline mean net return is strictly positive;
- overall stress mean net return is nonnegative;
- baseline mean is nonnegative in at least four slices;
- stress mean is nonnegative in at least three slices; and
- largest-event positive-profit share is at most `0.40`.

Cross-asset Development interest requires at least two assets passing every
asset gate. In addition, on at least two assets the primary rule's overall
baseline mean must be strictly greater than each control's overall baseline
mean. The comparison uses each rule's own valid-event population; a missing
mean cannot win. Controls can never be selected or promoted.

Passing all gates yields only
`KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_INTEREST_REVIEW_REQUIRED`.
Failure yields
`KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_NO_VIABLE_HYPOTHESIS_HOLD_CASH` and
closes this exact hypothesis without threshold, cost, lookback, asset or
polarity rescue. Neither result authorizes Candidate v2.

## One-shot and immutable evidence design

The future exact authorization phrase is:

`EXECUTE_KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_ONCE`.

This design does not activate that phrase. A later implementation, Windows
reproduction, commit/push and read-only preflight must all pass before the
operator can separately authorize one execution.

The future evidence root must be external to both Git and the archive. Final
directory is `kraken_weekly_persistent_up_momentum_development_v1`; staging is
`.kraken_weekly_persistent_up_momentum_development_v1.staging`. Existing final
or staging evidence blocks execution. Failure preserves staging for incident
review and does not silently authorize a retry.

The exact final file set is four files:

- `kraken_weekly_persistent_up_momentum_development_report.json`;
- its `.sha256` sidecar;
- `kraken_weekly_persistent_up_momentum_decisions.json`; and
- its `.sha256` sidecar.

JSON is canonical UTF-8 with LF. Sidecars are binary-written ASCII with exactly
`<digest><two spaces><filename><LF>`. The report binds commit, all source
hashes, archive/member evidence, counts, gaps, frozen configuration, all gate
results, terminal action and negative safety flags. Decisions contain every
asset/week/rule action and every valid or invalid outcome required to
independently recompute summaries and gates. No model artifact exists.

A separately implemented evidence reader must require the exact file set,
rehash every byte, validate both sidecars and recompute all summaries and gates
from decisions. It may not open the source archive, unpickle anything, write a
file, change the result or authorize a next stage.

## Current authorization boundary

At this design milestone, all are false: filesystem/network reader
implementation, evidence writer/reader implementation, authorization phrase
activation, source/archive value access, real aggregation/outcomes, gate
execution, Development, model training, Calibration, Evaluation, Candidate v2,
PAPER, cloud, real orders and live execution.

The only next permissible stage is
`SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_IMPLEMENTATION_DECISION`. That stage
may implement and test the frozen design with synthetic fixtures but may not
open the Kraken archive or execute Development.
