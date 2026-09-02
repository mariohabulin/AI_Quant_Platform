# Kraken BTC/ETH/XRP AI-Driven V2 Derivatives Context Dataset Lock and Reader V1

## Frozen purpose

Protocol ID:
`kraken-btc-eth-xrp-ai-v2-derivatives-context-dataset-lock-reader-v1`

Parent commit: `af0af86`

The parent hypothesis froze nine causal derivatives-context features before any
market value was opened. This component implements the only permitted next
step: acquire the exact public Binance USD-M Development objects, verify their
official checksums, validate their schemas and timestamps, and create one
immutable external dataset lock that a later learning runner can read.

Implementation and static review open no source object. A real acquisition is
one-shot and requires the exact phrase
`EXECUTE_KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ONCE` after an
independent clean preflight.

## Exact source registry

The interval is `2021-12-01T00:00:00Z` through
`2024-04-01T00:00:00Z` exclusive. The registry contains exactly:

| Source | Cadence | Objects per asset | Assets | Total |
|---|---:|---:|---:|---:|
| Funding rate | monthly | 28 | 3 | 84 |
| Futures open-interest metrics | daily | 852 | 3 | 2,556 |
| Native 12h mark price | monthly | 28 | 3 | 84 |
| Native 12h index price | monthly | 28 | 3 | 84 |
| **Total** |  |  |  | **2,808** |

Assets map explicitly as BTC-USD/BTCUSDT, ETH-USD/ETHUSDT and
XRP-USD/XRPUSDT. Object keys are derived only from the source registry already
audited in the parent feasibility component. No REST fallback, alternate
venue, symbol substitution, daily/monthly mixture or later partition is
permitted.

Every ZIP must match its adjacent official `.CHECKSUM` object. The lock also
records the ZIP, checksum text, decompressed CSV member and normalized output
SHA-256 digests. A ZIP may contain exactly one safe CSV member with the expected
basename; encrypted members, path traversal, extra members and oversized
payloads fail closed.

## Frozen source schemas

Funding requires exactly `calc_time`, `funding_interval_hours` and
`last_funding_rate`. The normalized output retains `source_timestamp` and
`funding_rate`.

Futures metrics requires exactly `create_time`, `symbol`,
`sum_open_interest`, `sum_open_interest_value`,
`count_toptrader_long_short_ratio`, `sum_toptrader_long_short_ratio`,
`count_long_short_ratio` and `sum_taker_long_short_vol_ratio`. The symbol must
match the object identity. The normalized output retains `source_timestamp`
and positive `open_interest` from `sum_open_interest`.

Mark and index native 12h klines require the official twelve-field kline
schema. Headerless official files and the exact documented header are accepted.
Open timestamps must be unique, increasing, UTC-aligned 12h buckets inside the
object month; close timestamps must be later than their opens. Only
`open_timestamp`, `close_timestamp` and positive `close` are normalized.

All numeric values must be finite. No duplicate, ordering inversion, foreign
period row, interpolation, backfill, cross-asset fill or schema alias is
allowed. Raw decimal text is preserved in normalized CSV output.

## Immutable external lock

The one-shot acquisition writes to a staging directory and renames it only
after all 2,808 objects validate. A failure preserves staging and does not
produce a final lock. The final directory contains:

- verified raw ZIP and `.CHECKSUM` bytes;
- twelve normalized source/asset CSV files;
- one canonical `manifest.json`; and
- one matching `manifest.sha256` sidecar.

The manifest records object identity, byte sizes, four hashes, row counts and
first/last timestamps. The independent reader verifies the manifest sidecar,
every raw artifact and every normalized file before constructing the exact
funding, open-interest and mark/index frames required by the parent feature
engine. It never downloads missing data while reading a lock.

## Safety boundary

This implementation does not execute acquisition, open values, generate
labels or fit a model. A later authorized lock run may open only Development
source values and may not generate labels or train.

Calibration, Evaluation, threshold or hyperparameter search, automatic model
selection, Candidate v2, PAPER, cloud, real orders and live execution remain
unauthorized. After a successful independently reviewed lock, the only next
implementation is the already frozen four-variant Development learning runner.
