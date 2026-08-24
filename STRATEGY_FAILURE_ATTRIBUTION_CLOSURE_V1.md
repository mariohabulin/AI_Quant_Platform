# Strategy Failure Attribution Closure v1

## Closed result

Strategy Failure Attribution v1 is closed as a completed diagnostic study on
inspected BTC/ETH six-hour development evidence.

| Field | Recorded value |
| --- | --- |
| Status | `FAILURE_ATTRIBUTION_COMPLETED` |
| Report schema | `1` |
| Dataset range | `[2019-01-01, 2026-08-01)` UTC |
| Manifest SHA-256 | `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f` |
| Screening-report SHA-256 | `9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f` |
| Attribution-report SHA-256 | `e4193bff907a2121701e7ddc1d740894641c7bf427c9501fd4ecd4392a1f81f4` |
| Runner revision | `334ceba` |
| Evidence revision | `f189689` |
| Strategies | 8 |
| Cost profiles | zero cost, baseline, stress |
| Multi-asset diagnostic replays | 24 |
| Asset/profile views | 48 |

The canonical report and SHA-256 sidecar are stored under:

```text
data/research/strategy_failure_attribution_v1/attribution_v1/
  failure_attribution_report.json
  failure_attribution_report.sha256
```

Windows reproduced 59/59 focused and 866/866 complete tests before the runner
revision was committed and pushed. Clean preflight then verified the exact
manifest and screening evidence, matching `HEAD`/`origin/main`, a clean working
tree and absent final/staging attribution evidence. The matrix executed once,
the report checksum matched and no staging directory remained.

## What the diagnostic established

Nine of the sixteen strategy/asset views have positive zero-cost OOS return.
The range is -45.50% to +54.33%, demonstrating that the rejected standalone
results do not all represent absence of raw signal.

Every baseline and stress view is nevertheless negative. Baseline evidence
records:

- cumulative modeled costs from 1,488.68 to 5,274.93 on 5,000 initial capital
- round-trip notional turnover from 42.53 to 150.71 times initial capital
- zero-to-baseline OOS return deterioration from 20.37 to 87.96 percentage
  points
- drawdown above the frozen 20% limit for every view
- failed walk-forward persistence and statistical falsification throughout

The cost amounts are cumulative across the OOS interval, not a fee for one
trade. Round-trip turnover counts both entry and exit notional. Under the
frozen baseline, 0.60% commission per side plus 0.05% slippage and half of the
0.10% full spread produces approximately 0.70% modeled friction per execution.
Repeated full-capital turnover therefore dominates several otherwise positive
zero-cost mechanisms.

The closed explanation is not `INDICATORS_HAVE_NO_INFORMATION`. It is:

```text
RAW_SIGNAL_EXISTS_IN_SOME_CONTEXTS
+ UNFILTERED_TURNOVER_AND_COST_DESTRUCTION
+ EXCESSIVE_DRAWDOWN
+ INSUFFICIENT_TEMPORAL_PERSISTENCE
```

Changing venue or order type may reduce friction, but cannot by itself repair
drawdown or persistence. Any venue comparison must freeze actual maker/taker
fees, spread, slippage and fill assumptions before replay; an unfilled maker
order is not equivalent to a filled market order.

## Market-regime evidence

The strongest cross-asset market-regime slice is the default ADX mechanism in
`BULLISH_NORMAL` conditions:

| Asset | Trades | Zero-cost P/L | Baseline P/L | Baseline costs |
| --- | ---: | ---: | ---: | ---: |
| BTC-USD | 14 | 1,621.39 | 481.04 | 1,029.87 |
| ETH-USD | 19 | 2,651.78 | 1,193.42 | 1,284.33 |

ADX losses outside that condition explain why the unrestricted standalone
configuration remains rejected. Several other positive slices are not
cross-asset stable: Bollinger BTC, Donchian ETH and Stochastic ETH retain
positive baseline P/L in `SIDEWAYS_NORMAL`, while their paired asset does not.
Isolated two-to-five-trade regime profits are descriptive only and cannot
support a new rule.

## Volume and OBV evidence

The strongest coherent cross-asset volume slice is ADX under `HIGH` relative
volume:

| Asset | Trades | Zero-cost P/L | Baseline P/L | Baseline costs |
| --- | ---: | ---: | ---: | ---: |
| BTC-USD | 25 | 3,721.52 | 1,850.49 | 1,718.26 |
| ETH-USD | 21 | 2,640.65 | 763.89 | 1,372.46 |

Low and normal relative-volume ADX entries are collectively destructive. This
is direct evidence that a participation filter may remove a substantial part
of the rejected mechanism's poor behavior rather than merely relabel it.

OBV direction is informative but not a cross-asset standalone gate. Falling
OBV ADX trades lose after baseline costs on both assets. Rising OBV retains
positive baseline P/L for ETH but remains negative for BTC. OBV may therefore
be tested as a secondary interaction feature, not assumed to be mandatory
confirmation solely from its marginal summary.

## Interpretation boundary

Market regime, relative-volume regime and OBV were summarized separately. The
report does not calculate their joint intersection. It is invalid to add their
marginal profits or claim that this exact conjunction is already profitable:

```text
ADX
+ directional trend condition
+ BULLISH_NORMAL market regime
+ HIGH relative volume
+ optional OBV confirmation
```

That conjunction is one falsifiable development hypothesis for the next
protocol, not a validated strategy and not Candidate v2.

The current dataset is fully inspected development evidence. Conditional
results may guide design, bounded calibration and mechanism falsification, but
cannot become the final unseen confirmation for a future candidate.

## Next controlled research boundary

Alpha Development Protocol v2 must freeze a small hypothesis-led mechanism set
before joint evaluation. It must include:

1. causal direction and market-regime definitions
2. mandatory per-asset relative-volume evidence
3. a bounded decision on whether OBV is a secondary confirmation
4. ATR-based risk distance, position sizing and drawdown controls
5. explicit exit, time-stop, cooldown and re-entry semantics
6. a turnover/cost budget that can screen out economically untradeable variants
7. Coinbase baseline/stress plus separately sourced venue/execution scenarios
8. temporally ordered training/validation and a frozen live-equivalent
   recalibration procedure if calibration is used
9. no unrestricted parameter sweep, result leaderboard or hindsight winner
10. a new immutable candidate identity and genuinely unseen final boundary
    before any formal candidate-v2 evaluation

Development must first test whether the joint mechanism reduces poor entries,
turnover, cumulative cost and drawdown while retaining cross-asset persistence.
Only a pre-declared rule may form one new candidate hypothesis.

## Authorization state

Closure records explanation, not promotion. It generated no ranking, automatic
strategy selection or automatic hypothesis. The following remain false:

- candidate-v2 authorization
- optimization authorization
- bounded-forward-PAPER review eligibility
- bounded-forward-PAPER authorization
- live-execution authorization

Cloud trading and monitoring services remain parked. Their completed
infrastructure soak is not profitability evidence and does not change this
research boundary.
