# Timeframe Sensitivity Study v1 — Closure

## Final status

- Date: `2026-08-23`
- Study ID: `ema-20-50-btc-eth-timeframe-sensitivity-v1`
- Execution revision: `8042816`
- Evidence commit: `cb43a74`
- Report SHA-256:
  `505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab`
- Closure classification: `COMPLETED_NO_ROBUST_EDGE`
- Automatic timeframe selection: `false`
- Candidate v2 authorized: `false`
- Optimization authorized: `false`
- Bounded forward PAPER authorized: `false`
- Live execution authorized: `false`

This classification is an exploratory research closure, not a Strategy
Evaluation Protocol promotion outcome. Candidate v1 remains permanently closed
as `REJECTED`; the study neither reopens it nor selects a replacement.

## Frozen evidence

The comparison used the unchanged long-only EMA 20/50 implementation, exact
BTC-USD/ETH-USD scope, causal next-Open execution, frozen baseline/stress costs,
seed `20260822`, equal 720-day training and 180-day test/step durations, and the
same historical end boundary.

- observed-native 1h manifest SHA-256:
  `b9ba8126ca0612402919dd7f0f0096db2b2ef2f0a7d0669b6848276e88bc8157`
- continuous 1d manifest SHA-256:
  `77bc9765a828174b1fd5d46b0d06d216db47e3edab5d91cc65f47a350a335691`
- recorded 6h reference-report SHA-256:
  `6b79d0932ee334574ffdbef1aca73c8b900ab8fcb8fbafb857bdd327d38d547c`

The six-hour candidate was not rerun. The one-hour lock retained 66,437 BTC
rows with 19 explicit provider gaps and 66,438 ETH rows with 18 gaps. The
longest gap was five hours for each asset. No synthetic, interpolated,
forward-filled or resampled candle entered the study.

## Result

Every aggregate and every asset/profile diagnostic classification is
`REJECTED`. No combination passed statistical falsification.

| Timeframe | Asset | OOS return baseline / stress | Max drawdown baseline / stress | Positive WF excess baseline / stress |
| --- | --- | ---: | ---: | ---: |
| 1h | BTC-USD | -93.06% / -96.76% | 93.06% / 96.76% | 0/11 / 0/11 |
| 1h | ETH-USD | -95.32% / -97.90% | 95.32% / 97.90% | 1/11 / 1/11 |
| 6h | BTC-USD | +3.74% / -6.88% | 40.72% / 44.36% | 3/11 / 2/11 |
| 6h | ETH-USD | -44.90% / -51.52% | 55.11% / 57.22% | 3/11 / 3/11 |
| 1d | BTC-USD | -3.17% / -6.22% | 36.16% / 37.30% | 3/11 / 3/11 |
| 1d | ETH-USD | -17.77% / -20.99% | 39.03% / 40.59% | 7/11 / 6/11 |

The one-hour result is not an evidence-volume failure: BTC/ETH supplied 190/200
OOS trades and 461/448 unseen walk-forward trades. Its extreme loss and
drawdown, zero/near-zero window persistence and entirely failed gates show that
the unchanged nominal EMA periods are unsuitable at that frequency under the
frozen assumptions.

Six-hour BTC produced a positive baseline absolute/excess return, but the
absolute return became negative under stress, only 2/11 stressed windows beat
the benchmark, drawdown stayed above 44% and falsification failed. ETH failed
absolute/excess evidence and reached 57.22% stressed drawdown.

Daily ETH is a development hypothesis signal only. It beat its declining
benchmark by 23.95 percentage points baseline and 20.96 points under stress;
baseline persistence reached 7/11. It still lost 17.77%/20.99% absolutely,
stress persistence fell to 6/11, OOS evidence contained only ten completed
trades and statistical falsification failed. The study's no-ranking rule
therefore prohibits calling 1d ETH a winner or promotion candidate.

Across all 12 asset/profile views, every bootstrap lower bound was negative and
permutation p-values ranged from approximately 0.221 to 1.0. There is no
statistically supported positive edge. Timeframe materially changes behavior,
but none rescues the frozen EMA 20/50 hypothesis.

## Evidence serialization closure

Attempt 1 failed before final/staging persistence when daily performance
contained the analyzer's defined positive-infinite profit factor. Schema v3 was
committed before deterministic recovery and encoded only that state as
`POSITIVE_INFINITY_NO_LOSING_TRADES`. The final evidence records two occurrences
in daily baseline and two in daily stress, zero in 1h/6h, and retains fatal
rejection of every other non-finite value.

## Research boundary after closure

All market history through `2026-08-01T00:00:00Z` used here is inspected
development data. It cannot become a genuinely unseen final test for candidate
v2, regardless of which strategy or timeframe is chosen later.

The next authorized milestone is research-only failure-mode analysis and design
of one new falsifiable strategy hypothesis. The evidence supports investigating
structural changes that reduce turnover, bound drawdown and distinguish market
regimes; it does not authorize a parameter sweep, automatic winner selection or
mutation of candidate v1. Any candidate v2 must receive a new immutable
identity and an independently locked future/unseen validation boundary before
formal evaluation. PAPER and live execution remain separate later gates.
