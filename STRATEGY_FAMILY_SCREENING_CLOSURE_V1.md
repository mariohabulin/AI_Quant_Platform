# Strategy Family Screening Closure v1

## Closed result

Strategy Family Screening v1 is closed as a completed development-only baseline
for eight exact standalone default configurations.

| Field | Recorded value |
| --- | --- |
| Status | `STRATEGY_FAMILY_SCREENING_COMPLETED` |
| Dataset | Coinbase native BTC/ETH 6h development data |
| Dataset range | `[2019-01-01, 2026-08-01)` UTC |
| Manifest SHA-256 | `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f` |
| Report SHA-256 | `9cf74deebe6a7efe9928d89b93b8ad4f7504ef70dfcf07ab0c00091a2cb9ec7f` |
| Evidence revision | `2973636` |
| Strategies screened | 8 |
| Multi-asset evaluations | 16 |
| Asset/profile views | 32 |
| `SCREEN_OUT` | 8 |
| `MECHANISM_RETAINS_INTEREST` | 0 |
| `INCONCLUSIVE` | 0 |
| Selected strategy | None |

The canonical report and SHA-256 sidecar are stored under:

```text
data/research/strategy_family_screening_v1/screening_v1/
  strategy_family_screening_report.json
  strategy_family_screening_report.sha256
```

## Evidence summary

ADX 14/25, ATR breakout 14/1, Bollinger 20/2, Donchian 20, MACD
12/26/9, RSI 14/30/70, Stochastic 14/3/20/80 and Supertrend 10/3 all
receive `SCREEN_OUT` in their exact frozen standalone configurations.

For every strategy:

- baseline multi-asset classification is `REJECTED`
- stress multi-asset classification is `REJECTED`
- minimum walk-forward-window evidence passes
- minimum unseen-trade evidence passes
- the 20% OOS-drawdown gate fails

All 32 BTC/ETH baseline/stress asset views have negative absolute OOS return and
fail statistical falsification. Recorded OOS drawdown ranges from 40.32% to
93.71%. A positive excess return in a subset of ETH views means only that the
strategy lost less than the negative buy-and-hold benchmark; it is not positive
absolute performance or validated edge.

## Exact scope of `SCREEN_OUT`

The frozen outcome is intentionally configuration-specific:

```text
SCREEN_OUT_AS_STANDALONE_FROZEN_CONFIGURATION
```

It means that an exact default implementation is not a deployable strategy and
cannot support candidate-v2 promotion. It does not mean:

- the indicator or strategy family can never contain edge
- the indicator cannot serve as a feature, filter or risk input
- a pre-registered combination or adaptive procedure must fail
- parameter calibration is permanently prohibited
- systematic trading is impossible

Protocol v1 deliberately tested no indicator combination, regime filter,
position-sizing adaptation or parameter-calibration procedure. Those untested
systems are different research objects and require their own bounded protocol.

## Why the negative baseline is retained

The evidence is retained unchanged because it defines what does not qualify as
a production strategy and prevents later hindsight from relabeling a rejected
default variant as successful. It also provides a controlled reference for
attributing failure before more complex research begins.

The existing history is now inspected development evidence. It may be used to
form and calibrate a future hypothesis, but any performance observed while
doing so is not final confirmation.

## Next controlled research boundary

The next milestone is controlled alpha discovery, beginning with failure
attribution rather than a broad parameter sweep.

The diagnostic must separate:

1. gross strategy behavior from commission, spread and slippage loss
2. turnover, exposure and holding-period effects
3. bull, bear, sideways and volatility-regime behavior
4. entry, exit and drawdown concentration
5. absolute return from relative benchmark excess
6. persistent effects from isolated favorable windows

After attribution, a new protocol may pre-register a small hypothesis-led set
of combinations, regime filters, volatility/risk sizing rules and bounded
parameter ranges. Calibration may occur only inside temporally ordered
training/validation boundaries. If intended live behavior recalibrates, the
entire causal recalibration procedure must itself be frozen and walk-forward
tested.

Any candidate v2 must then receive:

- one immutable candidate identity
- exact strategy and calibration procedure
- exact cost and execution semantics
- exact asset/timeframe scope
- a genuinely unseen final-validation boundary

## Authorization state

Closure does not authorize:

- automatic ranking or strategy selection
- candidate v2
- parameter optimization outside a future bounded protocol
- bounded forward PAPER
- live execution

All such authorization remains `False`.
