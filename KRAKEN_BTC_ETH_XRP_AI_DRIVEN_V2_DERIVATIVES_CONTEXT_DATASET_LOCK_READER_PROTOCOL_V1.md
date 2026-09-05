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

Implementation and static review open no source object. Attempts 1 and 2
consumed their authorizations and exposed two real source-schema conditions:
optional blank ratio cells and frozen paired `0E-8` open-interest sentinels.
Attempt 3 passed those corrections, then stopped on a transient DNS failure
after locking 695 complete object pairs. All three staging directories remain
incident evidence.

Recovery Attempt 4 used the exact phrase
`EXECUTE_KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_RECOVERY_ATTEMPT_4_ONCE`
after an independent clean preflight. It completed at commit `40b5943`, wrote
the final Attempt 4 lock atomically and consumed that authorization. The final
manifest SHA-256 is
`db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`.
Acquisition must not be repeated.

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

`create_time`, `symbol`, usable positive finite `sum_open_interest` and finite
`sum_open_interest_value` remain mandatory. Binance's official archives may
leave the four ancillary ratio columns blank. Each such cell is optional only
because none is retained by this frozen dataset or hypothesis. An exact blank
is recorded as missing; a finite decimal is validated; every other sentinel
fails closed. A blank is never converted to zero, filled, interpolated or used
to discard an otherwise valid open-interest observation.

A complete read-only forensic scan covered all 2,556 metrics objects and found
no fetch, ZIP, schema, symbol, chronology or period error. It found 735,323
positive open-interest rows and exactly 399 paired `0E-8` source sentinels at a
frozen list of 133 timestamps per asset. The canonical timestamp-list SHA-256
is `791ddfb1d1b584abbbd551bbcce77baef2de51b23f9c3f2668f4e6d6d41d5cbb`.
No negative, blank, non-finite or nonnumeric open-interest value exists.

Only an exact `0E-8` `sum_open_interest` paired with exact `0E-8`
`sum_open_interest_value` at that asset's frozen timestamp is a recognized
missing-value sentinel. Its raw row remains locked but it is omitted from the
normalized series and counted in the manifest. There must be exactly 133 such
rows per asset and 399 total. Any extra timestamp, alternative zero literal,
unpaired zero or other invalid required value fails closed. No zero is passed
to a logarithm, converted, filled, interpolated, backfilled or copied across
assets.

Mark and index native 12h klines require the official twelve-field kline
schema. Headerless official files and the exact documented header are accepted.
Open timestamps must be unique, increasing, UTC-aligned 12h buckets inside the
object month; close timestamps must be later than their opens. Only
`open_timestamp`, `close_timestamp` and positive `close` are normalized.

All retained numeric values and every present optional numeric value must be
finite. No duplicate, ordering inversion, foreign period row, interpolation,
backfill, cross-asset fill or schema alias is allowed. Raw decimal text is
preserved in normalized CSV output.

## Immutable external lock

The one-shot acquisition writes to a staging directory and renames it only
after all 2,808 objects validate. A failure preserves staging and does not
produce a final lock. The final directory contains:

- verified raw ZIP and `.CHECKSUM` bytes;
- twelve normalized source/asset CSV files;
- one canonical `manifest.json`; and
- one matching `manifest.sha256` sidecar.

Attempts 1, 2 and 3 staging are incident evidence. Recovery fingerprints every
file in all three directories before work and verifies the same inventories
again before publication. Attempt 4 requires Attempt 3 to match exactly 1,390
files, 7,317,431 bytes and inventory SHA-256
`8de82f8905358c79f3e0cb609f8b8ecd782e32e02497e9ef784e85b528aa63dd`.
Its file set must be the complete ZIP/checksum pairs for the contiguous first
695 objects in the frozen registry, with no partial or additional file.

Each of those 695 cached pairs is read only from Attempt 3 staging and must pass
the same official checksum, safe-member, schema, chronology, period and value
validation as a network object before it is copied to Attempt 4 staging. No
cached validation result is trusted. Objects 696 through 2,808 are downloaded
from their exact frozen public URLs. The manifest records the acquisition
origin of every object, all three prior inventories, 695 verified-resume
objects and 2,113 public-download objects.

Every public fetch has at most twelve attempts. Transient transport failures
use bounded exponential backoff of 1, 2, 4, 8, 16, 32 and then at most 60
seconds between later tries. The retry budget never changes the object registry
or any data rule. Exhaustion fails closed, leaves Attempt 4 staging for an
incident review and never publishes a final lock.

The manifest records object identity, byte sizes, four hashes, row counts and
first/last timestamps. The independent reader verifies the manifest sidecar,
every raw artifact and every normalized file before constructing the exact
funding, open-interest and mark/index frames required by the parent feature
engine. It never downloads missing data while reading a lock.

## Completed Attempt 4 and read-only reader recovery

Attempt 4 completed all 2,808 source objects and twelve normalized files in
728.63 minutes. It independently revalidated the 695 cached pairs, downloaded
the remaining 2,113 objects, recorded exactly 399 frozen zero sentinels and
preserved the three prior staging inventories. The final directory exists and
its staging directory does not, proving the atomic publication completed.

The first independent read-only review verified the manifest identity and
sidecar, the complete object registry, acquisition origins, prior-staging
inventories, all raw ZIP/checksum/source-schema evidence and all normalized
file hashes. Frame construction then failed because Pandas inferred one fixed
datetime layout from valid ISO-8601 strings containing mixed second and
fractional-second precision, including
`2021-12-01T16:00:00.001000Z`. This is a reader compatibility defect, not a
dataset, checksum, source-schema or strategy failure.

The bounded correction parses every normalized timestamp column with explicit
Pandas `format="ISO8601"`, `utc=True` and fail-closed errors. It applies to
funding and open-interest source timestamps and mark/index open and close
timestamps. It does not modify a raw object, normalized CSV, manifest, hash,
feature, label, model or economic gate. Mixed-precision and malformed-input
regression tests freeze both the accepted format and the rejection boundary.

That correction passed and the second read-only review reached the mark/index
alignment gate. A timestamp-only scan proved that each index series is an
exact subset of its mark series: BTC has 1,698 mark rows, 1,680 index/common
rows and 18 mark-only rows; ETH and XRP each have 1,700 mark rows, 1,698
index/common rows and two mark-only rows. There are zero index-only rows, zero
duplicates, monotonic order and zero close-time mismatches on common bars.

The frozen hypothesis requires mark and index from the exact same completed
12h bar and already declares an absent source invalid. The reader therefore
inner-aligns on exact open timestamps, requires identical close timestamps on
every common row and records per-asset source, common and unmatched counts.
It never fills, interpolates, shifts or approximately matches an unmatched
bar. Reindexing the paired frame onto Kraken decisions retains missing bars as
missing, so the existing 60-consecutive-context-bar rule remains unchanged.

## Safety boundary

Attempt 4 acquisition is complete and its authorization is consumed. The
read-only recovery implementation does not execute acquisition. Neither its
static review nor the next lock review may download an object, modify the
final lock, generate labels or fit a model. The next action is only to run the
ISO-8601 and exact-alignment corrected independent reader against the existing
final directory with the exact manifest SHA-256 above.

Calibration, Evaluation, threshold or hyperparameter search, automatic model
selection, Candidate v2, PAPER, cloud, real orders and live execution remain
unauthorized. Only after the existing lock passes independent read-only review
may the already frozen four-variant Development learning runner be considered.
