# Kraken BTC/ETH/XRP AI-Driven v2 Hybrid Discovery Round 1 Protocol v1

## Status

`KRAKEN_AI_V2_HYBRID_DISCOVERY_ROUND_1_PRE_REGISTERED_COMPONENTS_REQUIRED`

Protocol ID:
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`.

Round ID: `kraken-ai-v2-hybrid-discovery-round-1`.

This protocol pre-registers four hypotheses, one from each permitted hybrid
strategy family. It freezes economic theses, asset/regime routes, indicators,
numeric parameters, costs, development slices and absolute interest gates
before any new strategy component or market-data view exists.

It is registration, not execution. At this milestone all regime, signal and
execution components implemented: `false`; development data opened: `false`;
evaluation data opened: `false`.

## Parent boundary

The parent protocol is
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`.
Its shared catalog, manifest budget, asset/regime routing, offline-only learning
and hard portfolio safety envelope remain unchanged.

Reference A remains closed as
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH` against report
SHA-256
`f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`.
Only the capitulation hypothesis cites that report as feedback lineage. It
does not reuse the Reference-A signal, execution or run identity and explicitly
does not reuse the prior-resistance-room gate.

## Round structure

Each hypothesis is initially registered for BTC-USD, ETH-USD and XRP-USD using
the canonical asset order. This does not force one universal winner. The unit
of later retention is one `ASSET_FAMILY_PAIR`: BTC trend may pass while ETH
trend fails, and the failed route remains `HOLD_CASH`.

All four mechanisms use only completed-bar evidence, exclude the current bar
from rolling baselines, schedule entry at the next available open and require a
net cost-adjusted minimum reward of `3R`. Provider gaps and partition boundaries
reset every feature, regime, signal, pending intent, position and risk context.

## Hypothesis 1 — Capitulation recovery volatility path

- hypothesis ID:
  `kraken-ai-v2-r1-capitulation-recovery-volatility-path-v1`;
- family: `CAPITULATION_RECOVERY`;
- regime: `DOWNTREND_CAPITULATION`;
- indicators: return, relative volume, ATR and close location;
- source feedback: immutable Reference-A report SHA-256; and
- signal/execution identities are new Round-1 identities.

An event requires a close at least `18%` below the prior 60-bar close maximum,
one-bar return at or below `-6%`, true range at least `1.50` prior ATR, volume at
least `1.50` prior median and close location no higher than `0.35`.

The setup remains eligible for five completed bars. Confirmation requires close
location at least `0.65`, positive return, volume ratio at least `0.80` and a
close above the prior bar high.

The following-open gap may not exceed `0.50` prior ATR. The stop is the setup
low minus `0.25` prior ATR. The target is a net cost-adjusted fixed `3R`; an
open path may last at most 20 bars and a completed close below the prior
10-close low schedules a next-open exit. The old causal prior-resistance room
gate is not reused. This is a structurally different exit path, not a loosened
rerun of the 13 Reference-A signals.

## Hypothesis 2 — Trend-pullback continuation

- hypothesis ID: `kraken-ai-v2-r1-trend-pullback-continuation-v1`;
- family: `TREND_PULLBACK_CONTINUATION`;
- regime: `UPTREND_PULLBACK`; and
- indicators: EMA, ADX, relative volume and ATR.

Trend structure uses EMA `50` above EMA `200`, positive EMA-50 slope across 20
bars and ADX-14 at least `20`. EMA `20` defines the pullback reference.

A pullback low must come within `0.25` ATR of EMA-20, its close must remain
above EMA-50 and volume ratio must be no greater than `0.90`. Confirmation
requires a close above the prior high and EMA-20 with volume ratio at least
`1.10`.

The next-open gap cap is `0.50` ATR. The stop is the pullback low minus `0.25`
prior ATR, the target is net `3R`, maximum hold is 40 bars and a completed close
below EMA-50 schedules the exit at the next open.

## Hypothesis 3 — Range mean reversion

- hypothesis ID: `kraken-ai-v2-r1-range-mean-reversion-v1`;
- family: `RANGE_MEAN_REVERSION`;
- regime: `RANGE_BOUND`; and
- indicators: RSI, Bollinger bands, stochastic and ATR.

The causal range uses a 20-bar, two-standard-deviation Bollinger band. Current
band width and ATR-14 may each be at most `1.10` times their prior 120-bar
median.

The setup closes below the lower band with RSI-14 no higher than `25` and
stochastic `%K` no higher than `20`. Confirmation closes back inside the band,
with rising RSI and a `%K` cross above `%D`.

The next-open gap cap is `0.50` ATR and the stop is the setup low minus `0.25`
prior ATR. The signal-time Bollinger midline is frozen as the causal target and
must provide at least net `3R`; otherwise the entry is rejected. Maximum hold is
15 bars. A later recalculated midline may not move the frozen target.

## Hypothesis 4 — Volatility breakout

- hypothesis ID: `kraken-ai-v2-r1-volatility-breakout-v1`;
- family: `VOLATILITY_BREAKOUT`;
- regime: `VOLATILITY_EXPANSION`; and
- indicators: prior Donchian channel, ATR, relative volume, close location and
  ADX.

The regime uses the prior 55-bar close high, ATR-14 at least `1.10` its prior
60-bar median and ADX-14 at least `20`. A signal closes above the prior channel
high with volume ratio at least `1.25` and close location at least `0.70`.

The next-open gap cap is `0.50` ATR. The stop is the higher of breakout-bar low
minus `0.25` ATR and entry minus `2` ATR. The target is net `3R`, maximum hold
is 60 bars and a completed close below the prior 10-close low schedules a
next-open exit.

## Shared safety envelope

Every future execution component must retain:

- USD `5,000` research notional, cash-only and long-only;
- maximum `0.50%` planned risk per position;
- maximum `1.50%` total planned open risk;
- maximum three concurrent positions;
- maximum one-third notional per asset;
- adverse cost-aware size and reward calculations;
- entry-bar protection and stop-first intrabar ordering; and
- no synthetic terminal force close.

Family-specific stops and exits do not alter those shared ceilings.

## Cost profiles

| Profile | Commission each side | Slippage each side | Full spread |
| --- | ---: | ---: | ---: |
| baseline | `0.80%` | `0.15%` | `0.30%` |
| stress | `0.80%` | `0.30%` | `0.60%` |

The official adverse taker commission assumption is not reduced in stress.
Only the separately declared research slippage and spread assumptions double.
Neither profile proves an operator account tier, liquidity, partial-fill or
venue-availability model.

## Five fixed development slices

| Slice | Start inclusive | End exclusive |
| --- | --- | --- |
| `D1` | `2019-01-01T00:00:00Z` | `2020-01-01T00:00:00Z` |
| `D2` | `2020-01-01T00:00:00Z` | `2021-01-01T00:00:00Z` |
| `D3` | `2021-01-01T00:00:00Z` | `2022-01-01T00:00:00Z` |
| `D4` | `2022-01-01T00:00:00Z` | `2023-01-01T00:00:00Z` |
| `D5` | `2023-01-01T00:00:00Z` | `2024-04-01T00:00:00Z` |

These are reporting and stability slices, not five optimization folds. Missing
provider days stay missing and split continuity inside the applicable slice.
The five fixed development slices cannot be moved after performance inspection.

## Asset-route development-interest gates

An asset-family route retains development interest only if all absolute gates
pass under their exact later implementation:

- at least eight closed trades;
- trades in at least three of the five slices;
- at least three nonnegative slices;
- baseline net expectancy at least `+0.10R`;
- stress net expectancy at least `0.00R`;
- baseline profit factor at least `1.20`;
- stress profit factor at least `1.00`;
- baseline maximum marked drawdown no greater than `12%`;
- stress maximum marked drawdown no greater than `18%`;
- the largest trade contributes no more than `40%` of net route profit; and
- unresolved position count equals zero.

These are retention gates, not Candidate v2 gates. A route with nonpositive net
profit makes the largest-trade-share gate fail closed rather than produce an
undefined favorable value.

## Round-level selection boundary

Round 1 retains portfolio-construction interest only if at least two distinct
assets and at least two asset-family routes pass every route gate. Cross-asset
portability is diagnostic, not a universal-strategy requirement.

If more than one family passes for the same asset, the runner cannot select the
largest return or declare a winner. Status becomes
`SEPARATE_PORTFOLIO_REVIEW_REQUIRED`. A separate pre-registered review must
resolve compatibility, overlap and allocation. Every failed or absent route is
`HOLD_CASH`.

## Immutable configuration lock

`src/kraken_ai_driven_v2_hybrid_discovery_round_1.py` submits the four-member
manifest to the parent bounded validator, then canonicalizes and SHA-256 locks
the complete detailed configuration. Unknown or reordered assets, catalog
violations, Reference-A identity reuse, changed thresholds, costs, slices,
gates or authorization flags fail closed.

No source OHLCV, feature frame, signal, order, return or ranking is accepted by
this component. It contains no Pandas or backtesting dependency.

## Current authorization state

- hypothesis manifest registered: `true`;
- regime components implemented: `false`;
- signal components implemented: `false`;
- execution components implemented: `false`;
- discovery runner implemented: `false`;
- dataset opened: `false`;
- development data opened: `false`;
- calibration data opened: `false`;
- evaluation data opened: `false`;
- development run authorized: `false`;
- performance evaluation executed: `false`;
- parameter sweep authorized: `false`;
- automatic ranking authorized: `false`;
- runtime learning authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`; and
- live execution authorized: `false`.

## Next controlled boundary

The next stage is `IMPLEMENT_ROUND_1_CAUSAL_COMPONENTS_SYNTHETIC_ONLY`.

That milestone must implement the exact regime measurements, signal states and
family-specific execution contracts with synthetic formula, prefix-causality,
gap-reset, next-open and safety tests. It may not open Development, Calibration
or Evaluation. A runner and any request for one-shot Development authorization
remain later, separately reviewed milestones.
