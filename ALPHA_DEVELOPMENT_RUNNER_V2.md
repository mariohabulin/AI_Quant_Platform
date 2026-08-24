# Alpha Development Runner v2

## Purpose

This runner executes the exact Alpha Development Protocol v2 joint-condition
scope once on inspected development data. It asks whether the pre-declared
ADX, relative-volume, market-regime and optional OBV intersections retain
development interest when position sizing, active protective exits, execution
costs, turnover and drawdown are evaluated together.

It is not formal candidate validation. It cannot rank variants, calibrate
parameters, create Candidate v2, authorize PAPER or enable live execution.

## Frozen evaluation matrix

The runner executes exactly nine multi-asset evaluations:

```text
3 fixed causal ablations x 3 reviewed taker scenarios = 9 evaluations
```

The immutable variant order is:

1. `adx_high_relative_volume`
2. `adx_bullish_normal_high_relative_volume`
3. `adx_bullish_normal_high_relative_volume_obv_rising`

Each evaluation covers `BTC-USD` and `ETH-USD` on the exact native Coinbase
six-hour development dataset. The executable scenario order is Coinbase
baseline, Coinbase stress and Kraken Pro taker sensitivity.

The deferred Kraken maker scenario is structurally excluded. The runner has no
maker fill, partial-fill or non-fill model and therefore cannot use maker fees.

## Deterministic validation configuration

Every scenario uses the same frozen validation settings:

- 2,880 six-hour train bars
- 720 test bars and a 720-bar non-overlapping step
- expanding walk-forward history
- 70% chronological in-sample split
- 5,000 initial capital per asset evaluation
- 5,000 falsification simulations, 95% confidence and seed `20260822`
- at least five walk-forward windows
- at least 20 completed development trades per asset
- at most 20% OOS drawdown
- `next_bar_open` execution and deterministic terminal close

Twenty trades is a development-evidence threshold only. A future formal
candidate still requires a new immutable identity and at least 30 trades per
asset on genuinely unseen evidence.

## Risk and protective execution

Every validator receives a fresh frozen Risk Engine and Protective Exit Policy:

- 0.50% equity risk per position and 50% maximum position fraction
- 20% portfolio drawdown guard
- 2% daily and 5% weekly loss guards
- minimum 3:1 reward/risk, no leverage and no shorting
- active signal-bar ATR stop and 3R target
- stop-first same-bar ambiguity and conservative gap semantics
- commission, slippage and spread on protective fills

The runner verifies the exact protective-policy declaration in in-sample, OOS
and every walk-forward partition before accepting validator evidence.

## Operational evidence derived before compaction

Raw OOS trade evidence is used to calculate, per variant, scenario and asset:

- executed entry plus exit notional
- turnover as a multiple of initial capital and annualized turnover
- total modeled costs and annualized cost fraction of initial capital
- counts of signal, protective-stop, protective-target and terminal exits
- number of trades actually closed by the protective engine

The canonical report retains those summaries but not raw trade history or the
equity curve. Each complete raw evaluation is hashed before compaction.

## Development outcome policy

Coinbase baseline and stress control the development gates. Kraken is
sensitivity evidence only and cannot rescue or promote a mechanism.

`MECHANISM_RETAINS_DEVELOPMENT_INTEREST` requires every frozen gate:

- baseline and stress multi-asset `VALIDATED`
- positive baseline OOS return on both assets
- minimum windows and development trades
- OOS drawdown no greater than 20% under baseline and stress
- annualized baseline turnover no greater than 24 times initial capital
- annualized baseline cost no greater than 20% of initial capital
- exact protective policy active in every scenario and asset

`SCREEN_OUT` applies when baseline or stress is `REJECTED`, or when drawdown,
turnover, cost or protective-execution integrity fails. `INCONCLUSIVE` applies
when hard rejection is absent but evidence volume, persistence or another gate
is incomplete.

Retained development interest is not validation or selection. The fixed
ablation order is descriptive and no score, rank or tie-break exists.

## One-shot atomic evidence

Before computation the runner requires exact manifest and attribution hashes,
dataset and asset scope, variant order, strategy parameters, configuration and
absence of final/staging evidence. All nine evaluations finish before staging.
Canonical JSON and its SHA-256 sidecar are renamed into place together.
Existing final or staging evidence blocks a repeat.

## Controlled command after repository integration

Run exactly once only after focused/full Windows reproduction, commit/push and
an explicit absent-evidence preflight:

```powershell
python src/alpha_development_runner.py `
    --manifest data/research/first_candidate_v1/manifest.json `
    --attribution-report data/research/strategy_failure_attribution_v1/attribution_v1/failure_attribution_report.json
```

The command writes canonical report and checksum files below
`data/research/alpha_development_v2/development_v2/`.

The run summary always retains ranking, selection, calibration, Candidate v2,
optimization, PAPER and live authorization as false. Cloud services remain
parked.
