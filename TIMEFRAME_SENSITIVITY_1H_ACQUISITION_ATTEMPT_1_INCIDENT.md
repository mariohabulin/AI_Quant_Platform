# Timeframe Sensitivity 1h Acquisition Attempt 1 Incident

## Classification

- Date: `2026-08-23`
- Study implementation revision: `c39fd7c`
- Incident class: `TECHNICAL_DATA_ACQUISITION_INCOMPLETENESS`
- Strategy evaluation executed: `false`
- Candidate v1 reopened: `false`
- Candidate v2 authorized: `false`
- Optimization authorized: `false`
- Bounded forward PAPER authorized: `false`
- Live execution authorized: `false`

## Observed result

The independently acquired native `1d` development dataset completed first.
Its canonical manifest contains 2,769 rows per asset and has SHA-256:

```text
77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691
```

The first native `1h` acquisition then stopped while validating the initial
`BTC-USD` provider response:

```text
Incomplete BTC-USD candle grid: missing=19 extra=0.
```

The builder failed before writing any one-hour asset CSV, manifest or checksum.
The one-hour output directory existed but was empty. No exploratory timeframe
evaluation ran, no final study or staging evidence existed and the frozen
six-hour reference report was not changed.

## Recovery boundary

Coinbase documents that historical candle responses can be incomplete and that
intervals with no ticks may have no published candle. This incident is therefore
treated as a data-acquisition completeness failure, not strategy evidence.

The reviewed recovery may only re-request provider data for exact missing UTC
buckets after the normal chunked pass. It is bounded to:

- at most two missing-candle recovery passes
- at most 100 exact-bucket recovery requests per asset
- the existing finite transport retry budget on every request
- the existing duplicate-conflict, exact-grid and OHLCV validation

Recovery must never interpolate, forward-fill, resample or synthesize an OHLCV
bar. Only a complete provider-returned candle is accepted. If any gap persists,
the builder fails closed again, reports exact missing timestamp samples and
writes no dataset artifacts.

The recovery implementation and tests must be reproduced on Windows, reviewed,
committed and pushed before the one-hour acquisition is retried. The completed
daily manifest remains separate untracked dataset-lock evidence until the
one-hour acquisition also passes.
