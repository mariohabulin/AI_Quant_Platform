# Kraken BTC/ETH/XRP Daily Dataset Lock Protocol v2

## Status

`ARCHIVE_ONLY_BUILDER_REVIEWED_LOCK_NOT_EXECUTED`

Reviewed on `2026-08-27` after the v1 acquisition path failed closed on exact
Kraken archive/REST OHLCVT equality. This protocol preserves that failure and
replaces the unpublished v1 dataset identity. It does not reinterpret, delete
or publish any v1 dataset.

The upstream provider-selection audit remains bound by normalized SHA-256:

`fc71ff88e11b5984ebf5168fdbe09446554f720fc3ec0241eef0839ca90b3fca`

## Why v2 exists

The v1 contract proposed an official-archive historical baseline followed by a
recent Kraken REST OHLC bridge through `2026-08-01` exclusive. A completed
482-row overlap audit for every asset found:

| Asset | OHLC exact | Full-row exact | Volume mismatches | Trade-count mismatches |
|---|---:|---:|---:|---:|
| `BTC-USD` | 482/482 | 156/482 | 326 | 299 |
| `ETH-USD` | 482/482 | 119/482 | 363 | 299 |
| `XRP-USD` | 482/482 | 94/482 | 388 | 299 |

OHLC equality proves pair and UTC-bucket alignment. It does not prove full
OHLCVT source equivalence. Volume and trade-count mismatches persisted across
the historical overlap rather than only at one boundary. The v1 builder
therefore correctly published nothing.

V2 does not introduce a tolerance, discard volume, discard trade count during
validation or give one provider representation precedence. Its controlling
source decision is:

`REST_STITCHING_PROHIBITED`

Kraken REST remains available to later forward operation under a separately
reviewed contract. It is not an input, overlap gate or fallback for this frozen
historical dataset.

## Frozen dataset identity

- dataset: `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- provider: `Kraken Spot`;
- source mode: `OFFICIAL_OHLCVT_ARCHIVES_ONLY`;
- assets, in exact order: `BTC-USD`, `ETH-USD`, `XRP-USD`;
- provider pairs: `XBT/USD`, `ETH/USD`, `XRP/USD`;
- archive stems: `XBTUSD`, `ETHUSD`, `XRPUSD`;
- interval: provider-native `1440` minutes;
- start: `2019-01-01T00:00:00Z`, inclusive;
- end: `2026-04-01T00:00:00Z`, exclusive;
- final included day: `2026-03-31T00:00:00Z`;
- expected UTC daily grid: `2,647` possible buckets per asset;
- canonical columns: `Date, Open, High, Low, Close, Volume`;
- unavailable bucket state: `NO_TRADE_UNAVAILABLE`.

The grid count never authorizes manufactured rows. Missing provider-native
days remain explicit and split continuous replay segments.

## Frozen source bytes

Production v2 accepts exactly these inputs, in this order:

| Filename | Role | Bytes | SHA-256 |
|---|---|---:|---|
| `Kraken_OHLCVT.zip` | `COMPLETE` | 7,885,068,519 | `e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d` |
| `Kraken_OHLCVT_Q1_2026.zip` | `QUARTERLY_UPDATE` | 545,431,093 | `95b2fec056bbacdfb5426e859a756d269bb19ba31eac7ea9e814759dfccd77b1` |

The complete archive contributes history through `2025-12-31`. The official
Q1 update was independently inspected before integration. For each exact
`XBTUSD_1440.csv`, `ETHUSD_1440.csv` and `XRPUSD_1440.csv` member it contains
90 rows from `2026-01-01T00:00:00Z` through `2026-03-31T00:00:00Z`, with zero
timestamp gaps, zero duplicates and zero seven-column schema failures.

Any different filename, order, role, byte size or SHA-256 blocks production
publication. A later Kraken replacement is a new reviewed source version, not
a silent update to v2.

## Archive inventory and row validation

Before selecting market rows, the builder hashes every ZIP byte and inventories
every member name, size, compressed size, CRC32, directory flag, encryption
flag and duplicate-name state. Every archive must contain exactly one native
daily member for each frozen asset.

Every selected row must contain exactly:

`Unix time, Open, High, Low, Close, Volume, Trades`

The builder requires UTC-midnight integer timestamps, finite positive OHLC,
valid price geometry, finite nonnegative base-asset volume and positive integer
trade count. Rows are filtered only after validation.

Official archive inputs merge without precedence. Equal duplicate timestamps
are counted as evidence. Any conflicting OHLCVT duplicate blocks the entire
lock. No source can overwrite another source.

## Missing timestamps and canonical output

For every asset the manifest records expected and observed counts, first and
last observations, every missing timestamp, continuous segments, archive
contributions and equal-duplicate counts. The builder never forward-fills,
synthesizes or inserts a zero-volume candle.

Canonical CSV files use UTF-8, LF, UTC ISO timestamps and exact
non-exponential decimal rendering. Trade count remains validated archive
evidence and is not silently promoted into the frozen strategy-feature schema.

## Atomic archive-only lock

The dataset directory contains only:

- three canonical daily CSV files;
- `archive_inventory.json`;
- canonical `manifest.json`;
- `manifest.sha256`.

No REST response or other network-derived market file exists in v2. The
manifest must state `network_requests_executed: false` and
`source_mode: OFFICIAL_OHLCVT_ARCHIVES_ONLY`.

All files are written under a unique staging directory and promoted only after
every validation and hash succeeds. Existing final output is never overwritten.
Any failure removes staging and publishes no dataset. An independent lock
revalidates the protocol hash, provider-audit hash, exact production source
evidence, archive inventory, canonical manifest and every asset hash.

## Safety state

A successful archive-only lock may establish data provenance only. It retains:

- real chart replay authorized: `false`;
- real chart replay executed: `false`;
- crypto strategy implemented: `false`;
- performance evaluation executed: `false`;
- optimization authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- live execution authorized: `false`.

## Reviewed execution sequence

1. Integrate v2 tests and builder without a network request.
2. Reproduce the focused and complete project test suites on Windows.
3. Run review mode and confirm every execution/authorization flag is false.
4. Execute one fresh output attempt with the two exact frozen archives.
5. Review archive hashes, members, contributions, gaps, segments and canonical
   hashes for all three assets.
6. Independently re-lock the final manifest.
7. Record only compact reviewed evidence in Git; never commit source ZIPs.
8. Review real blinded replay as a separate later authorization boundary.

No strategy rule, performance result, PAPER operation or live execution is
authorized by this protocol.
