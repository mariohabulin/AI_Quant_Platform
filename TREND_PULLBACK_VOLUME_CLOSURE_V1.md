# Trend Pullback Volume Development v1 Closure

## Closure status

The exact four-member Trend Pullback and Volume Re-expansion catalog is closed
as `SCREEN_OUT` on inspected development data.

Canonical evidence:

- report SHA-256:
  `7598ea3616a60753d5be5b4d7af8c146f1bea881cb2d43ed71ea16cebdd685e3`;
- runner revision: Windows `f8f9c42`;
- evidence revision: Windows `8b1560c`;
- outer windows: 7;
- selected outer windows: 0; and
- hold-cash outer windows: 7.

The report and sidecar were verified byte-for-byte. No staging directory
remained. Candidate v2, optimization, bounded PAPER review, PAPER and live
authorization are false.

## What was tested

The one-shot runner evaluated all four immutable combinations of:

- 0.5 or 1.0 ATR pullback distance; and
- 1.2 or 1.5 trigger relative volume.

Every combination retained causal completed-bar state, following-Open entry,
long-only bullish EMA structure, ADX 25/20/15 hysteresis, lagged 20-bar
relative volume, static 2 ATR protection, 3R target, 0.50% equity risk and no
leverage.

Ten unique inner validation windows were evaluated under baseline and stressed
Coinbase costs. Each of seven chronological outer decisions received only its
available prior inner evidence. No configuration was eligible, so all outer
actions were `HOLD_CASH` and no outer strategy evaluation occurred.

## Gate evidence

Across four parameter sets and seven selection boundaries, there are 28
parameter/boundary decisions.

Universal passes, 28/28:

- active exact protective policy;
- drawdown within 20%;
- annual turnover within 12x; and
- annualized baseline cost within 10%.

Universal failures, 0/28 passes:

- at least 12 inner trades per asset;
- positive baseline median return on both assets;
- at least 60% positive baseline inner windows; and
- at least 60% positive stressed inner windows.

Nonnegative stressed median return on both assets passed only 2/28 decisions.

## Interpretation

Four recent inner windows contain only 1–11 completed trades per asset. A
positive-window rate therefore moves in 25-point increments and never exceeds
50%, below the frozen 60% gate. The evidence is both too sparse and too
inconsistent to support selection.

The 1 ATR pullback generally increases trade count but worsens median returns.
The 0.5 ATR pullback produces fewer, less-negative results. In the last
selection boundary, shallow-pullback ETH reaches approximately +0.48% baseline
and +0.46% stress median return, while BTC is flat. The deeper variants retain
positive late ETH evidence but negative BTC evidence. This is descriptive
asset asymmetry, not validated edge.

Maximum observed window drawdown is approximately 2.04%. Selection-level mean
annual turnover is approximately 0.13x–1.28x and all cost budgets pass. Low
operational burden partly reflects low participation. It does not establish
profitability, but it shows that cost, turnover and uncontrolled drawdown are
not the controlling failures in this experiment.

The overall report's nonnegative stressed outer median is a hold-cash result:
seven zero-return outer decisions. It is not evidence that a strategy passed
stressed execution.

## What is closed

Closed:

- the literal four-member catalog;
- its fixed entry sequence and exit/risk combination as a selectable adaptive
  procedure; and
- any claim that these results authorize Candidate v2 or deployment.

Not closed:

- the broad economic idea of pullbacks within persistent trends;
- volume contraction/re-expansion as a diagnostic feature;
- asset-specific differences requiring causal explanation; or
- structurally different entry and exit mechanisms derived from new evidence.

No gate may be lowered and no least-bad member may be promoted to reverse the
recorded result.

## Next research boundary

Before defining another performance catalog, perform bounded trade-path
attribution on these exact inspected-development trades. The diagnostic must
measure:

- initial risk and realized R;
- maximum favorable and adverse excursion;
- stop, target, signal and terminal exit counts;
- holding bars and bars to maximum favorable excursion;
- whether 3R was approached but not captured;
- whether signal exits truncate favorable paths or avoid larger losses;
- shallow versus deep pullback behavior; and
- BTC versus ETH asymmetry.

This analysis may form a new falsifiable hypothesis. It cannot select a
parameter set, reopen this catalog, authorize optimization or substitute for
genuinely unseen validation data.
