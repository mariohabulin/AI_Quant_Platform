# US Equity Point-in-Time Data Feasibility Attempt 1 Result

## Immutable identity

- execution commit: `6a185e6d0dd9a7e31513f951a234601cfb9b06fa`;
- protocol: `us-equity-point-in-time-data-feasibility-v1`;
- source-observation SHA-256:
  `2d70d8bee1f0a7840a184f627ae9341419ac8eb9a8716273f5713052c0ab9a72`;
- source-evidence SHA-256:
  `2ffa2430ff22f3fdf86f0bf7d7695ac634fe05586a8f4639702b2c9f3b6be539`;
- audit-report SHA-256:
  `8f2348138376438129f3db1a94d0321e6b10177cd486f5436c935a167de0d2cb`.

## Read-only source review

The authorized audit inspected only official documentation and public schemas:

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces),
  [EDGAR access](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data),
  [as-filed financial statements](https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets),
  [13F data sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets)
  and [reuse guidance](https://www.sec.gov/about/webmaster-frequently-asked-questions);
- [Nasdaq Symbol Directory definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs);
- [Sharadar Core US Equities Bundle](https://data.nasdaq.com/databases/SFA),
  [Core US Fundamentals](https://data.nasdaq.com/databases/SF1) and
  [Sharadar Equity Prices](https://data.nasdaq.com/databases/SEP).

SEC was the sole non-sample source with reviewed reuse permission. It proved
six of twelve capabilities: point-in-time filing availability, as-filed annual
and quarterly fundamentals, material-event and institutional-filing
availability timestamps, at least ten years of history and bulk export.

The SEC CIK is a permanent filer identity, not a complete security-level
identifier and corporate-action lineage across share classes. Public Nasdaq
symbol directories are periodically refreshed current-symbol metadata, not a
documented historical active-and-delisted master. The full Sharadar price
product is premium; its free role remains schema-only and cannot contribute to
the capability union.

## Exact gap

The zero-cost stack did not prove:

1. a stable security identifier across ticker changes;
2. an active-and-delisted security master;
3. active-and-delisted daily OHLCV;
4. corporate-action and ticker lineage;
5. point-in-time sector and industry classification; or
6. market-calendar and benchmark history.

Status:
`US_EQUITY_POINT_IN_TIME_NO_COST_SOURCE_GAP_RECORDED_NO_PURCHASE_AUTHORIZED`

Action: `HOLD_RESEARCH_OR_FIND_ANOTHER_NO_COST_SOURCE`

The audit cost was `0 USD`. It is a valid feasibility result, not an
implementation incident. A complete point-in-time US-equity learning dataset
is not authorized from these sources, and there is no automatic purchase.

No market values, labels or models were opened or generated. Calibration,
Evaluation, Candidate v2, portfolio construction, PAPER, cloud execution, real
orders and live execution remain closed.
