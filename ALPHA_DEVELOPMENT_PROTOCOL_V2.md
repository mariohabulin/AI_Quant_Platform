# Alpha Development Protocol v2

## Purpose

This protocol converts the closed Failure Attribution v1 diagnosis into a
small, falsifiable joint-condition research scope. It does not attempt to find
a winner by trying many combinations. It does not authorize Candidate v2,
optimization, forward PAPER or live execution.

The research question is:

> Can the default ADX directional mechanism retain cross-asset evidence after
> costs when entries require causal high relative volume, optionally the exact
> bullish-normal market regime, while active risk and turnover controls bound
> the failure modes observed in the standalone screen?

The answer is unknown. Failure Attribution v1 summarized market regime,
relative volume and OBV separately; it did not test their intersection.

## Frozen evidence identity

| Field | Value |
| --- | --- |
| Protocol schema | `2` |
| Development ID | `adx-regime-volume-alpha-development-v2` |
| Dataset role | `INSPECTED_DEVELOPMENT_ONLY` |
| Timeframe | native Coinbase `6h` |
| Assets | `BTC-USD`, `ETH-USD` |
| Dataset manifest SHA-256 | `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f` |
| Failure Attribution report SHA-256 | `e4193bff907a2121701e7ddc1d740894641c7bf427c9501fd4ecd4392a1f81f4` |

The lock rechecks canonical report bytes, the checksum sidecar, execution and
authorization state, and the exact qualitative ADX evidence used to form the
hypothesis. It also independently revalidates the dataset manifest and assets.

## Exact causal ablation chain

The order below is fixed and is not a leaderboard:

1. `adx_high_relative_volume`
2. `adx_bullish_normal_high_relative_volume`
3. `adx_bullish_normal_high_relative_volume_obv_rising`

All variants share:

- long-only ADX 14 directional entry: ADX at least 25 and `+DI > -DI`
- high per-asset relative volume versus the lagged 20-bar median
- completed signal-bar observation and following-bar-open execution
- exit hysteresis when ADX falls below 20 or `+DI <= -DI`
- four completed bars of cooldown after an exit
- signal-bar ATR 14 risk distance of two ATR
- target distance of three times initial risk

The second variant adds the exact `BULLISH_NORMAL` causal market regime. The
third adds rising 20-bar OBV as a secondary ablation because rising OBV was not
cross-asset positive in marginal evidence. Volume confirms entry only; moving
from high to normal volume does not force an immediate exit and create churn.
Relative dollar volume is retained as diagnostics rather than silently added
as another gate.

No parameter grid, automatic rank, tie-break or result-driven rule mutation is
allowed in this protocol.

## Risk and turnover boundary

The intended live-equivalent risk contract is frozen before performance:

- 0.50% equity risk per new position
- maximum 50% equity position size
- no leverage and no shorting
- 20% portfolio-drawdown ceiling
- 2% daily and 5% weekly new-risk ceilings
- minimum 3:1 reward/risk
- maximum annual total executed notional of 24 times initial capital
- maximum annual baseline modeled cost of 20% of initial capital

A breach of either turnover/cost budget screens out the mechanism even if its
gross return is positive. Both assets must survive baseline costs.

## Implemented protective-exit prerequisite

Protective Exit Engine v1 now converts signal-bar ATR distance into active,
costed stop and target exits. The earlier Backtesting Engine limitation—using
Risk Engine levels for sizing and reporting without executing them—has been
removed. That component alone does not authorize Alpha v2 performance.

The implemented and tested component freezes:

- position sizing at the following bar open from the lagged signal-bar ATR
- stop at execution open minus two signal-bar ATR
- target at execution open plus three initial-risk distances
- exit at the first available open after a gap through the stop
- conservative stop-first treatment when stop and target are both touched in
  one candle
- commission, slippage and spread on every protective fill
- unchanged next-bar-open signal semantics and deterministic terminal close

This prerequisite prevents a report from claiming bounded risk when no actual
protective fill occurred.

## Venue and execution scenarios

The separate runner may use only these frozen taker scenarios:

| Scenario | Commission | Slippage | Full spread | Role |
| --- | ---: | ---: | ---: | --- |
| Coinbase low-volume taker baseline | 0.60% | 0.05% | 0.10% | deployability baseline |
| Coinbase adverse stress | 0.60% | 0.15% | 0.30% | stress |
| Kraken Pro $10k 30-day taker | 0.38% | 0.05% | 0.10% | venue sensitivity only |

The Kraken rate was frozen from its public fee schedule on 2026-08-24. It is
not proof that a particular account qualifies: current 30-day volume, assets
on platform and the then-current fee schedule must be rechecked. The Kraken
0.22% maker scenario is recorded but blocked until a causal order-placement,
non-fill and partial-fill model exists. A maker fee cannot be applied to every
historical signal while assuming guaranteed fills.

A cheaper venue may explain cost sensitivity. It cannot override drawdown,
walk-forward persistence or statistical falsification.

## Temporal development and interpretation

Development walk-forward windows retain 2,880 six-hour training bars, 720 test
bars and a 720-bar step, with at least five test windows. Twenty completed
development trades per asset are required for descriptive interest; a future
formal candidate still requires at least 30 genuinely unseen trades per asset.

This dataset has already been inspected. Outcomes are limited to:

- `MECHANISM_RETAINS_DEVELOPMENT_INTEREST`
- `SCREEN_OUT`
- `INCONCLUSIVE`

Retaining development interest is neither validation nor Candidate v2. Any
bounded calibration is a later, separately pre-registered procedure. Formal
candidate evaluation requires a new immutable identity and a genuinely unseen
future-validation boundary.

## Separate one-shot development runner

`alpha_development_runner.py` binds this protocol without changing its
hypothesis. It executes exactly three fixed variants under Coinbase baseline,
Coinbase stress and Kraken taker sensitivity: nine multi-asset evaluations.
Baseline and stress control outcomes; Kraken remains sensitivity only.

Every evaluation receives the exact Risk Engine and active Protective Exit
Policy. Raw OOS trades derive annualized executed-notional turnover, modeled
cost fraction and exit-reason counts before compact canonical evidence is
written. The 24x annual turnover and 20% annual baseline-cost budgets are hard
screen-out gates alongside the 20% drawdown limit.

The runner is one-shot and atomic. It emits no score, ranking, calibration,
selected variant or candidate. Execution remains prohibited until its patch is
reproduced on Windows, committed and pushed and an absent-evidence preflight is
reviewed.

## Controlled commands after integration

Print the declaration without reading evidence or evaluating performance:

```powershell
python src/alpha_development_protocol.py
```

Lock the exact dataset and attribution evidence without performance:

```powershell
python src/alpha_development_protocol.py `
    --manifest data/research/first_candidate_v1/manifest.json `
    --attribution-report data/research/strategy_failure_attribution_v1/attribution_v1/failure_attribution_report.json
```

Expected statuses are `ALPHA_DEVELOPMENT_EVIDENCE_LOCK_PENDING` and
`ALPHA_DEVELOPMENT_EVIDENCE_LOCKED`. Both report protective-exit implementation
as true while joint performance, calibration, Candidate v2, optimization,
PAPER and live execution remain false.
