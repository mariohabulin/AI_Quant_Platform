# Kraken BTC/ETH/XRP AI-Driven V2 Derivatives Context Feasibility Protocol V1

## Purpose

Protocol ID: `kraken-btc-eth-xrp-ai-v2-derivatives-context-feasibility-v1`

Alpha Research Lab Attempt 1 permanently closed the native Kraken 12h spot-
OHLCV hypothesis with `HOLD_CASH`. Its result SHA-256 is
`d76bb013c2124672132868752a5bb350a782eb45ef7f062b78b5edcb6d3b3703`.
There is no seventh learner, threshold relaxation or hidden retry.

This component answers one smaller question before another model is designed:
does official public archive metadata show a sufficiently long common
Development history for materially new derivatives context?

## Frozen first information bundle

The audit inventories exactly these Binance USD-M public archive series for
`BTCUSDT`, `ETHUSDT` and `XRPUSDT`:

1. monthly funding-rate files;
2. daily futures metrics files containing open-interest context;
3. monthly native 12h mark-price files; and
4. monthly native 12h index-price files.

Mark and index prices are the two required legs for a later causal basis
feature. Liquidations, order-book depth, news, alternative assets and stock
data are not part of this first bundle.

The Kraken spot archive remains the future label and execution-price source.
The Binance archive is only a candidate explanatory context source. Venue
identity must remain explicit in every later feature and report.

## Metadata-only audit

The component lists official public object names and archive periods. It does
not download or parse market-value CSV rows. Therefore it does not inspect
funding values, open-interest values, prices, returns, labels or performance.

For every source and asset it records:

- first and last available archive period;
- observed and expected periods inside the common interval;
- missing and duplicate archive periods; and
- the common calendar interval shared by all twelve source/asset identities.

The Development upper boundary remains `2024-04-01T00:00:00Z`. The audit may
identify a later common start caused by derivatives launch or archive history.
That timestamp is only a candidate input for the next protocol; it does not
silently rewrite the existing Kraken partitions.

## Feasibility gates

`DATA_FEASIBLE` requires all of the following:

- all four series exist for all three assets;
- at least 730 common calendar days end no later than the frozen Development
  boundary;
- every source/asset identity covers at least 98% of its expected daily or
  monthly archive periods inside that common interval; and
- no duplicate archive period is reported.

These are source-feasibility gates, not claims that two years is automatically
enough to learn alpha. If they pass, the next stage must separately freeze a
causal feature schema, fold plan and economic falsification gates before any
values or labels are opened.

If any gate fails, the action is `EXTEND_OR_CHANGE_DATA_SOURCE`. The response
is not a shorter test, relaxed gate or return to the closed OHLCV search.

## Frozen boundary

- object metadata may be listed read-only and repeatedly;
- market values: unopened;
- labels and model fitting: prohibited;
- hyperparameter and threshold search: prohibited;
- Calibration and Evaluation: unopened;
- Candidate v2, PAPER, cloud and live execution: unauthorized;
- real orders: impossible from this component.

The only permitted outcomes are a reviewed source-feasibility result followed
by a separately pre-registered new-information hypothesis, or a documented
data-extension decision.
