# Kraken BTC/ETH/XRP Weekly Persistent-UP Momentum Hypothesis Protocol v1

## Status

`KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_HYPOTHESIS_FROZEN_NO_DATA_OR_RUN`

Protocol ID:
`kraken-btc-eth-xrp-weekly-persistent-up-momentum-hypothesis-v1`.

This milestone freezes one literature-informed, falsifiable crypto signal
hypothesis. It does not open the Kraken archive, aggregate a real weekly bar,
generate an outcome, fit a model, run Development, select a Candidate, submit
an order or authorize PAPER, cloud or live execution.

## Decision and novelty boundary

The hypothesis is:

> An asset's positive four-week time-series momentum may retain positive
> next-week net return only when the equal-weight BTC/ETH/XRP market proxy has
> remained in an `UP` state for two consecutive completed weekly decisions.
> Every other state returns `HOLD_CASH`.

This is not another trend-pullback, breakout, capitulation or 12-hour model
variant. It changes all three of the following:

- source-native daily bars are aggregated into complete UTC weeks;
- the predictor is a transition between lagged market states rather than a
  static indicator threshold; and
- the outcome is fixed next-week net return rather than the closed 12-hour
  `3R/1R` barrier label.

Kraken daily Rule Discovery Rounds 1 and 2 remain closed with no eligible
route. The regime-gated 12-hour result remains terminal as
`KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_NO_VIABLE_HYPOTHESIS_STOP_KRAKEN_12H_RESEARCH`.
Neither boundary is reopened, reinterpreted or tuned by this protocol.

## External research boundary

The rationale is informed by, but does not claim to replicate:

- Liu and Tsyvinski, *Risks and Returns of Cryptocurrency*, Review of
  Financial Studies 34(6), DOI `10.1093/rfs/hhaa113`; and
- Hsieh, Huang and Liu, *State transitions and momentum effect in
  cryptocurrency market*, Finance Research Letters 86, DOI
  `10.1016/j.frl.2025.108356`.

The papers are hypothesis sources only. Their broader universes, portfolio
construction, costs and samples do not prove that this three-asset Kraken
derivative works. No paper data or reported return enters this protocol.

## Frozen source and partition identity

- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- source assets in exact order: `BTC-USD`, `ETH-USD`, `XRP-USD`;
- source resolution: native `1d` Kraken OHLCVT;
- research partition: Development only, from `2019-01-01T00:00:00Z`
  inclusive to `2024-04-01T00:00:00Z` exclusive; and
- Calibration and Evaluation remain unopened.

The existing archive and manifest may be opened only by a separately
implemented and separately authorized future runner. This declaration accepts
no path, frame, candle, price, volume, return or outcome input.

## Complete UTC-week contract

A weekly interval is exactly `[Monday 00:00:00Z, next Monday 00:00:00Z)`.
One asset week is valid only when it contains exactly seven consecutive native
daily observations at the expected UTC boundaries.

Future aggregation, if separately implemented, must use:

- Open: first observed daily Open;
- High: maximum observed daily High;
- Low: minimum observed daily Low;
- Close: last observed daily Close; and
- Volume and Trades: sums of the seven observed daily values.

No incomplete week is repaired, resampled, forward-filled or interpolated.
An asset gap invalidates that asset week. The market proxy additionally
requires the same valid completed week for all three assets. A gap resets the
four-week state and momentum histories; observations separated by a gap may
not be joined into one lookback.

## Causal state and eligibility

At the close of completed week `t`:

1. Compute each asset's weekly close-to-close return.
2. Compute the market weekly return as the equal-weight arithmetic mean of the
   three same-week asset returns.
3. Compound the four completed market weekly returns ending at `t`. State `t`
   is `UP` when that four-week return is at least zero and `DOWN` otherwise.
4. A persistent-up transition exists only when both state `t-1` and state `t`
   are `UP`.
5. Compound the asset's own four completed weekly returns ending at `t`.
6. The primary signal is eligible only when the persistent-up transition is
   true and the asset's four-week return is strictly positive.

All inputs end at the completed week. A same-week incomplete input, insufficient
four-week history or missing prior state returns `HOLD_CASH`. Ties at zero are
conservative: zero market return is `UP`, while zero asset momentum is not an
entry signal.

## Fixed next-week outcome

The future signal study schedules entry at the first valid source Open of week
`t+1` and exit at the first valid source Open of week `t+2`. Both boundaries
must belong to a continuous, complete provider path. Missing entry or exit
observations invalidate and count the event; they are never substituted.

The recorded outcome is the long-only round-trip return after the exact frozen
cost profile. The two classes are `NEXT_WEEK_NET_POSITIVE` and
`NEXT_WEEK_NET_NONPOSITIVE`; equality belongs to the nonpositive class.

For each cost profile, let `a = slippage + full_spread / 2` and `c` be the
commission rate. The future runner must compute `entry_fill = open(t+1) *
(1+a)`, `exit_fill = open(t+2) * (1-a)`, entry cash `entry_fill * (1+c)` and
exit proceeds `exit_fill * (1-c)`. Net return is `(exit proceeds - entry cash)
/ entry cash`. A valid eligible asset-week is one event. Consecutive eligible
weeks are permitted as adjacent, non-overlapping one-week events; no event may
be dropped by a ranking or portfolio-cap rule in this signal-feasibility study.

This is signal-feasibility evidence, not a deployable execution policy. It
contains no stop, position size, capital allocation, drawdown claim or `3R`
promotion. A positive result could authorize only a separate risk-and-execution
design that restores the portfolio risk and approximately `3R` entry-quality
requirements before any Candidate or PAPER decision.

## Primary rule and non-promotable controls

Exactly one primary hypothesis exists:

`PERSISTENT_UP_ASSET_MOMENTUM`.

Two diagnostic controls isolate the proposed mechanism but can never become a
Candidate:

- `CURRENT_UP_ONLY_ASSET_MOMENTUM_CONTROL` removes the required prior `UP`
  state: it requires state `t` to be `UP` and the asset's four-week momentum
  to be strictly positive; and
- `PERSISTENT_UP_MARKET_ONLY_CONTROL` removes the asset's own positive-momentum
  requirement: it requires only state `t-1 = UP` and state `t = UP`.

Both controls retain the primary rule's complete-week, timing, outcome and cost
boundaries. Their different eligibility sets are intentional mechanism
ablations, not alternate strategies.

There is no return ranking, top-k selection, alternative lookback, threshold
grid, asset exclusion or automatic winner. The controls may only show whether
state persistence and asset momentum add information to the exact primary
rule.

## Cost boundary

The primary rule and both controls must later be measured under the same two
pre-declared profiles:

| Profile | Commission each side | Slippage each side | Full spread |
| --- | ---: | ---: | ---: |
| `KRAKEN_BASELINE_ADVERSE` | `0.80%` | `0.15%` | `0.30%` |
| `KRAKEN_STRESS_ADVERSE` | `0.80%` | `0.30%` | `0.60%` |

The baseline is the preserved
`kraken-tier1-taker-adverse-20260829-v1` contract. This protocol does not lower
costs to rescue a signal. Any future update to actual account-tier fees is a
separate execution-feasibility audit, not a retroactive edit.

## Frozen Development evidence shape

The first four-week warm-up remains non-reporting. Later Development evidence
uses five fixed UTC slices:

| Slice | Start inclusive | End exclusive |
| --- | --- | --- |
| `D1` | `2019-02-04T00:00:00Z` | `2020-01-06T00:00:00Z` |
| `D2` | `2020-01-06T00:00:00Z` | `2021-01-04T00:00:00Z` |
| `D3` | `2021-01-04T00:00:00Z` | `2022-01-03T00:00:00Z` |
| `D4` | `2022-01-03T00:00:00Z` | `2023-01-02T00:00:00Z` |
| `D5` | `2023-01-02T00:00:00Z` | `2024-04-01T00:00:00Z` |

These are chronological stability slices, not fitting folds. V1 trains no
model. The complete primary rule must execute once if a later runner is
separately authorized.

An asset retains signal-development interest only if all gates pass:

- at least 30 valid primary events overall;
- at least four events in at least four of five slices;
- positive overall baseline mean net return;
- nonnegative overall stress mean net return;
- nonnegative baseline mean in at least four slices;
- nonnegative stress mean in at least three slices; and
- no single profitable event contributes more than 40% of positive aggregate
  baseline net return.

The study retains cross-asset interest only if at least two assets pass every
gate. The primary rule must also exceed both non-promotable controls in overall
baseline mean net return on at least two assets. Failure returns `HOLD_CASH`
and closes this exact hypothesis without threshold rescue.

## Authorization boundary

At this milestone:

- protocol declaration frozen: `true`;
- source/archive values opened: `false`;
- real weekly aggregation executed: `false`;
- outcomes generated: `false`;
- model training authorized or executed: `false`;
- Development run authorized or executed: `false`;
- parameter or threshold search authorized: `false`;
- automatic asset selection authorized: `false`;
- Calibration and Evaluation opened: `false`;
- Candidate v2 authorized: `false`;
- PAPER, cloud, real orders and live execution authorized: `false`.

The only next permissible stage is a synthetic-only implementation of the
complete-week validator, causal state transition and fixed next-week outcome
boundary. That stage requires separate operator authorization and may not open
the Kraken archive or produce performance.
