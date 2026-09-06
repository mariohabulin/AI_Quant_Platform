# Kraken BTC/ETH/XRP AI-Driven V2 Bidirectional Score and Polarity Forensic Review V1

## Purpose and immutable input

Protocol ID:
`kraken-btc-eth-xrp-ai-v2-bidirectional-score-polarity-forensic-review-v1`.

This component diagnoses the completed bidirectional Development Attempt 1.
It reads only the independently verified evidence whose report SHA-256 is
`7176ca3a005b7bdbfbdcbc2259fafd11c154ee45b0517eab26894e675aa26b3f`.
The existing evidence reader must first verify the canonical report, OOF
predictions and all twelve model hashes without unpickling.

## Frozen integrity checks

The review requires exactly 3,793 labeled decisions, 7,586 directional labels,
4,210 OOF rows, two registered variants, three folds, three assets and both
LONG and SHORT outcomes on every matched row. Context and control rows,
timestamps, labels and realized directional outcomes must be identical.

Every recorded action is independently reconstructed. LONG requires a strictly
positive long prediction greater than the short prediction. SHORT requires the
strictly positive larger short prediction. A nonpositive maximum or exact
positive tie must be `HOLD_CASH`.

Label polarity is checked without recomputing labels: `TARGET_3R_FIRST` must
have positive net R and `STOP_1R_FIRST` must have negative net R for each
direction. Timeout outcomes only need to be finite because costs and exit price
can leave them on either side of zero.

## Frozen diagnostics

For each variant and direction, overall and by fold, the review records:

- prediction and realized-net-R distributions;
- mean prediction bias, MAE, RMSE, Pearson and Spearman association;
- positive-score and positive-outcome confusion counts;
- ten deterministic equal-count score deciles and top-decile economics;
- top-decile results independently inside every fold; and
- label support and realized outcome by label.

For each variant it also records the exact action counts, raw and chronological
non-overlapping selected economics, LONG/SHORT selection fractions, winning
score and directional-margin distributions, and the same economics by fold
and asset. These are measurements of the already frozen policy, not candidate
alternatives.

## Interpretation boundary

This is not a threshold, top-k, polarity-flip or model search. It does not
simulate a different decision rule, refit or unpickle a model, generate a
label, select an asset, compare new features or authorize Experiment 2.

A human review may distinguish only three next decisions: implementation
recovery if an integrity check fails; one separately pre-registered abstention
hypothesis if ranking evidence is stable; or closure of this 12h bidirectional
hypothesis if ranking evidence is unstable or economically negative. The
forensic component does not make that decision automatically.

Gross return, commission, spread and slippage are not present separately in
the OOF artifact, so cost decomposition is unavailable.

## Safety

Static review opens no evidence. External execution is read-only and writes no
report. Development evidence may be inspected; Calibration and Evaluation
remain unopened. Candidate v2, PAPER, cloud, real orders and live execution
remain unauthorized.
