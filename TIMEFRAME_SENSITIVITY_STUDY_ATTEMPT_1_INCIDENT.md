# Timeframe Sensitivity Study Attempt 1 — Profit-Factor Serialization Incident

## Incident record

- Date: `2026-08-23`
- Execution revision: `e07b93eb4e9ea991a9bd169a6a0ac9546ab70cd0`
- Study: `ema-20-50-btc-eth-timeframe-sensitivity-v1`
- Incident class: `TECHNICAL_SERIALIZATION_FAILURE`
- Final study evidence written: `false`
- Staging evidence written: `false`
- Candidate v1 reopened: `false`
- Candidate v2 authorized: `false`
- Optimization authorized: `false`
- Bounded forward PAPER authorized: `false`
- Live execution authorized: `false`

## Frozen input state

The execution used the committed and pushed one-hour and daily dataset locks:

- 1h manifest SHA-256:
  `b9ba8126ca0612402919dd7f0f0096db2b2ef2f0a7d0669b6848276e88bc8157`
- 1d manifest SHA-256:
  `77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691`
- frozen 6h reference-report SHA-256:
  `6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c`

The 1h lock contains 66,437 observed BTC rows with 19 explicit gaps and
66,438 observed ETH rows with 18 explicit gaps. Both assets have a maximum
five-bucket consecutive gap, remain inside the frozen schema-v2 limits and
contain no synthetic, interpolated, forward-filled or resampled candle.

## What happened

The runner loaded and revalidated every frozen input and executed the new 1h
and 1d exploratory validation profiles in memory. During compaction of one
daily baseline evaluation, canonical JSON serialization encountered:

```text
profit_factor=inf
```

The Performance Analyzer intentionally returns positive infinity when a window
has positive winning P/L and zero losing P/L. That is a legitimate defined
metric state, but RFC-compatible canonical JSON does not permit an unquoted
infinite number. The strict serializer therefore failed closed with
`Out of range float values are not JSON compliant: inf`.

The exception occurred before creation of either `study_v1` or
`.study_v1.staging`. Both directories, the final report and its checksum were
explicitly checked and absent. The CLI printed no aggregate classification,
comparison, ranking or promotion result. The exception revealed only that one
retained profit-factor field had the engine's defined positive-infinity state.

## Reviewed recovery boundary

Study evidence schema v3 encodes only a positive infinite value whose exact key
is `profit_factor` as the explicit string:

```text
POSITIVE_INFINITY_NO_LOSING_TRADES
```

Every compact evaluation also records the number of such encodings and the
exact sentinel. NaN, negative infinity and non-finite values in every other
field remain fatal before staging. This preserves the metric's meaning without
replacing it with zero, a finite cap or `null`, and without weakening the
canonical serializer globally.

Recovery may reproduce the same frozen study only after focused/full Windows
tests, reviewed commit and push. Strategy code, nominal EMA periods, assets,
datasets and hashes, calendar windows, random seed, cost profiles and report
selection policy must remain unchanged. No inspected value may be used to tune
the study. Candidate-v2, optimization, PAPER and live authorization remain
false.
