# Kraken BTC/ETH/XRP AI-Driven v2 Strategy Discovery and Learning Protocol v1

## Status

`KRAKEN_AI_V2_HYBRID_DISCOVERY_PROTOCOL_FROZEN_NO_RUN_AUTHORIZATION`

Protocol ID:
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`.

This protocol freezes the architecture for bounded strategy discovery after
Reference A closed without an executable trade. Its exact model is **shared catalog, asset/regime-specific routing**
with a common portfolio safety envelope for BTC, ETH and XRP. It does not
register a new hypothesis, open market data, execute a backtest or authorize
Candidate v2.

## Decision

The selected architecture is hybrid:

- all assets draw from one economically named strategy-family catalog;
- every hypothesis explicitly names the assets and regimes to which it applies;
- BTC, ETH and XRP are not forced to use the same signal or execution contract;
- all active routes share the same hard portfolio-risk and adverse-cost safety
  envelope; and
- an asset without an eligible route remains `HOLD_CASH`.

The system therefore seeks transferable mechanisms without assuming that all
three markets behave identically. “Supports BTC, ETH and XRP” means each asset
is evaluated under the same governance and may receive a separately validated
route. It does not mean that every asset must trade or that one universal rule
must be forced onto all three.

## Immutable predecessor boundary

Reference A remains closed as
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH` against
canonical report SHA-256
`f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`.

Its exact signal contract `kraken-ai-v2-ccvr-reference-a-v1`, execution policy
`kraken-ai-v2-risk-execution-reference-a-v1` and development run identity may
not be reused. The 13 inspected confirmations may inform a new economic thesis,
but the prior-resistance `3R` gate may not simply be lowered to manufacture
entries.

The broader capitulation-recovery family remains researchable only through a
new signal identity, a structurally justified causal exit/target mechanism and
a new execution contract. Reference A itself is immutable evidence, not an
active catalog member.

## Frozen data and partition identity

- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- partition protocol:
  `kraken-btc-eth-xrp-ai-driven-v2-partition-v1`; and
- permitted research partition for a later discovery runner: `DEVELOPMENT`.

This architecture review opens none of those values. Calibration remains
inspected context containing the prior BTC episode, and evaluation remains a
sealed one-time boundary.

## Regime catalog

Regimes are causal routing labels, not hindsight performance buckets. A future
component must calculate each label from completed bars only and must freeze
the exact thresholds before a development run.

| Regime ID | Economic meaning | Fallback |
| --- | --- | --- |
| `DOWNTREND_CAPITULATION` | decline with volatility and volume shock | `HOLD_CASH` |
| `UPTREND_PULLBACK` | positive trend with a causal retracement | `HOLD_CASH` |
| `RANGE_BOUND` | bounded distribution without directional trend | `HOLD_CASH` |
| `VOLATILITY_EXPANSION` | causal range break with expanding volatility | `HOLD_CASH` |
| `UNCLASSIFIED` | insufficient or conflicting causal evidence | `HOLD_CASH` |

`UNCLASSIFIED` is never an invitation to guess. It routes directly to cash.

## Strategy-family catalog

| Family | Eligible regime | Permitted indicator primitives | Mechanism |
| --- | --- | --- | --- |
| `CAPITULATION_RECOVERY` | `DOWNTREND_CAPITULATION` | return, relative volume, ATR, close location | exhaustion, stabilization and recovery |
| `TREND_PULLBACK_CONTINUATION` | `UPTREND_PULLBACK` | EMA, ADX, MACD, relative volume, ATR | continuation after a causal pullback |
| `RANGE_MEAN_REVERSION` | `RANGE_BOUND` | RSI, Bollinger bands, stochastic, ATR, relative volume | reversal from a causal range extreme |
| `VOLATILITY_BREAKOUT` | `VOLATILITY_EXPANSION` | Donchian channel, ATR, relative volume, close location, ADX | confirmed channel break with expansion |

This table is an allowed vocabulary, not four implemented strategies and not a
performance ranking. Every executable hypothesis still requires separately
reviewed causal regime, signal, execution and development-gate contracts.

An indicator outside its family list fails manifest validation. Each hypothesis
must use between two and five named primitives, preventing both a one-number
placeholder and an unbounded indicator soup.

## Bounded discovery budget

One round may contain at most six hypotheses. No family may contribute more
than two variants and no asset may receive more than four routes in one round.
This protocol permits at most two separately authorized rounds and twelve
executed hypotheses in total.

These are hard ceilings, not targets. A round may contain fewer hypotheses and
an asset may have no active route. A Cartesian parameter grid, generated
leaderboard or repeated retry until something passes is prohibited.

Round order has no ranking meaning. When more than one route later satisfies
its frozen gates, a separate portfolio-construction decision is required; the
discovery runner may not silently choose the largest return.

## Hypothesis manifest contract

Before code or development values are opened, every round must create one
canonical manifest containing:

- stable round, hypothesis, signal, execution and development-gate IDs;
- one named family from the catalog;
- an ordered nonempty subset of BTC, ETH and XRP;
- only regimes eligible for that family;
- two to five family-permitted indicator primitives;
- a falsifiable economic thesis of sufficient detail;
- optional parent hypothesis lineage and at most three source-evidence hashes;
- explicit `DEVELOPMENT` partition identity; and
- every data-access, ranking, mutation, Candidate and execution authorization
  set to `false`.

`validate_hypothesis_manifest` rejects unknown fields, unknown assets, changed
asset order, duplicate IDs, Reference-A identity reuse, invalid SHA-256 lineage,
budget excess and any true authorization flag. It returns canonical immutable
content plus a SHA-256 fingerprint. Validation itself opens no data and grants
no run authority.

## Shared portfolio safety envelope

Every future family-specific execution contract must preserve at least:

- USD 5,000 research notional and cash-only long positions;
- maximum `0.50%` planned risk per position;
- maximum `1.50%` total planned open risk;
- no more than three concurrent positions;
- maximum one-third notional per asset;
- completed-bar decisions and next-open entry;
- entry-bar protection and stop-first intrabar ordering;
- adverse cost profile `kraken-tier1-taker-adverse-20260829-v1`; and
- no synthetic terminal force close.

This common envelope is not the full Reference-A execution policy. Each family
must pre-register its own causal stop, target/exit, gap and maximum-hold
semantics. The closed prior-resistance target is not inherited automatically.
A shared risk envelope keeps portfolio safety comparable while allowing a
trend, breakout, range or recovery mechanism to express a different economic
trade path.

## Feedback and learning contract

The future evidence schema must attribute at least:

- signals, approved entries and entry-rejection reasons;
- closed-trade count and unresolved positions;
- net expectancy in risk units and modeled cost drag;
- maximum marked drawdown;
- results by chronological slice, asset and causal regime; and
- a named failure attribution.

The required interest-gate classes are sample sufficiency, adverse-cost
survival, chronological stability, asset concentration, drawdown bound and
complete failure attribution. Exact numeric gates and their calculation must
be hash-bound before the related round receives execution authorization.

Learning occurs only offline between immutable versions:

1. pre-register a bounded manifest and exact components;
2. execute once on permitted development evidence after separate authorization;
3. lock and close the result without automatic ranking;
4. attribute why each route passed, failed or stayed inactive; and
5. optionally propose a new manifest version under the remaining budget.

There is no runtime learning. A running strategy may not change its family,
assets, regimes, indicators, parameters, risk, costs, exit logic or gates. AI
may propose and explain the next version, but a human-reviewed, hash-bound
artifact and a fresh authorization boundary are required before execution.

## Multiple-testing and overfitting controls

- fixed family, route and total-hypothesis budgets;
- no global leaderboard or winner-by-return selection;
- no mutation from in-run outcomes;
- no use of calibration or evaluation to design a hypothesis;
- chronological and cross-asset attribution required before retention;
- baseline adverse costs remain mandatory;
- failure and `HOLD_CASH` are valid outcomes; and
- passing development interest gates cannot create Candidate v2.

A hypothesis that fails may be retired or replaced only under a new identity.
Its inspected result remains part of cumulative lineage and consumes its
hypothesis budget; deleting poor attempts from history is prohibited.

## Current nonexecuting state

At this milestone:

- hypothesis manifest registered: `false`;
- strategy components implemented: `false`;
- discovery runner implemented: `false`;
- dataset opened: `false`;
- development data opened: `false`;
- calibration data opened: `false`;
- evaluation data opened: `false`;
- performance evaluation executed: `false`;
- runtime learning authorized: `false`;
- automatic ranking authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`; and
- live execution authorized: `false`.

## Next controlled boundary

The next stage is `PRE_REGISTER_BOUNDED_HYBRID_DISCOVERY_ROUND_1`.

That stage must choose a small set of exact economic hypotheses from this
catalog, define each causal regime/signal/execution contract, freeze numeric
development-interest gates and pass synthetic/prefix-causality review. Only a
later, separate runner milestone may request development-data authorization.
Calibration and sealed evaluation are not the next step.
