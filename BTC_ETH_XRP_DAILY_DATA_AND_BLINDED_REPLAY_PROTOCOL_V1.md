# BTC/ETH/XRP Daily Data and Blinded Replay Protocol v1

## Status

`PROTOCOL_AND_REPLAY_COMPONENT_REVIEWED_PROVIDER_AUDIT_REQUIRED`

This milestone implements a causal, performance-free replay boundary and binds
the exact Selective Swing Trading Research Mandate v1 to the existing recorded
BTC/ETH one-day manifest. It does not acquire XRP history, merge providers,
run a real chart replay, define a trading strategy, calculate profitability,
select parameters or authorize Candidate v2, PAPER, cloud or live execution.

## Purpose

The first crypto research task is to reconstruct the user's manual observation
without hindsight: inspect roughly one month of completed daily candles, decide
whether to enter, skip, hold or exit, record the reason, and only then reveal
the next day. This boundary preserves that workflow as auditable evidence while
keeping hypothesis reconstruction separate from performance evidence.

Protocol identity:

- protocol: `btc-eth-xrp-daily-data-blinded-replay-v1`
- assets: `BTC-USD`, `ETH-USD`, `XRP-USD`
- decision resolution: provider-native completed `1d` bars
- timestamp boundary: UTC midnight
- initial and rolling visible context: 30 bars
- default portfolio state: cash
- evidence role: `INSPECTED_HYPOTHESIS_RECONSTRUCTION_ONLY`

## Existing BTC/ETH reference

The protocol references, but does not reinterpret, the previously recorded
Coinbase Exchange BTC/ETH one-day manifest:

`77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691`

That manifest covers `2019-01-01T00:00:00Z` inclusive through
`2026-08-01T00:00:00Z` exclusive with 2,769 native daily rows per asset. Its
contract, canonical bytes and SHA-256 sidecar are revalidated by this protocol.
The reference does not by itself create a complete BTC/ETH/XRP replay dataset.

## XRP and provider audit boundary

No XRP provider is frozen in this milestone. Selecting a convenient current
venue without reviewing its historical listing and availability could create
false volume comparisons or silently exclude important periods. Before the
three-asset dataset may be locked, a separately reviewed provider audit must
record for each asset and venue:

- product identity, quote currency and any symbol or contract migrations;
- first and last genuinely available daily buckets;
- maintenance, suspension, delisting and known unavailable intervals;
- candle timestamp and volume semantics;
- base-volume versus quote-volume meaning;
- API pagination, revision and retention behavior;
- executable liquidity, spread, commission and slippage assumptions;
- whether one provider can support all three assets without changing the
  intended price-volume meaning.

If more than one provider is required, every row remains provider/venue bound.
Raw volumes from different providers may not be compared as though they were a
single market. Relative volume must be calculated causally per asset from its
own lagged trailing history.

## Daily data contract

The future data lock must satisfy all of the following:

1. retain exact provider-native completed OHLCV candles;
2. use ordered `Open`, `High`, `Low`, `Close`, `Volume` values;
3. retain UTC-midnight timestamp alignment and one-day granularity;
4. reject duplicate, nonmonotonic, nonfinite and invalid-geometry rows;
5. never synthesize or forward-fill a missing candle;
6. list every missing/unavailable timestamp explicitly;
7. split replay at availability gaps rather than hiding them;
8. preserve original file hashes, canonical manifest and SHA-256 sidecar;
9. identify development-only and genuinely unseen chronological boundaries;
10. prohibit performance execution until provider, availability, liquidity and
    cost assumptions are reviewed.

An unavailable candle is not automatically a zero-volume candle. Treating it
as one would fabricate precisely the volume evidence this hypothesis studies.

## Blinded replay contract

`src/blinded_daily_replay.py` implements only the causal interaction boundary.
Synthetic fixtures are permitted for regression testing; real market replay
remains unauthorized until the complete data lock exists.

At every replay decision:

- the view contains only the trailing 30 bars ending at the current completed
  bar;
- future bars, remaining-bar counts and future end timestamps are absent;
- returned frames are defensive copies;
- a nonempty reason must be recorded before `advance()`;
- a flat state permits only `ENTER` or `SKIP`;
- a long state permits only `HOLD` or `EXIT`;
- one timestamp accepts exactly one immutable decision;
- each decision binds a canonical SHA-256 of the visible bars;
- the next bar cannot appear before the current decision exists.

Replay completion records decisions and safety flags only. It deliberately
does not generate profit, return, benchmark, drawdown, ranking or parameter-
selection fields. Later strategy and performance protocols must not relabel
these inspected annotations as unseen evidence.

## Components

- `src/daily_crypto_replay_protocol.py` validates the normalized mandate hash,
  exact BTC/ETH manifest and fail-closed authorization state.
- `src/blinded_daily_replay.py` validates continuous daily availability
  segments and implements the sequential decision state machine.
- `tests/test_daily_crypto_replay_protocol.py` protects hashes, data semantics,
  provider-audit requirements and authorization boundaries.
- `tests/test_blinded_daily_replay.py` protects causality, decision order,
  position transitions, defensive copies, gaps and the absence of performance.

## Next reviewed boundary

The next milestone is a BTC/ETH/XRP provider and historical-availability audit.
Only after that audit may a new immutable three-asset daily manifest and raw
dataset be acquired and locked. A small Crypto Capitulation-Volume Reversal v1
rule catalog comes after real blinded-replay methodology and data causality are
reviewed; it is not part of this package.

## Authorization state

- data acquisition executed: `false`
- all-asset dataset locked: `false`
- XRP provider audit completed: `false`
- real chart replay executed: `false`
- crypto strategy implemented: `false`
- performance evaluation executed: `false`
- parameter optimization authorized: `false`
- automatic strategy selection authorized: `false`
- Candidate v2 authorized: `false`
- bounded forward PAPER review eligible: `false`
- bounded forward PAPER authorized: `false`
- cloud execution authorized: `false`
- live execution authorized: `false`
