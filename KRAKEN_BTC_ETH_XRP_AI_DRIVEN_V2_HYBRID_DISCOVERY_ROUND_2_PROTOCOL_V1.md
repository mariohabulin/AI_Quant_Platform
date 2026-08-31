# Kraken BTC/ETH/XRP AI-Driven v2 Hybrid Discovery Round 2 Protocol v1

## Status

`KRAKEN_AI_V2_HYBRID_DISCOVERY_ROUND_2_PRE_REGISTERED_COMPONENTS_REQUIRED`

Protocol ID:
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`.

Round ID: `kraken-ai-v2-hybrid-discovery-round-2`.

This protocol pre-registers three new hypotheses derived from immutable Round 1
offline feedback. It freezes their identities, causal economic mechanisms,
asset routes, indicator vocabulary, parameters, costs, Development slices and
absolute interest gates before any Round 2 signal, execution or runner
component exists.

This is registration, not execution. No dataset or external evidence is opened
by this milestone. Development, Calibration and Evaluation access remain false.

## Immutable predecessor and feedback boundary

Round 1 is closed as
`KRAKEN_AI_V2_ROUND_1_CLOSED_NO_ELIGIBLE_ROUTE_HOLD_CASH` against canonical
report SHA-256
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`.

Its 12 frozen asset-family routes remain immutable. Round 1 rerun authorization
is permanently false. Round 2 may cite the locked report as source feedback,
but it cannot change Round 1 eligibility, remove a failed route from history or
weaken a gate after observing performance.

The Round 1 evidence is descriptive rather than a leaderboard:

- BTC volatility breakout failed only the largest-trade concentration gate;
- ETH volatility breakout failed only the nonnegative-slice gate;
- capitulation recovery had positive baseline and stress expectancy on all
  three assets but insufficient or concentrated chronological evidence;
- BTC and ETH trend pullback had positive but insufficient and concentrated
  evidence;
- every range-reversion route produced zero closed trades; and
- XRP trend pullback and volatility breakout had negative expectancy under
  both frozen cost profiles.

These facts justify new mechanism-level questions. They do not prove that a
Round 2 route will work.

## Parsimonious Round 2 decision

Round 2 registers three hypotheses, although the parent budget permits as many
as six. A ceiling is not a target. Registering only evidence-grounded economic
questions reduces multiple-testing pressure and preserves `HOLD_CASH` as a
valid outcome.

| Order | Hypothesis | Family | Asset routes |
| ---: | --- | --- | --- |
| 1 | ATR-normalized capitulation recovery | `CAPITULATION_RECOVERY` | BTC, ETH, XRP |
| 2 | Breakout-retest continuation | `VOLATILITY_BREAKOUT` | BTC, ETH |
| 3 | Multi-bar MACD trend resumption | `TREND_PULLBACK_CONTINUATION` | BTC, ETH |

Round order has no performance or ranking meaning. Each asset-family route is
evaluated independently against unchanged absolute gates.

## Retired Round 1 routes

Round 2 does not register `RANGE_MEAN_REVERSION`. Its three Round 1 routes had
no executable closed-trade evidence. The frozen net-`3R` feasibility rule is
not lowered to manufacture entries.

XRP is excluded from the new trend and breakout hypotheses because both parent
routes had negative expectancy under baseline and stress costs. XRP remains in
the ATR-normalized capitulation hypothesis because its parent capitulation
route retained positive expectancy under both profiles, while still failing
the complete frozen gate set.

Retirement is not deletion. Every Round 1 result remains in cumulative lineage.

## Hypothesis 1 — ATR-normalized capitulation recovery

- hypothesis ID:
  `kraken-ai-v2-r2-atr-normalized-capitulation-recovery-v1`;
- parent hypothesis:
  `kraken-ai-v2-r1-capitulation-recovery-volatility-path-v1`;
- family: `CAPITULATION_RECOVERY`;
- regime: `DOWNTREND_CAPITULATION`;
- assets: BTC-USD, ETH-USD and XRP-USD; and
- indicators: return, relative volume, ATR and close location.

Round 1 used the same fixed percentage-shock thresholds for all three assets.
Round 2 asks a different transferable question: whether shock magnitude scaled
to each asset's prior ATR, followed by a two-bar stabilization, produces more
chronologically distributed recovery evidence.

The setup requires the close to be at least six prior ATR below the prior
40-bar high, one-bar price change at or below `-1.50` prior ATR, true range at
least `1.75` prior ATR, volume at least `1.50` its prior median and close
location no higher than `0.35`.

The setup may remain active for seven completed bars. At least two
stabilization bars are required before confirmation. Confirmation requires
close location at least `0.60`, a close above the prior two-bar high and volume
ratio at least `0.80`.

Entry is scheduled at the next available open and an upward gap may not exceed
`0.50` prior ATR. The stop is the setup low minus `0.25` prior ATR. The target
is net cost-adjusted fixed `3R`, maximum hold is 25 bars and a completed close
below the prior 10-close low schedules a next-open exit. Reference A's prior-
resistance-room gate remains prohibited.

## Hypothesis 2 — Breakout-retest continuation

- hypothesis ID:
  `kraken-ai-v2-r2-breakout-retest-continuation-v1`;
- parent hypothesis: `kraken-ai-v2-r1-volatility-breakout-v1`;
- family: `VOLATILITY_BREAKOUT`;
- regime: `VOLATILITY_EXPANSION`;
- assets: BTC-USD and ETH-USD; and
- indicators: prior Donchian channel, ATR, relative volume, close location and
  ADX.

The prior 55-bar channel, ATR-14 expansion threshold `1.10` against its prior
60-bar median, ADX-14 minimum `20`, breakout volume ratio `1.25` and breakout
close-location minimum `0.70` remain unchanged. This isolates a new entry
mechanism rather than hiding a parameter search.

A qualifying breakout becomes a setup, not an immediate entry. Within five
completed bars price must retest to within `0.25` ATR of the frozen breakout
level, close at or above that level and then confirm with a close above the
prior high and volume ratio at least `1.00`. Only that confirmation schedules
next-open entry.

The entry gap cap is `0.50` prior ATR. The stop is the retest low minus `0.25`
prior ATR, the target is net fixed `3R`, maximum hold is 60 bars and a completed
close below the prior 10-close low schedules a next-open exit. The Round 1
direct-breakout entry is not reused.

## Hypothesis 3 — Multi-bar MACD trend resumption

- hypothesis ID:
  `kraken-ai-v2-r2-trend-pullback-macd-resumption-v1`;
- parent hypothesis: `kraken-ai-v2-r1-trend-pullback-continuation-v1`;
- family: `TREND_PULLBACK_CONTINUATION`;
- regime: `UPTREND_PULLBACK`;
- assets: BTC-USD and ETH-USD; and
- indicators: EMA, ADX, MACD, relative volume and ATR.

Trend structure retains EMA-50 above EMA-200, positive EMA-50 slope across 20
bars and ADX-14 at least `20`. EMA-20 remains the pullback reference.

Instead of the immediate-next-bar Round 1 confirmation, the new state requires
a two-to-five-bar pullback. Its low must come within `0.50` ATR of EMA-20, its
close must remain above EMA-50 and volume ratio may not exceed `1.00`. MACD
histogram must become nonpositive during the pullback and then cross above zero
while price closes above the prior three-bar high with volume ratio at least
`1.00`.

The next-open gap cap remains `0.50` prior ATR. The stop is the pullback low
minus `0.25` prior ATR, target is net fixed `3R`, maximum hold is 40 bars and a
completed close below EMA-50 schedules a next-open exit.

## Unchanged costs, safety and Development gates

Round 2 reuses the exact Round 1 baseline and stress profiles without reducing
commission, slippage or spread. It also reuses all five fixed chronological
Development slices from `2019-01-01T00:00:00Z` through
`2024-04-01T00:00:00Z`.

The shared envelope remains USD `5,000` research notional, cash-only,
long-only, maximum `0.50%` planned risk per position, maximum `1.50%` total
planned open risk, no more than three concurrent positions and no more than
one-third notional per asset. Decisions use completed bars, entries use the
next open, stop-first ordering and entry-bar protection remain mandatory, and
synthetic terminal force-close remains prohibited.

Every route must still pass all Round 1 absolute interest gates:

- at least eight closed trades;
- trades in at least three fixed slices;
- at least three nonnegative slices;
- baseline expectancy at least `+0.10R` and stress expectancy at least `0.00R`;
- baseline profit factor at least `1.20` and stress at least `1.00`;
- baseline marked drawdown no greater than `12%` and stress no greater than
  `18%`;
- largest trade no more than `40%` of net route profit; and
- zero unresolved positions.

Round interest still requires at least two eligible assets and two eligible
routes. Multiple passing routes for one asset require a separate portfolio
review; no return ranking or automatic winner selection is permitted.

## Discovery budget accounting

Round 1 executed four hypotheses. Round 2 registers three, so cumulative use is
seven of the maximum twelve hypotheses under parent protocol v1. This is the
second of the maximum two rounds.

Five unused hypothesis slots do not authorize additional variants, a Round 3,
a retry or execution. Changing this protocol would require a new governance
decision rather than interpreting unused capacity as permission.

## Immutable configuration lock

`src/kraken_ai_driven_v2_hybrid_discovery_round_2.py` submits the three-member
manifest to the parent bounded validator and SHA-256 locks the complete detailed
configuration. It binds the exact Round 1 report hash, parent hypothesis IDs,
route dispositions, costs, slices, gates, safety envelope and cumulative budget.

Unknown or reordered assets, invalid family indicators, changed thresholds,
new authorization, gate weakening, deleted failure lineage or budget excess
fails closed. The component accepts no OHLCV, signal, return, position or
ranking input and imports no market-data or backtesting dependency.

## Current authorization state

- Round 1 closed: `true`;
- Round 1 rerun authorized: `false`;
- Round 2 manifest registered: `true`;
- Round 2 causal components implemented: `false`;
- Round 2 execution components implemented: `false`;
- Round 2 discovery runner implemented: `false`;
- dataset opened: `false`;
- Development data opened: `false`;
- Calibration data opened: `false`;
- Evaluation data opened: `false`;
- Development run authorized: `false`;
- parameter sweep authorized: `false`;
- automatic ranking authorized: `false`;
- runtime learning authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`; and
- live execution authorized: `false`.

## Next controlled boundary

The next stage is `IMPLEMENT_ROUND_2_CAUSAL_COMPONENTS_SYNTHETIC_ONLY`.

That milestone must implement the exact ATR-normalized capitulation,
breakout-retest and multi-bar MACD state machines with synthetic formula,
prefix-causality, gap-reset and next-open tests. It may not open Development,
Calibration or Evaluation. A Round 2 runner and any one-shot Development
authorization remain later, separately reviewed boundaries.
