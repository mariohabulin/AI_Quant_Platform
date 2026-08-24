# Strategy Failure Attribution Runner v1

## Purpose

This runner executes the exact diagnostic matrix frozen by Strategy Failure
Attribution and Volume Research Protocol v1. It explains the recorded failure
of eight standalone default configurations on inspected development data. It
does not optimize them, combine indicators, rank results, select a strategy or
perform candidate-v2 validation.

## Frozen matrix

| Dimension | Exact scope |
| --- | --- |
| Strategies | ADX, ATR, Bollinger, Donchian, MACD, RSI, Stochastic, Supertrend |
| Profiles | zero cost, baseline cost, stress cost |
| Assets | BTC-USD, ETH-USD |
| Timeframe | native 6h |
| Multi-asset replays | 24 |
| Asset/profile views | 48 |
| Execution | completed signal bar, following-bar Open |

Zero cost is an explanatory counterfactual. Baseline and stress remain the
deployability evidence. A favorable zero-cost result cannot authorize a
candidate, PAPER or live trading.

## Evidence produced

For every strategy/profile/asset, the report retains:

- OOS and walk-forward validation evidence in bounded compact form
- a SHA-256 of the complete raw evaluation before compaction
- gross P/L, commission, spread/slippage execution cost and net P/L
- entry/exit notional and turnover relative to initial capital
- observed-bar exposure and holding-period distribution
- maximum drawdown peak, trough, recovery and yearly concentration
- causal market regime on `entry_signal_index`
- causal relative volume and relative dollar-volume context
- LOW/NORMAL/HIGH volume-regime and OBV-direction results

Trade cost identities must satisfy both:

```text
total_commission + execution_cost = total_costs
gross_profit_loss - total_costs = profit_loss
```

Any mismatch fails before evidence persistence.

## Cross-profile interpretation

The runner reports the zero-to-baseline and baseline-to-stress change for each
asset. Diagnostic flags describe facts such as:

- no positive zero-cost OOS return
- positive zero-cost return that fails baseline cost survival
- positive baseline return that fails stress survival
- baseline/stress drawdown above the frozen limit
- failed walk-forward persistence
- failed statistical falsification

These flags are not a score. There is no aggregate rank, tie-break, winner,
selected strategy or automatically generated alpha hypothesis.

## Atomic evidence boundary

The runner refuses to start when final or staging evidence already exists. It
revalidates the exact dataset manifest, recorded screening report, strategy
order, configuration, asset scope and causal execution semantics.

All 24 raw evaluations, metrics, compact evidence and final canonical JSON must
complete in memory before staging begins. The report and sidecar are then
written to a staging directory and atomically renamed to:

```text
data/research/strategy_failure_attribution_v1/attribution_v1/
  failure_attribution_report.json
  failure_attribution_report.sha256
```

The runner will not overwrite or repeat recorded evidence.

## Controlled execution command

Run only after Windows focused/full reproduction, reviewed commit/push, clean
working tree and absent final/staging evidence:

```powershell
python src/strategy_failure_attribution_runner.py `
    --manifest data/research/first_candidate_v1/manifest.json `
    --screening-report data/research/strategy_family_screening_v1/screening_v1/strategy_family_screening_report.json
```

The command executes the complete diagnostic matrix once. It must not be
combined with parameter changes or ad hoc strategy runs.

## Required review after execution

Before designing a new system, review the report in this order:

1. distinguish absent gross signal from cost-destroyed signal
2. identify turnover, exposure, holding and drawdown failure
3. inspect persistence across chronological windows
4. inspect market-regime concentration
5. inspect RVOL, relative dollar volume and OBV context
6. form a small causal hypothesis; do not select the least-bad result

The future hypothesis may combine direction, regime, volume confirmation and
risk sizing. Its calibration procedure must be frozen separately and its final
claim must use genuinely unseen data.

## Authorization state

The recorded report explicitly keeps automatic ranking, strategy selection,
parameter sweep, combination execution, candidate v2, optimization, bounded
forward PAPER and live execution false. Cloud PAPER infrastructure remains
parked and unchanged.
