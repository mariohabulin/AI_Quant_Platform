# Kraken BTC/ETH/XRP AI-Driven v2 Partition Protocol v1

## Status

`AI_DRIVEN_V2_PARTITION_PROTOCOL_REVIEWED_SYNTHETIC_TESTS_ONLY`

This protocol freezes a calendar-only development, calibration and evaluation
partition for the Kraken AI-driven v2 research path. It does not open the
external dataset, materialize a real partition, run features, state, risk or
execution, calculate performance, select parameters or authorize an order.

## Frozen identity

- protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`;
- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- assets, in fixed order: `BTC-USD`, `ETH-USD`, `XRP-USD`;
- source mode: `OFFICIAL_OHLCVT_ARCHIVES_ONLY`;
- research window: `2019-01-01T00:00:00Z` inclusive through
  `2026-04-01T00:00:00Z` exclusive;
- prior inspected BTC episode evidence SHA-256:
  `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`.

The protocol applies only to that immutable dataset identity and manifest. A
quarterly extension, repaired source, altered gap list or changed canonical
asset requires a new dataset ID, new manifest and a separately reviewed
partition protocol. Nothing may extend this identity in place.

## Frozen half-open partitions

| Partition | Inclusive start | Exclusive end | Calendar buckets | Role | Inspection class |
|---|---|---|---:|---|---|
| `DEVELOPMENT` | `2019-01-01T00:00:00Z` | `2024-04-01T00:00:00Z` | 1,917 | model development | development only |
| `CALIBRATION` | `2024-04-01T00:00:00Z` | `2025-04-01T00:00:00Z` | 365 | parameter selection and freeze | inspected, not unseen |
| `EVALUATION` | `2025-04-01T00:00:00Z` | `2026-04-01T00:00:00Z` | 365 | one-time final evaluation | sealed and untouched |

The windows are contiguous, non-overlapping and cover all 2,647 expected UTC
daily buckets in the locked research window. Boundary membership is determined
only by the timestamp and the half-open interval; no market value, label,
signal, fill or result may affect membership.

## Selection basis and prior inspection

The boundaries were frozen before any AI-driven v2 complete-data run or
performance result. They use whole UTC calendar years and satisfy three
identity-only requirements:

1. all known provider gaps remain in `DEVELOPMENT`;
2. the already inspected BTC supervised episode lies wholly in
   `CALIBRATION` and therefore can never be called unseen evidence;
3. the final complete 365-day calendar year remains a sealed one-time
   `EVALUATION` window.

The inspected BTC participant decisions ran from
`2024-05-08T00:00:00Z` through `2024-07-06T00:00:00Z`. They are process and
hypothesis-reconstruction context only. Their evidence SHA-256 is bound above.
The window is explicitly `INSPECTED_NOT_UNSEEN`; no later runner or report may
rename it out-of-sample, blinded or untouched.

The earlier provider/availability audit, archive inventory, dataset lock,
independent re-lock and price-independent sealed-preflight schedule are data
provenance or process evidence, not AI-driven v2 performance inspection. They
do not by themselves unseal the `EVALUATION` market observations.

## Exact availability reconciliation

Provider-native missing buckets remain absent and keep their existing
`NO_TRADE_UNAVAILABLE` meaning.

| Asset | Development observed | Calibration observed | Evaluation observed | Locked total |
|---|---:|---:|---:|---:|
| `BTC-USD` | 1,916 | 365 | 365 | 2,646 |
| `ETH-USD` | 1,917 | 365 | 365 | 2,647 |
| `XRP-USD` | 1,915 | 365 | 365 | 2,645 |

Exact known missing UTC buckets:

- `BTC-USD`: `2024-03-31T00:00:00Z`;
- `ETH-USD`: none;
- `XRP-USD`: `2022-05-11T00:00:00Z` and
  `2022-05-12T00:00:00Z`.

The development availability segments are therefore BTC `1916`, ETH `1917`
and XRP `1226, 689` observed rows. Calibration and evaluation each contain one
365-row segment for every asset. No gap may be filled, interpolated,
forward-filled, backfilled or represented by a manufactured zero-volume row.

## Isolation and causal reset rules

Every asset and partition starts independently flat with empty feature warmup,
empty signal state, no synthetic position, zero prior open risk and no pending
intent. No feature baseline, event anchor, state age, entry intent, position,
cash mutation or exit can cross a partition boundary.

Every recorded provider gap imposes the same reset. Feature calculation must
receive one continuous availability segment at a time. The first rows after a
partition boundary or gap remain unavailable until the frozen causal lookbacks
are populated entirely inside that segment. A runner may not borrow historical
bars from an earlier partition merely to avoid warmup.

Partition results, configuration or evidence cannot be pooled across assets in
a way that hides an asset-specific failure. Deterministic asset order does not
grant cross-asset state or future access.

## Sequential access policy

All real data access remains closed at this milestone:

- development data opened: `false`;
- calibration data opened by AI-driven v2: `false`;
- evaluation data opened by AI-driven v2: `false`;
- partitions materialized from the external dataset: `false`;
- performance evaluation executed: `false`.

The next eligible artifact is a separate, hash-bound development runner. It
may be reviewed to open only the `DEVELOPMENT` timestamps and must reject any
calibration/evaluation row before feature generation. This protocol alone does
not authorize that runner or data access.

After development is formally closed, a separate calibration protocol may
authorize the `CALIBRATION` window for pre-registered candidate selection and
final parameter freeze. Once opened it remains permanently inspected. It can
never supply a final unseen claim.

Only after code, parameters, costs, reporting rules and candidate identity are
frozen may a separate evaluation protocol authorize `EVALUATION`. Evaluation
is one sealed one-time test. Any unauthorized observation, diagnostic chart,
parameter change, manual selection, rerun chosen because of a result or use of
evaluation data in development invalidates untouched status and requires an
incident record. An operational interruption may be handled only by a
separately reviewed fail-closed recovery rule; this protocol grants no retry.

## Deterministic component boundary

`src/kraken_ai_driven_v2_partition.py` may:

- expose the exact frozen identity and half-open window metadata;
- derive expected UTC timestamp indexes from calendar identity and known gaps;
- validate one explicitly supplied asset/partition timestamp index;
- split that validated index at recorded provider gaps;
- return defensive index copies;
- emit a canonical partition-plan SHA-256.

It may not locate or read dataset files, OHLCV values, manifests from disk,
network resources or prior result artifacts. It may not calculate features,
signals, plans, fills, P&L, returns, rankings, thresholds or eligibility. The
reference constructor accepts no alternate windows, so changed boundaries
cannot retain the same protocol identity.

Synthetic timestamp tests do not open the locked dataset and do not count as
partition materialization. Exact input type, timezone, UTC-midnight alignment,
ordering, uniqueness, membership and gap identity fail closed.

## Non-authorization boundary

This milestone freezes partition governance only. It does not authorize:

- a complete-data runner or any external dataset access;
- performance evaluation or optimization;
- Candidate v2 designation;
- bounded forward PAPER operation;
- cloud deployment;
- live execution.

The next boundary is design, synthetic testing and hash-bound review of a
development-only runner. Calibration and the sealed one-time evaluation remain
closed behind later explicit protocols.
