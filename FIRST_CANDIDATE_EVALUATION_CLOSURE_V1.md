# First Candidate Evaluation Closure v1

## Decision

The immutable first strategy candidate is closed as `REJECTED` under Strategy
Evaluation Protocol v1. The result is a valid research outcome, not a runtime
failure and not permission to alter candidate v1 after inspecting its evidence.

- Candidate: `ema-crossover-20-50-btc-eth-native-6h-v1`
- Dataset manifest SHA-256:
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`
- Evaluation report SHA-256:
  `6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c`
- Evidence commit: `8978c72`
- Protocol result: `REJECTED`
- Next stage: `RESEARCH`

The canonical report and checksum remain the source of truth at:

```text
data/research/first_candidate_v1/evaluation_v1/evaluation_report.json
data/research/first_candidate_v1/evaluation_v1/evaluation_report.sha256
```

## Frozen evaluation boundary

The report matches the pre-registered identity and exact named scope:

- existing long-only EMA 20/50 strategy, with no leverage
- native Coinbase six-hour candles
- `BTC-USD` and `ETH-USD`
- `2019-01-01T00:00:00Z` inclusive through `2026-08-01T00:00:00Z`
  exclusive, with 11,076 continuous rows per asset
- completed-close signals executed at the following bar's Open
- expanding 2,880-bar train / 720-bar test walk-forward windows with a 720-bar
  step
- frozen random seed `20260822` and 5,000 simulations
- nonzero baseline costs of 0.60% commission, 0.05% slippage and 0.10% full
  spread
- stress costs of 0.60% commission, 0.15% slippage and 0.30% full spread

The 70/30 chronological OOS split placed the unseen segment from
`2024-04-22T06:00:00Z` through `2026-07-31T18:00:00Z`. No candidate parameter,
cost, threshold, asset or date boundary was changed after viewing the result.

## Protocol gates

| Gate | Required | Observed | Result |
| --- | ---: | ---: | --- |
| Strategy identity frozen | exact | exact | PASS |
| Asset scope frozen | exact | exact | PASS |
| Baseline aggregate | `VALIDATED` | `REJECTED` | FAIL |
| Cost-stress aggregate | `VALIDATED` | `REJECTED` | FAIL |
| Walk-forward windows per asset | at least 5 | 11 / 11 | PASS |
| Unseen walk-forward trades per asset | at least 30 | 75 / 74 | PASS |
| Maximum OOS drawdown | at most 20% | 44.36% BTC / 57.22% ETH worst profile | FAIL |

Both aggregate passes classified zero assets as `VALIDATED` and both assets as
`REJECTED`. The failed protocol gates are therefore
`baseline_validated`, `cost_stress_validated` and
`oos_drawdown_within_limit`.

## Per-asset evidence

The return values below are unseen OOS results. Excess return is measured
against the aligned first-Open/final-Close buy-and-hold benchmark.

| Asset / profile | Strategy return | Benchmark return | Excess return | OOS max drawdown | Positive excess windows | OOS trades |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BTC baseline | +3.74% | -6.73% | +10.46 pp | 40.72% | 3/11 (27.27%) | 27 |
| BTC stress | -6.88% | -7.10% | +0.21 pp | 44.36% | 2/11 (18.18%) | 27 |
| ETH baseline | -44.51% | -43.19% | -1.71 pp | 55.11% | 3/11 (27.27%) | 32 |
| ETH stress | -51.08% | -43.42% | -8.10 pp | 57.22% | 3/11 (27.27%) | 32 |

The promotion threshold required positive walk-forward excess return in at
least 60% of windows. Every observed rate was below 28%. The protocol's unseen
trade-count gate uses completed trades across walk-forward test windows (75 BTC
and 74 ETH), while the final table's OOS-trade column describes the separate
70/30 chronological split; the two counts measure different evidence views.

## Statistical falsification

None of the four asset/profile combinations passed statistical falsification.
Every 95% bootstrap expectancy interval crossed zero and every one-sided
permutation result was nonsignificant:

| Asset / profile | Observed expectancy | 95% bootstrap interval | Permutation p-value |
| --- | ---: | ---: | ---: |
| BTC baseline | 17.16 | [-132.66, 189.48] | 0.4119 |
| BTC stress | -2.72 | [-149.88, 166.88] | 0.5019 |
| ETH baseline | 145.53 | [-142.23, 513.11] | 0.2212 |
| ETH stress | 123.86 | [-161.40, 484.95] | 0.2527 |

This means the frozen evidence does not establish a persistent positive edge.
BTC baseline produced a small positive OOS absolute result and beat a declining
benchmark, but that isolated result did not persist across windows, survive the
stress profile as a positive absolute return, pass falsification or stay within
the drawdown ceiling. ETH failed both absolute and excess-return gates under
both profiles.

## Authorization state

Candidate v1 is not eligible for bounded forward PAPER and must not be rerun as
though it were unseen. The evidence envelope correctly retains:

- `bounded_forward_paper_review_eligible=false`
- `bounded_forward_paper_authorized=false`
- `optimization_authorized=false`
- `live_execution_authorized=false`

The rejection does not invalidate the research platform. It demonstrates that
the pre-registration, causal execution, realistic-cost, multi-asset,
walk-forward, falsification and risk gates rejected a weak candidate instead of
promoting it.

## Next controlled research boundary

Candidate v1 and its report are permanently closed. The next authorized work is
an explicitly exploratory Timeframe Sensitivity Study v1 over `1h`, `6h` and
`1d` BTC/ETH evidence. That study may diagnose whether the EMA 20/50 behavior is
timeframe-dependent, but it may not retroactively rescue candidate v1 or
authorize PAPER.

If exploration justifies a candidate v2, its hypothesis, strategy/risk rules,
timeframe, assets, costs and thresholds must be frozen under a new identity.
Because the current historical evidence has now been inspected, formal v2
promotion also requires a separately locked, genuinely unseen final-validation
boundary. Equity research remains a later, separately pre-registered venue and
market-calendar track rather than an extension of this Coinbase result.
