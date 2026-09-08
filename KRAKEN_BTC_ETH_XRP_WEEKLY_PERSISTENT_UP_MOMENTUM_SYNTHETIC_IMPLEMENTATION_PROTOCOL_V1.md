# Kraken BTC/ETH/XRP Weekly Persistent-UP Momentum Synthetic Implementation Protocol v1

## Status

`KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_SYNTHETIC_ENGINE_FROZEN_NO_REAL_DATA_OR_RUN`

Protocol ID:
`kraken-btc-eth-xrp-weekly-persistent-up-momentum-synthetic-implementation-v1`.

This milestone implements the already frozen hypothesis only against explicit
in-memory synthetic fixtures. It cannot open a path, archive, CSV, ZIP,
manifest, URL or market-data client. It does not run Development, evaluate real
performance, fit a model, select a Candidate or authorize execution.

## Bound parent and hypothesis

- parent commit:
  `f7ca20a77f203a4a732d79d5fda4812954a956b2`;
- hypothesis protocol:
  `kraken-btc-eth-xrp-weekly-persistent-up-momentum-hypothesis-v1`;
- source dataset identity remains
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- assets remain `BTC-USD`, `ETH-USD`, `XRP-USD` in that order; and
- Development remains `[2019-01-01T00:00:00Z, 2024-04-01T00:00:00Z)`.

The terminal Kraken 12h status and the closed daily discovery rounds are not
reopened. The synthetic engine creates no evidence about the real dataset.

## Synthetic-only call boundary

The engine accepts only a Python dictionary with exactly the three assets and
an explicit token:
`KRAKEN_WEEKLY_PERSISTENT_UP_SYNTHETIC_FIXTURE_V1`.

Each asset maps to an ordered nonempty list or tuple of dictionaries with exact
fields:
`timestamp, open, high, low, close, volume, trades`.

Timestamps must be canonical `YYYY-MM-DDT00:00:00Z`, strictly increasing,
unique and inside Development. OHLC must be finite, positive and geometrically
valid. Volume must be finite and nonnegative. Trades must be a positive
integer. Unknown/missing assets or fields, booleans, non-finite values,
duplicates and unordered rows fail closed.

The token is a scope assertion, not a claim that values are genuine. No future
real-data runner may reuse it as authorization. A future runner must own a
separate path-bound reader and separate operator decision.

## Complete-week implementation

The week is `[Monday 00:00:00Z, next Monday 00:00:00Z)`. The engine enumerates
every week between the earliest and latest supplied synthetic row. A valid
asset-week contains all seven expected UTC-midnight observations.

Aggregation is exact:

- Open: Monday Open;
- High: maximum daily High;
- Low: minimum daily Low;
- Close: Sunday Close;
- Volume: sum of seven daily volumes; and
- Trades: sum of seven positive integer trade counts.

An incomplete or empty enumerated week is recorded with its exact missing
timestamps and no OHLCVT output. Nothing is filled, interpolated or repaired.
The market week is complete only when all three asset-weeks are valid.

## Causal state implementation

Complete common weeks form consecutive segments. Any incomplete market week
ends the segment and resets market-state and asset-momentum lookbacks.

For each completed common week `t`:

1. each asset weekly return is `Close(t) / Close(t-1) - 1`;
2. the market weekly return is the arithmetic mean of the three asset returns;
3. the four-week market return compounds the four market weekly returns;
4. market state is `UP` at a return greater than or equal to zero, otherwise
   `DOWN`;
5. asset momentum is `Close(t) / Close(t-4) - 1`; and
6. persistence requires state `t-1 = UP` and state `t = UP`.

The first four weeks of a segment have insufficient current state. The fifth
week can exercise only the current-UP control because prior state is still
insufficient. A persistent-state rule therefore first becomes eligible on the
sixth consecutive complete common week.

## Rule implementation

The exact ordered rules are:

1. `PERSISTENT_UP_ASSET_MOMENTUM` — persistent `UP` and strictly positive
   asset momentum;
2. `CURRENT_UP_ONLY_ASSET_MOMENTUM_CONTROL` — current `UP` and strictly
   positive asset momentum; and
3. `PERSISTENT_UP_MARKET_ONLY_CONTROL` — persistent `UP` without the asset
   momentum requirement.

Every asset/week/rule produces either `LONG` or `HOLD_CASH` with a deterministic
reason. Zero market momentum is `UP`; zero asset momentum is not eligible.
Controls remain mechanism diagnostics and cannot become Candidates.

## Synthetic outcome implementation

A synthetic `LONG` decision uses only that asset's complete weeks:

- entry reference: Open of exact week `t+1`;
- exit reference: Open of exact week `t+2`;
- a missing entry or exit week yields
  `INVALID_MISSING_FUTURE_BOUNDARY`; and
- `HOLD_CASH` yields `NOT_APPLICABLE_HOLD_CASH`.

For each frozen baseline/stress profile, adverse price rate is
`slippage + full_spread / 2`. Entry fill is `open(t+1) * (1+a)` and exit fill is
`open(t+2) * (1-a)`. Entry cash is `entry_fill * (1+c)`, exit proceeds are
`exit_fill * (1-c)`, and net return is
`(exit_proceeds - entry_cash) / entry_cash`.

Decimal arithmetic uses deterministic 50-digit local precision. Public numeric
output is canonical non-exponential decimal text. Net return strictly greater
than zero is `NEXT_WEEK_NET_POSITIVE`; zero is nonpositive.

## Output and non-performance boundary

Output includes complete/invalid weeks, all causal decisions, rule actions,
synthetic outcomes and counts. It is deterministic for identical inputs and
does not mutate the supplied fixture. It does not apply Development viability
gates or write evidence; those belong to a separately designed future runner.

Every result records:

- input mode: `SYNTHETIC_TEST_ONLY`;
- synthetic pipeline executed: `true`;
- real source/archive values opened: `false`;
- real weekly aggregation/outcomes generated: `false`;
- Development run/model training: `false`; and
- Calibration, Evaluation, Candidate, PAPER, cloud and real orders: `false`.

## Next boundary

After Windows synthetic/static and full regression pass, the only possible next
stage is `SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_DESIGN_DECISION`. That decision
may design a reader but may not itself open the archive or run Development.
