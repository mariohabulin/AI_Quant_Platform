# Trend Pullback Volume Runner v1

## Status

This component is a reviewed one-shot development runner for the exact
four-member Trend Pullback and Volume Re-expansion Protocol v1. It does not
execute when imported or declared. It may run only after locking, in the same
process:

- native six-hour BTC-USD and ETH-USD manifest SHA-256
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`;
- closed Alpha Discovery report SHA-256
  `2fc8f4d1a5d690c072408bc2d299516904feb58b2e2f40345983641bf26ed678`;
- exact protocol configuration; and
- catalog SHA-256
  `952046ddb7a9f9a85a8976f3ccafe43a017a745c887e592a44c39c2146ba8e00`.

Any identity, asset, timeframe, configuration, evidence or window drift fails
closed.

## Exact execution contract

The runner uses seven chronological outer windows with 5,760 training rows,
720 test rows and a 720-row step. Each outer decision receives at most four
prior inner validation windows built from 2,880 training rows, 720 validation
rows and a 720-row step.

Across the complete dataset there are ten unique inner validation windows.
Each is evaluated for:

- all four immutable parameter sets;
- Coinbase baseline and Coinbase stress costs; and
- both BTC-USD and ETH-USD in the same multi-asset result.

This produces 80 complete inner multi-asset evaluations. Repeated references
to an already completed inner window reuse its immutable evidence rather than
rerunning it.

## Selection isolation

Selection receives the complete catalog in exact declaration order and only
inner validation metrics available before the relevant outer-test boundary.
It has no API input for outer evidence.

Every asset must pass:

- positive baseline median return;
- nonnegative stressed median return;
- at least 60% positive baseline and stressed inner windows;
- at least 12 completed trades;
- at most 20% drawdown;
- at most 12x annual turnover;
- at most 10% annualized baseline execution cost; and
- active exact protective-exit policy.

If no configuration passes all gates on both assets, the action is
`HOLD_CASH`. In that case the runner performs no outer strategy evaluation.
If one or more pass, deterministic selection uses worst-asset stress return,
then worst-asset baseline return, then lower turnover and finally frozen
catalog order. Only the selected member is evaluated on that outer window.

There is no global hindsight leaderboard and no outer result can change a
later parameter definition or selection rule.

## Risk and execution

Every evaluation uses:

- initial capital USD 5,000;
- following-bar Open execution;
- 0.50% current-equity risk per trade;
- maximum 50% position exposure;
- no leverage and no shorting;
- static 2 ATR initial risk distance;
- 3R target;
- conservative stop-first same-bar ordering; and
- no break-even ratchet.

Baseline and stressed Coinbase cost profiles are both required. The Risk
Engine retains 20% maximum drawdown, 2% daily-loss and 5% weekly-loss limits.

## Evidence boundary

Each window summary contains exact asset, phase, window ID and positions,
parameter identity, cost profile, return, drawdown, trades, annualized turnover
and cost, active protection proof and a SHA-256 over the complete canonical raw
partition. Raw trade histories and equity curves are not persisted in the
development report.

The final artifacts are:

- `data/research/trend_pullback_volume_v1/development_v1/`
  `trend_pullback_volume_report.json`; and
- the adjacent `trend_pullback_volume_report.sha256` sidecar.

They are written first to `.development_v1.staging` and renamed to the final
directory only after the complete procedure succeeds. Existing final or
staging evidence prevents another run.

## Authorization boundary

The report may state only whether the adaptive development procedure retains
descriptive research interest or screens out. It is not formal validation and
cannot authorize Candidate v2, optimization, bounded PAPER review, PAPER,
cloud deployment or live execution. Any future Candidate v2 requires a new
immutable preregistration and genuinely unseen validation data.
