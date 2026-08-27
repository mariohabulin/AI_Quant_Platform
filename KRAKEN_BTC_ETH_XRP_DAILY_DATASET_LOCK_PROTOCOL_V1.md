# Kraken BTC/ETH/XRP Daily Dataset Lock Protocol v1

## Status

`BUILDER_REVIEWED_ACQUISITION_NOT_EXECUTED`

Reviewed on `2026-08-27` against the exact provider-audit normalized SHA-256:

`fc71ff88e11b5984ebf5168fdbe09446554f720fc3ec0241eef0839ca90b3fca`

This milestone implements the fail-closed acquisition, byte-inventory and
immutable-lock builder required by the reviewed provider audit. It does not
download Kraken archives during integration, execute a real chart replay,
define a crypto strategy, calculate performance, optimize parameters or
authorize Candidate v2, PAPER, cloud or live trading.

## Frozen dataset identity

- dataset: `kraken-spot-btc-eth-xrp-native-1d-20190101-20260801-v1`;
- provider: `Kraken Spot`;
- assets, in exact order: `BTC-USD`, `ETH-USD`, `XRP-USD`;
- provider pairs: `XBT/USD`, `ETH/USD`, `XRP/USD`;
- archive stems: `XBTUSD`, `ETHUSD`, `XRPUSD`;
- interval: provider-native `1440` minutes;
- start: `2019-01-01T00:00:00Z`, inclusive;
- end: `2026-08-01T00:00:00Z`, exclusive;
- expected UTC daily grid: `2,769` possible buckets per asset;
- canonical columns: `Date, Open, High, Low, Close, Volume`;
- default state at an unavailable bucket: `NO_TRADE_UNAVAILABLE`.

The expected grid count is not an instruction to manufacture 2,769 rows. A
provider-native archive may omit an interval in which no trade occurred. Every
such absence remains an explicit missing timestamp and splits the continuous
replay segments.

## Official archive boundary

The builder accepts local bytes downloaded from Kraken's reviewed official
links:

- [complete OHLCVT archive](https://drive.google.com/file/d/1ptNqWYidLkhb2VAKuLCxmp2OXEfGO-AP/view?usp=sharing);
- [official quarterly OHLCVT updates](https://drive.google.com/drive/folders/15RSlNuW_h0kVM8or8McOGOMfHeBFvFGI?usp=sharing);
- [Kraken OHLCVT documentation](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data).

The public quarterly directory inspected on `2026-08-27` contained updates
from `Q1 2023` through `Q1 2026`; it did not contain `Q2 2026`. This observation
does not authorize a fabricated filename, mirror or unofficial replacement.
The builder starts with one complete archive and accepts reviewed quarterly
updates when they are necessary to create exact overlap with the recent REST
window.

Exactly one input must have role `COMPLETE`. Every additional ZIP must have
role `QUARTERLY_UPDATE`, an HTTPS source reference and a UTC retrieval time.
The command-line boundary accepts only the reviewed complete filename
`Kraken_OHLCVT.zip` or the explicit quarterly filename form
`Kraken_OHLCVT_Q[1-4]_YYYY.zip`. Any other filename requires a new provider
review rather than silent acceptance.

## Archive byte inventory

Before reading market rows, the builder:

1. hashes every ZIP byte with SHA-256;
2. records its filename, role, official source, retrieval time and byte size;
3. inventories every ZIP member, not only the selected pairs;
4. records every member name, compressed and uncompressed size, CRC32 and
   directory status;
5. rejects encrypted or duplicate member names;
6. requires exactly one `XBTUSD_1440.csv`, `ETHUSD_1440.csv` and
   `XRPUSD_1440.csv` member in every submitted archive;
7. ignores other pairs and intervals only after the full inventory exists.

The complete member inventory is written as canonical
`archive_inventory.json` and bound into the final manifest by SHA-256. Archive
ZIP bytes are not copied into the repository or canonical dataset directory;
their hashes and retrieval evidence remain in the manifest, while the original
downloads remain external acquisition inputs.

## Native CSV validation

Every selected archive row must contain exactly:

`Unix time, Open, High, Low, Close, Volume, Trades`

The builder requires:

- integer timestamps aligned to UTC midnight;
- finite positive OHLC values and valid price geometry;
- finite nonnegative base-asset volume;
- positive integer trade count;
- exact asset, pair and `1440`-minute member identity;
- values inside the frozen interval before canonical publication.

Rows from complete and quarterly archives are merged without precedence.
Numerically identical duplicates are counted as verified equal duplicates.
Any conflicting duplicate blocks the entire lock; a later archive cannot
silently overwrite an earlier provider observation.

## REST bridge and exact overlap

The builder makes one bounded public Kraken OHLC request per frozen asset using
the reviewed endpoint:

`GET https://api.kraken.com/0/public/OHLC`

Request parameters are the legacy pair, `interval=1440` and a `since` boundary
no older than the endpoint's most recent 720-day capacity. `assetVersion=1`
forces the documented display-pair response identity (`BTC/USD`, `ETH/USD` or
`XRP/USD`) so a swapped response cannot pass silently. The raw response bytes
are stored under `source_evidence/` and bound by SHA-256.

The endpoint's final row is always treated as the current uncommitted candle
and removed before any comparison. The remaining response must:

- contain no provider error;
- contain exactly one pair payload;
- satisfy the same OHLCV/trade-count validation as the archive;
- overlap the submitted archive inputs for every asset;
- match every overlapping completed bucket exactly, including trade count.

REST can append only completed rows after an exact same-venue overlap has been
proven. It cannot reconstruct the older history by itself. No overlap or one
mismatched completed value blocks final publication.

## Missing timestamps and availability segments

For each asset, the builder compares observed timestamps with the exact 2,769-
bucket UTC grid and records:

- first and last observed timestamp;
- observed row count;
- missing count and every missing timestamp;
- every continuous availability segment;
- archive contributions and equal-duplicate count;
- exact REST overlap start, end and row count.

The builder never inserts a missing timestamp into the canonical CSV. It does
not forward-fill prices, manufacture zero-volume rows or infer a price from a
different venue. The only permitted trading state at an absent timestamp is
`NO_TRADE_UNAVAILABLE`.

## Canonical files and atomic lock

Canonical assets use UTF-8, LF line endings, UTC ISO timestamps and
non-exponential exact decimal rendering. The dataset directory contains:

- three ordered canonical daily CSV files;
- `archive_inventory.json`;
- one raw REST response per asset under `source_evidence/`;
- canonical `manifest.json`;
- `manifest.sha256`.

Every file is written under a unique sibling staging directory. The final
dataset path is created only after archive identity, rows, duplicate equality,
REST response, overlap, gaps, canonical bytes and all hashes pass. Existing
final output is never overwritten. Any failure leaves no published dataset.

`KrakenDailyDatasetLock` independently revalidates the canonical manifest,
sidecar, provider-audit hash, inventory, asset files and raw REST evidence
before returning a locked dataset object.

## Manifest safety state

A successful data build may set only:

- data acquisition executed: `true`;
- network requests executed: `true`;
- byte-level historical bucket inventory completed: `true`;
- all-asset dataset locked: `true`.

Even after a successful lock, the manifest retains:

- real chart replay authorized: `false`;
- real chart replay executed: `false`;
- crypto strategy implemented: `false`;
- performance evaluation executed: `false`;
- optimization authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER review eligible: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- live execution authorized: `false`.

A data lock proves provenance and causal availability only. It is not evidence
of a trading edge.

## Reviewed execution sequence

1. Integrate and test this builder without network acquisition.
2. Run its no-argument declaration and confirm every execution flag is false.
3. Download the official complete archive outside the repository.
4. Execute the builder with the complete archive in a new output root.
5. If the byte-level archive has no exact REST overlap, add only the necessary
   official quarterly updates and rerun into a fresh output root.
6. Review every source hash, gap, segment, overlap and canonical file hash.
7. Independently re-lock the resulting manifest.
8. Commit only the reviewed compact manifest and sidecar if the repository
   evidence policy permits; never commit multi-gigabyte source archives.
9. Review real blinded replay as a separate next authorization boundary.

## Components

- `src/kraken_daily_dataset.py` — contract, archive inventory, row validation,
  REST bridge, atomic canonical publisher, independent lock and review CLI;
- `tests/test_kraken_daily_dataset.py` — synthetic deterministic regression for
  archive identity, rows, duplicates, REST causality, overlap, gaps, hashes,
  atomic publication and authorization state.

## Next boundary

After Windows integration, the next action is the bounded real acquisition.
Only a reviewed successful manifest can make real blinded-replay review
eligible. Strategy rules, execution costs and profitability remain later
milestones.
