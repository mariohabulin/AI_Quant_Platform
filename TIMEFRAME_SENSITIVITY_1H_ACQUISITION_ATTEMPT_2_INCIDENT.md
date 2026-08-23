# Timeframe Sensitivity 1h Acquisition Attempt 2 Incident

## Classification

- Date: `2026-08-23`
- Recovery revision: `0b3e5bdd2eebb697ec557701fab6b8e86240f646`
- Incident class: `PERSISTENT_PROVIDER_NATIVE_CANDLE_GAPS`
- Strategy evaluation executed: `false`
- Candidate v1 reopened: `false`
- Candidate v2 authorized: `false`
- Optimization authorized: `false`
- Bounded forward PAPER authorized: `false`
- Live execution authorized: `false`

## Observed result

The second one-hour acquisition reran the complete primary BTC-USD request pass
and then made two exact-bucket recovery passes for all 19 missing intervals.
Coinbase still returned no in-range candle for any of those buckets. The builder
failed closed with:

```text
missing=19 extra=0 recovery=exhausted_2_passes
```

Its diagnostic samples were:

```text
2019-04-11T13:00:00Z
2019-06-20T15:00:00Z
2019-10-31T20:00:00Z
2020-01-30T17:00:00Z
2020-09-04T23:00:00Z
2020-10-20T20:00:00Z
2023-03-04T18:00:00Z
2023-03-04T19:00:00Z
2023-03-04T20:00:00Z
2025-10-25T16:00:00Z
```

No one-hour CSV, manifest or checksum was written and no exploratory evaluation
or study staging evidence was created.

## Independent exact-interval diagnostic

The first missing interval, `[2019-04-11T13:00:00Z,
2019-04-11T14:00:00Z)`, was checked without writing data through three official
Coinbase candle views:

| Source | Returned rows | Exact in-range rows |
| --- | ---: | ---: |
| Exchange native 1h | 1 | 0 |
| Exchange native 5m | 0 | 0 |
| Advanced Trade native 1h | 1 | 0 |

The single raw rows were outside the requested half-open interval. There was no
real lower-timeframe candle from which to derive the missing hour. This matches
Coinbase's warning that historical rates may be incomplete and no data is
published for intervals without ticks:

https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles

## Reviewed methodology amendment before evaluation

Because no strategy result has been produced, the exploratory one-hour dataset
boundary may be revised without rescuing or mutating candidate v1. Schema v2
uses only provider-observed native one-hour rows and records every absent UTC
bucket in a canonical manifest. The frozen limits are:

- at most 50 missing buckets per asset
- at most 24 consecutive missing buckets
- two exact-bucket recovery passes and at most 100 recovery requests
- no interpolation, forward-fill, resampling or synthetic candles
- atomic one-shot persistence only after both assets pass
- calendar-time 70/30 OOS and exact 720-day/180-day walk-forward boundaries

Within a valid calendar partition, a signal before a gap may execute only at the
next provider-observed candle Open. No order can execute on an absent interval.
The manifest and lock independently account for expected rows, observed rows,
every missing timestamp, maximum consecutive gap, recovery status, asset hashes
and complete OHLCV validity.

The amendment must pass focused/full Windows reproduction, commit and push
review before acquisition attempt 3. The already locked daily manifest and the
frozen six-hour candidate-v1 report remain unchanged.
