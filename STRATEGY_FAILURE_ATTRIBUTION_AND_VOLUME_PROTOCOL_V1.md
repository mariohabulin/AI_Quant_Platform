# Strategy Failure Attribution and Volume Research Protocol v1

## Purpose

This protocol begins controlled alpha discovery by explaining why the eight
recorded standalone default strategies failed. It does not attempt to prove
that trading is impossible, and it does not select the least-bad rejected
strategy. The intended output is evidence for designing one structurally new,
falsifiable strategy hypothesis whose live behavior can later be reproduced by
a bounded calibration and validation procedure.

Volume is mandatory in this research stage. It is treated as market
participation and liquidity context, not as an automatic source of edge.

## Frozen source evidence

The protocol accepts only these inspected-development inputs:

| Evidence | Frozen identity |
| --- | --- |
| Dataset | Coinbase native BTC-USD and ETH-USD six-hour candles |
| Range | `[2019-01-01, 2026-08-01)` UTC |
| Dataset manifest SHA-256 | `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f` |
| Screening report SHA-256 | `9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f` |
| Recorded result | Eight `SCREEN_OUT` standalone default configurations |

The report loader rechecks the report bytes, exact SHA-256 sidecar, canonical
JSON, strategy order, dataset identity, all eight closed outcomes and every
authorization flag. The dataset lock independently rechecks the manifest,
sidecar, asset files and OHLCV evidence.

## Diagnostic profiles

Every strategy will later be replayed under three fixed profiles:

1. zero cost, to expose gross signal behavior
2. the existing conservative baseline cost profile
3. the existing adverse stress cost profile

Zero cost is diagnostic only. It is not a deployable assumption and cannot
support promotion. The difference between zero, baseline and stress evidence
will separate a weak signal from an otherwise useful but excessively expensive
implementation.

## Required attribution axes

The future one-shot attribution runner must report, without a score or ranking:

- gross profit/loss before costs
- commission, spread, slippage and total-cost drag
- turnover and completed-trade count
- market exposure and holding-period distribution
- drawdown magnitude and temporal concentration
- absolute return versus buy-and-hold excess return
- walk-forward persistence rather than only aggregate return
- market regime on the completed signal bar
- volume regime on the completed signal bar

Attribution uses `entry_signal_index`. Using the following execution bar to
label market or volume context would expose information that was unavailable
when the signal was formed.

## Frozen volume semantics

The initial causal volume layer uses a 20-bar trailing median of prior completed
bars. The current bar is excluded from its own baseline by a one-bar lag.

For each asset separately, it computes:

- relative volume: current volume divided by its prior trailing median
- relative dollar volume: current close-times-volume divided by its own prior
  trailing median
- on-balance volume as a directional participation feature
- `LOW`, `NORMAL` and `HIGH` relative-volume regimes using frozen thresholds
  `0.75` and `1.50`

BTC and ETH raw volume must never be compared directly. The scale-independent
ratios are calculated per asset and then interpreted descriptively across the
asset scope. All warm-up observations remain explicitly `UNKNOWN`; they are not
backfilled.

Volume may later serve as entry/breakout confirmation, low-liquidity avoidance,
a market-regime feature or a risk-sizing input. It is not assumed to be a
standalone strategy. Historical candle volume also does not replace live spread,
order-book depth or market-impact evidence.

## Interpretation boundary

This diagnostic is allowed to form future hypotheses. It is prohibited from:

- ranking the eight rejected configurations
- selecting a winner or candidate v2
- changing parameters after viewing a preferred slice
- executing an indicator combination
- claiming formal validation on inspected data
- authorizing optimization, PAPER or live execution

The exact meaning of the source outcome remains:

```text
SCREEN_OUT_AS_STANDALONE_FROZEN_CONFIGURATION
```

An indicator may still become a feature, filter or risk input in a different,
pre-registered system.

## Controlled commands after repository integration

Print the declaration without loading evidence or replaying performance:

```powershell
python src/strategy_failure_attribution.py
```

Revalidate and bind the exact dataset plus recorded screening report:

```powershell
python src/strategy_failure_attribution.py `
    --manifest data/research/first_candidate_v1/manifest.json `
    --screening-report data/research/strategy_family_screening_v1/screening_v1/strategy_family_screening_report.json
```

The lock command must print `failure_attribution_executed=false` and
`performance_replay_executed=false`. It writes no evidence. Actual diagnostic
execution requires a separate reviewed runner, clean preflight and explicit
command.

## Exit criteria

This protocol can advance only after the separate runner records enough detail
to distinguish at least these failure modes per strategy and asset:

- no gross signal edge even before costs
- possible gross behavior destroyed by turnover and costs
- edge limited to one market or volume regime
- excessive exposure or holding-period risk
- drawdown concentrated in identifiable regimes or windows
- unstable behavior across walk-forward windows

Those observations may define a small hypothesis-led combination containing
direction, regime, volume confirmation and risk sizing. They cannot themselves
validate it. Any future candidate requires a new immutable identity and a
genuinely unseen final-validation boundary.

## Authorization state

Candidate v2, automatic ranking, parameter sweep, strategy combination,
optimization, bounded forward PAPER and live execution remain unauthorized.
