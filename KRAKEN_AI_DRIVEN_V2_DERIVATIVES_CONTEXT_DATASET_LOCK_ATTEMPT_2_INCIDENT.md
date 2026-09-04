# Kraken AI-Driven V2 Derivatives Context Dataset Lock Attempt 2 Incident

## Scope

Dataset Lock Recovery Attempt 2 was the single authorized Development-only
acquisition run executed from commit `8181d05`. It was authorized only to
download, checksum, validate, normalize and atomically lock the frozen 2,808
public Binance USD-M context objects. It did not authorize label generation,
model training, Calibration, Evaluation, Candidate v2, PAPER or orders.

## Recorded execution result

- run exit code: `1`;
- elapsed time: `5.68` minutes;
- last emitted progress marker:
  `175/2808|OPEN_INTEREST_METRICS|BTC-USD|2022-03-01`;
- exception: `Open-interest metrics value must be a positive decimal`;
- final Attempt 2 dataset: absent;
- Attempt 2 staging: present and preserved;
- Attempt 1 staging: present and preserved with 226 files;
- repository content after failure: unchanged.

The authorization for Attempt 2 is consumed. Neither Attempt 1 nor Attempt 2
may be rerun, renamed, deleted or reused as a final dataset.

## Root cause

The first rejected source object was registry object 181,
`BTCUSDT-metrics-2022-03-07.zip`. Its first affected row was
`2022-03-07T15:30:00Z`. Binance recorded the exact literal `0E-8` in both
`sum_open_interest` and `sum_open_interest_value`. The current reader correctly
prohibited zero open interest because the frozen feature engine takes its
logarithm, but the acquisition contract did not yet distinguish a verified
source missing-value sentinel from a usable positive observation.

This is a source-value contract gap. It is not a model result, strategy result
or reason to weaken any economic gate.

## Complete public-source forensic scan

A separate read-only scan opened all 2,556 frozen daily metrics ZIP objects
across BTCUSDT, ETHUSDT and XRPUSDT. It did not write a lock or reuse either
staging directory.

- objects scanned: `2556/2556`;
- fetch, ZIP, member, schema, symbol, chronology or period errors: `0`;
- positive `sum_open_interest` rows: `735323`;
- exact-zero `sum_open_interest` rows: `399`;
- negative, blank, non-finite or nonnumeric `sum_open_interest` rows: `0`;
- affected objects: `24`;
- affected timestamps per asset: `133`;
- all three timestamp lists identical: `true`;
- canonical per-asset timestamp-list SHA-256:
  `791ddfb1d1b584abbbd551bbcce77baef2de51b23f9c3f2668f4e6d6d41d5cbb`;
- zero open-interest literal: exactly `0E-8` in all 399 rows;
- paired `sum_open_interest_value`: exactly `0E-8` in all 399 rows.

The affected common dates are 2022-03-07, 2022-03-08, 2023-06-06,
2023-08-09, 2023-11-11, 2023-11-20, 2023-11-23 and 2023-11-26. Three other
objects contain 32 finite zero `sum_open_interest_value` cells while
`sum_open_interest` remains positive; that non-retained notional field was
already required to be finite, not positive. Four finite zero cells also occur
in the unused optional taker-ratio column. Neither case changes the retained
open-interest series.

## Frozen correction for a possible Attempt 3

The raw official ZIP and checksum remain preserved. A zero open-interest row
may be classified as missing only when all of these conditions hold:

1. the timestamp belongs to the frozen 133-timestamp allowlist for that asset;
2. both open-interest fields use the exact literal `0E-8`;
3. the aggregate is exactly 133 omitted rows per asset and 399 total;
4. the row is excluded from normalized open interest without zero conversion,
   interpolation, forward fill, backfill or cross-asset fill.

Any additional timestamp, different literal, unpaired value, negative,
non-finite, blank or nonnumeric required field fails closed. The existing
30-minute causal age gate then makes affected context absent or stale, and the
learning runner must discard context-incomplete rows.

Attempt 3 must use a new root, fingerprint and preserve both prior staging
directories, record both incident hashes and receive a new explicit one-shot
operator authorization. This incident record itself does not authorize it.
