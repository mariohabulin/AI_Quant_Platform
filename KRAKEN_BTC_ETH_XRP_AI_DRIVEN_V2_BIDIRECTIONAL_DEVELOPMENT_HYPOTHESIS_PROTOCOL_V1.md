# Kraken BTC/ETH/XRP AI-Driven V2 Bidirectional Development Hypothesis V1

## Purpose and prior evidence

Protocol ID:
`kraken-btc-eth-xrp-ai-v2-bidirectional-development-hypothesis-v1`.

The completed Context Score Forensic Review Attempt 1 closed the prior
long-only derivatives-context hypothesis with `HOLD_CASH`. Both context score
families had negative overall rank association, every score decile lost net R
and no top decile was positive in every fold. This protocol permits one
materially different question: can the same causal information distinguish
profitable `LONG`, profitable `SHORT` and `HOLD_CASH` decisions?

This is a Development-only pre-registration. It opens no Kraken archive,
derivatives dataset, model artifact, Calibration or Evaluation data and trains
no model.

## Frozen information set

No indicator is added or tuned. Every decision uses the existing 16 causal
spot features plus asset identity. The matched context variant adds the
existing nine causal derivatives features. Thus the numeric schemas remain
exactly 16 and 25 features.

Spot features cover signed returns, ATR fraction, realized volatility, EMA
distances and spread, relative volume, prior 20-bar high/low distance, RSI,
same-time market return and BTC return. Context features remain funding level,
mean and z-score; open-interest changes and z-score; and basis level, change
and z-score. A feature is an input, never a hard-coded buy or sell rule.

## Symmetric outcome contract

For every eligible completed 12h decision bar, two outcomes are created from
the same next-open entry and future path:

- `LONG`: buy then sell;
- `SHORT`: sell then buy to cover.

Both directions keep the existing 60-bar (30-day) horizon, `1.5 × ATR-14` risk
unit, `3R` target, `1R` stop, baseline adverse commission, half-spread and
slippage. Gap opens use their adverse executable price. If stop and target are
both touched in one bar, stop wins. Provider gaps and insufficient right-edge
history censor both directions. No row is filled or repaired.

Short cash flow is explicit: entry proceeds use the adverse sell fill and
commission; exit cost uses the adverse buy fill and commission. Net short R is
`(entry proceeds - cover cost) / risk unit`.

## Frozen learners and action

Exactly two direct expected-net-R variants are allowed:

1. `SPOT_ONLY_BIDIRECTIONAL_HIST_GBT_NET_R_CONTROL`;
2. `SPOT_CONTEXT_BIDIRECTIONAL_HIST_GBT_NET_R`.

Each variant fits one LONG and one SHORT histogram-gradient-boosting regressor
inside each of the existing three 30-day-purged expanding folds. The maximum
is therefore twelve fold-direction model fits. There is no classifier, new
model family, hyperparameter sweep, feature search or threshold sweep.

For one asset/timestamp, the action is the larger of predicted LONG and SHORT
net R only when it is strictly above `0.0 R`. A nonpositive maximum or an exact
positive tie returns `HOLD_CASH`. The action rule is fixed before real value
access.

## Frozen evidence gates

Each bidirectional variant must independently satisfy:

- at least 30 raw and 10 chronological non-overlapping selections per fold;
- positive non-overlapping cumulative and mean net R in every fold;
- positive overall non-overlapping net R;
- positive non-overlapping net R on at least two of three assets; and
- deterministic row, direction and event-identity validation.

The spot-only variant is an absolute bidirectional control and may provide
Development evidence if every absolute gate passes. The context variant must
pass every absolute gate and also beat the spot-only variant in overall mean
net R, worst-fold mean net R and at least two fold means. No winner is selected
automatically. A Development passer requires human review and later separate
Calibration authorization; it is not Candidate v2.

## Safety and next step

Implementation may use synthetic fixtures only. A separate hash-bound runner
is required before any real Development labels or fitting. Calibration,
Evaluation, Candidate v2, PAPER, cloud, real orders and live execution remain
unauthorized.
