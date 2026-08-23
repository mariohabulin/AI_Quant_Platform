# Strategy Research Inventory and Failure-Mode Analysis v1

## Purpose

This boundary answers what remains available after EMA candidate v1 and
Timeframe Sensitivity Study v1 closed without a robust edge. It inventories the
existing standalone strategy implementations, verifies their causal Strategy
Engine integration on synthetic diagnostic data and extracts facts from the
exact recorded timeframe report without running another market evaluation.

It does not rank strategies, sweep parameters, create combinations, select a
timeframe or authorize candidate v2, PAPER or live execution.

## Existing inventory

| Strategy | Family | Frozen implementation defaults | Research status |
| --- | --- | --- | --- |
| ADX | Trend | period 14, threshold 25 | Unevaluated component |
| ATR breakout | Breakout | period 14, multiplier 1 | Unevaluated component |
| Bollinger | Mean reversion | period 20, 2 standard deviations | Unevaluated component |
| Donchian | Breakout | period 20 | Unevaluated component |
| EMA crossover | Trend | fast 20, slow 50 | Candidate v1 rejected/closed |
| MACD | Trend | 12/26/9 | Unevaluated component |
| RSI | Mean reversion | period 14, 30/70 | Unevaluated component |
| Stochastic | Mean reversion | 14/3, 20/80 | Unevaluated component |
| Supertrend | Trend | period 10, multiplier 3 | Unevaluated component |

The eight unevaluated entries are code components, not eight approved trading
systems. Their unit-tested signal logic does not establish profitability,
robustness, suitable exit behavior or eligibility for formal validation.

## Synthetic integration audit

The audit builds one deterministic 720-row oscillating/trending OHLCV fixture
with explicit volatility shocks. For every default implementation it verifies:

- exact inventory name and declared feature requirements
- input-frame preservation
- deterministic repeated output
- signal domain restricted to `-1`, `0`, `1`
- at least one diagnostic buy and sell
- prefix causality: selected historical signals remain identical when all later
  rows are removed

The audit never invokes Backtesting Engine, Performance Analyzer, Multi-Asset
Validation, Strategy Evaluation Protocol or a real market dataset. Signal counts
on this fixture prove integration activity only and must not be interpreted as
quality or ranking.

Local Python 3.12 evidence reports all nine default implementations as
integration-ready. The fixed diagnostic counts are:

| Strategy | Buy | Sell | Neutral |
| --- | ---: | ---: | ---: |
| ADX | 13 | 13 | 694 |
| ATR | 3 | 3 | 714 |
| Bollinger | 78 | 68 | 574 |
| Donchian | 82 | 92 | 546 |
| EMA crossover | 9 | 9 | 702 |
| MACD | 20 | 19 | 681 |
| RSI | 243 | 241 | 236 |
| Stochastic | 21 | 22 | 677 |
| Supertrend | 8 | 9 | 703 |

## Recorded EMA failure modes

Failure-mode analysis accepts only canonical Timeframe Sensitivity Study report
SHA-256:

```text
505bd5b40a38d7e5b8b4538e1d7ac9cb459cd40f46108dc1a33a42c1647b64ab
```

It rechecks the sidecar, canonical bytes, schema/identity, exact 1h/6h/1d order,
no-ranking policy and every false authorization flag before extracting recorded
facts. It performs no new strategy calculation.

The closed evidence establishes constraints for the next hypothesis:

- reduce turnover or explicitly prove survival under baseline and stress costs
- bound drawdown rather than relying on terminal return alone
- state a falsifiable market-regime mechanism
- retain causal completed-Close/next-Open execution
- reserve genuinely unseen future validation data
- prohibit automatic ranking and leaderboard-style parameter sweeps

These constraints do not choose trend, breakout or mean reversion. In
particular, daily ETH remains an inspected relative development signal rather
than a selected winner.

## Controlled commands after integration

Print the inventory without audit or evidence analysis:

```powershell
python src/strategy_research_inventory.py
```

Run only synthetic integration checks and exact recorded-evidence extraction:

```powershell
python src/strategy_research_inventory.py `
    --audit-integrations `
    --study-report data/research/timeframe_sensitivity_v1/study_v1/timeframe_sensitivity_report.json
```

Both commands explicitly retain `strategy_screening_executed=false`,
`candidate_v2_authorized=false`, `optimization_authorized=false`,
`bounded_forward_paper_authorized=false` and
`live_execution_authorized=false`.

The next separately reviewed artifact may define a fixed development screening
protocol for standalone strategy families. It must freeze scope, defaults,
costs and multiple-comparison interpretation before any new performance results
are produced. Combining indicators or creating candidate v2 is a later decision,
not an automatic consequence of this inventory.
