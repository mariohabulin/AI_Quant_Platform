# BTC/ETH/XRP Provider and Historical Availability Audit v1

## Status

`REVIEWED_SOURCE_SELECTED_ACQUISITION_NOT_EXECUTED`

Reviewed on `2026-08-27`.

This audit selects the source boundary for the future BTC/ETH/XRP daily
research dataset. It reviews documentary historical availability, known XRP
trading interruptions, candle and volume semantics, archive/API limits and
current fee evidence. It does not download data, inventory archive bytes, lock
a dataset, execute the blinded replay, define a trading strategy, calculate
performance or authorize Candidate v2, PAPER, cloud or live execution.

## Decision

The primary three-asset research source is:

`Kraken Spot official OHLCVT archives`

All three normalized research assets will come from one USD spot venue:

| Research asset | Kraken display pair | Kraken legacy/archive identity |
|---|---|---|
| `BTC-USD` | `BTC/USD` | `XBT/USD`, archive stem `XBTUSD` |
| `ETH-USD` | `ETH/USD` | `ETH/USD`, archive stem `ETHUSD` |
| `XRP-USD` | `XRP/USD` | `XRP/USD`, archive stem `XRPUSD` |

The target research interval remains:

- start: `2019-01-01T00:00:00Z`, inclusive;
- end: `2026-08-01T00:00:00Z`, exclusive;
- native interval: `1440` minutes / one completed day;
- timestamp boundary: UTC midnight.

Kraken announced the `XRP/USD` spot pair on `2017-05-18`, before the target
research window. Its official OHLCVT download states that it provides CSV
history for every currency pair from the beginning of each market, including
native `1440`-minute files and quarterly updates.

This is a source-selection decision, not a claim that every requested daily
bucket has already been inspected. Exact archive members, file hashes, first
and last observed buckets, missing timestamps and overlap equality remain the
next byte-level acquisition gate.

## Why Coinbase is not the common primary source

The existing Coinbase Exchange BTC/ETH one-day manifest remains valid recorded
evidence and is not deleted or reinterpreted. It continues to provide an
independent cross-venue reference for BTC and ETH.

Coinbase is rejected only as the common primary provider for the new
three-asset dataset because its own official notice records that XRP trading:

- was fully suspended on `2021-01-19` at `10:00 PST`
  (`2021-01-19T18:00:00Z`);
- was relisted on `2023-07-13`.

That known multi-year venue interruption would split XRP into materially
different availability segments and remove a central market period from the
requested 2019–2026 reconstruction. Filling the suspension with another venue
would mix volume regimes, while filling it with zero or synthetic candles would
fabricate the exact capitulation-volume evidence being studied.

Coinbase therefore remains:

- an immutable BTC/ETH reference dataset;
- a possible independent cross-venue sensitivity source;
- prohibited from being merged row-by-row with Kraken volume;
- prohibited from replacing missing Kraken observations without a separate
  provider-change protocol.

## Why Kraken is selected

Kraken satisfies the documentary source requirements better than Coinbase for
this exact research question:

1. `BTC/USD`, `ETH/USD` and `XRP/USD` belong to one USD spot venue.
2. `XRP/USD` existed before the research start.
3. Kraken publishes official OHLCVT archive downloads from each market's
   beginning.
4. The archive includes native `1440`-minute OHLCVT files.
5. Kraken publishes quarterly incremental archives.
6. Missing archive candles have an explicit meaning: no trades occurred in
   that interval.
7. The REST OHLC endpoint can verify recent same-venue overlap, while its
   limitations are explicit and fail-closed.

The selection reduces, but does not eliminate, venue bias. Kraken daily price
and volume represent Kraken trading, not the entire global crypto market. The
future strategy must describe its edge as venue-observed unless independent
cross-venue evidence later justifies a broader claim.

## Historical acquisition contract

The next data milestone must use this exact hierarchy:

1. download the official complete Kraken OHLCVT archive;
2. download every required official quarterly update through the requested
   boundary;
3. record the exact source URL, retrieval time, byte size and SHA-256 of every
   downloaded archive before extraction;
4. inventory all archive members before choosing files;
5. extract only the reviewed `1440`-minute `XBTUSD`, `ETHUSD` and `XRPUSD`
   members;
6. normalize provider identities to `BTC-USD`, `ETH-USD` and `XRP-USD` only in
   canonical output while retaining the original pair identity in the
   manifest;
7. use Kraken REST OHLC only as a recent completed-bar bridge and same-venue
   overlap check;
8. require exact equality across every completed overlapping archive/REST
   bucket;
9. remove the REST endpoint's last, not-yet-committed candle;
10. write no final data or manifest if identity, schema, overlap, coverage or
    hash validation fails.

The Kraken REST OHLC endpoint returns at most `720` recent entries and cannot
retrieve older data regardless of `since`. It is therefore prohibited as the
sole full-history source.

No duplicate source receives silent precedence. If two official Kraken inputs
contain the same completed timestamp, their OHLCVT values must be identical.
Any difference is a provider revision or acquisition defect that blocks the
lock until explicitly reviewed.

## Exact availability inventory required next

For every asset, the acquisition manifest must record:

- provider display pair and legacy/archive pair;
- exact first observed archive timestamp;
- exact last observed completed timestamp before the exclusive end;
- expected UTC daily grid count;
- observed row count;
- every missing UTC timestamp;
- continuous availability segments;
- duplicate/revised timestamps and their resolution status;
- source archive filename and SHA-256 for every contributing row range;
- REST overlap start/end, row count and equality result;
- canonical output file SHA-256.

Documentary evidence establishes that the intended market existed and the
official archive route is available. Only byte inspection can establish exact
historical bucket availability. Accordingly:

- documentary availability audit completed: `true`;
- byte-level historical bucket inventory completed: `false`;
- all-asset dataset locked: `false`.

## Missing intervals and no-trade treatment

Kraken states that OHLCVT entries exist only for intervals in which trades
occurred. The project will preserve that meaning.

For every missing daily timestamp:

- do not synthesize a candle;
- do not forward-fill OHLC;
- do not insert a zero-volume candle;
- do not infer a venue outage merely from absence;
- record the timestamp explicitly;
- classify the research state as `NO_TRADE_UNAVAILABLE`;
- split blinded replay into separate continuous availability segments.

A missing candle cannot become a signal, entry, exit, price, volume observation
or hidden flat day.

Long gaps or suspicious clusters require a separate incident review using
Kraken status/event evidence where available. The absence of a published
provider incident is not proof that a row is valid, and the absence of a row is
not automatically proof of an outage.

## Candle and volume semantics

The selected data are native venue OHLCVT observations:

- `Open`: first traded price in the interval;
- `High`: highest traded price;
- `Low`: lowest traded price;
- `Close`: final traded price;
- `Volume`: total amount traded by all trades;
- `Trades`: count of individual trades.

The acquisition must verify that archive volume is expressed in the pair's base
asset units, consistent with Kraken trade-volume semantics:

- BTC volume in BTC;
- ETH volume in ETH;
- XRP volume in XRP.

The canonical research CSV retains `Date, Open, High, Low, Close, Volume`.
Trade count may be retained in raw or audit evidence but is not silently added
as a strategy feature.

The future relative-volume feature is always calculated separately for each
asset from its own lagged trailing Kraken history. Raw BTC, ETH and XRP volumes
are not comparable numbers and may not be ranked against one another. Raw
Kraken and Coinbase volumes may not be merged or treated as one venue.

## Liquidity, spread and execution-cost boundary

The provider chosen for historical research is not automatically the future
execution venue. Nevertheless, a strategy evaluated on venue-native candles
must use defensible venue and account-scale costs.

The public Kraken fee schedule reviewed on `2026-08-27` showed for Spot Crypto
Tier 1 (`$0+` trailing 30-day spot volume):

- maker: `0.40%`;
- taker: `0.80%`.

The previously recorded `0.38%` taker sensitivity corresponds to Kraken's
`$10K+` tier, not the zero-volume tier. Neither value is frozen here as the
future strategy cost profile.

Before any performance evaluation, a separate execution-cost decision must:

- recheck the then-current account fee tier;
- measure or defensibly estimate pair-specific bid/ask spread;
- include next-boundary slippage;
- stress gaps through stops;
- review minimum notional and precision;
- review rejected and partial fills;
- preserve fee, spread and slippage as separate components;
- test adverse costs rather than choose the most favorable tier after seeing
  performance.

Daily OHLCVT proves neither the quoted spread nor an executable fill at the
daily Open. These remain independent execution assumptions.

## Official sources reviewed

Only provider-owned primary sources control this audit:

### Coinbase

- [Coinbase will suspend trading in XRP on January 19](https://www.coinbase.com/blog/coinbase-will-suspend-trading-in-xrp-on-january-19)
- [Coinbase Exchange: Get product candles](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles)
- [Coinbase Exchange: Get product stats](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-stats)

Coinbase documents a maximum of `300` candles per request, possible incomplete
historical rates and no published buckets for intervals without ticks. Its
product statistics documentation identifies volume in base-currency units.

### Kraken

- [Kraken Introduces New Fiat Pairs for Ripple (XRP) Trading](https://blog.kraken.com/product/kraken-introduces-new-fiat-pairs-for-ripple-xrp)
- [Downloadable historical OHLCVT data](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data)
- [Kraken REST: Get OHLC Data](https://docs.kraken.com/api-reference/market-data/get-ohlc-data)
- [Kraken Fee Structures](https://www.kraken.com/features/fee-schedule)
- [Kraken Trades History FAQ](https://support.kraken.com/articles/360001184886-how-to-interpret-trades-history-fields)

Source pages may change after this review. The declaration records the review
date but does not freeze remote webpage bytes. Downloaded data archives and the
future canonical dataset require their own exact byte hashes.

## Relationship to the existing BTC/ETH manifest

The Coinbase BTC/ETH daily manifest with SHA-256
`77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691`
remains immutable prior evidence. It is not extended by appending Kraken XRP.

The future primary dataset reacquires all three assets from Kraken. This avoids
making BTC/ETH volume mean Coinbase activity while XRP volume means Kraken
activity inside one primary replay. Coinbase BTC/ETH may later support
pre-registered cross-venue diagnostics, but it cannot select thresholds or
replace unseen evidence.

## Next reviewed boundary

Implement a non-performance Kraken daily data acquisition and lock builder that
executes the archive, quarterly-update and REST-overlap contract above. The
builder must create staging output first and publish a final dataset only after
all three assets, every gap and every hash pass exact review.

Only after that immutable three-asset manifest exists may the real blinded
daily replay be reviewed for execution. Strategy rules and performance remain
later, separately authorized milestones.

## Authorization state

- provider audit completed: `true`
- documentary historical availability audit completed: `true`
- byte-level historical bucket inventory completed: `false`
- bounded data-acquisition review eligible: `true`
- data acquisition executed: `false`
- all-asset dataset locked: `false`
- real chart replay authorized: `false`
- crypto strategy implemented: `false`
- performance evaluation executed: `false`
- parameter optimization authorized: `false`
- automatic strategy selection authorized: `false`
- Candidate v2 authorized: `false`
- bounded forward PAPER review eligible: `false`
- bounded forward PAPER authorized: `false`
- cloud execution authorized: `false`
- live execution authorized: `false`
