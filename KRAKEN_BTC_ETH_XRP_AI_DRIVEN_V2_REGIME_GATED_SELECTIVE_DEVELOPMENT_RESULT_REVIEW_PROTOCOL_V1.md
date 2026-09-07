# Kraken BTC/ETH/XRP AI-Driven V2 Regime-Gated Selective Result Review V1

## Purpose and binding

Protocol ID:
`kraken-btc-eth-xrp-ai-v2-regime-gated-selective-development-result-review-v1`.

This read-only review binds the one valid Development result executed from
commit `40d9811`. It accepts only report SHA-256
`a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286`
and prediction SHA-256
`728b60750ed9de5070281d8d3cebecddbef701f2f6ea604dbeec7c2ea7015400`.

## Independent checks

The review hashes the canonical report, predictions, sidecars and all declared
model bytes. Model artifacts are never unpickled. It independently validates:

- the exact terminal status, `HOLD_CASH` action and empty passer registry;
- 3,793 labeled decisions and 291 OOF prediction rows;
- exactly two supported direction-fold cells and ten fail-closed cells;
- exactly two base models and two sigmoid calibrators;
- the probability-threshold action on every OOF row;
- per-cell row counts, calibrated Brier scores and prevalence comparisons;
- zero selected rows, zero positive assets and every frozen gate failure; and
- unopened Calibration/Evaluation plus all nonauthorization boundaries.

The review may read JSON and hash opaque `.pkl` bytes. It may not load an
estimator, generate labels, fit, recalibrate, change a threshold, rank an
alternative, search a successor or write into the evidence directory.

## Terminal decision

The valid result is
`KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_NO_VIABLE_HYPOTHESIS_STOP_KRAKEN_12H_RESEARCH`.
Both variants selected zero rows. The context variant produced no supported
direction-fold cell; the control produced OOF predictions only for SHORT in
folds 1 and 2, and every probability remained below its frozen payoff threshold.

This is a valid economic result, not a technical incident. It consumes the
one-shot authorization and terminates the Kraken BTC/ETH/XRP 12h research
branch. No retry, recovery, refit, threshold relaxation, new indicator or
automatic successor is permitted.

Calibration, Evaluation, Candidate v2, PAPER, cloud, real orders and live
execution remain unauthorized.
