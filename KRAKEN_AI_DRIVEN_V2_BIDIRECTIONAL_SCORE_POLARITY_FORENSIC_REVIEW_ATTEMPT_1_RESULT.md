# Kraken AI-Driven V2 Bidirectional Score and Polarity Forensic Review Attempt 1 Result

## Immutable execution identity

- execution commit: `8f51ab4f52725ab7529009a0f9fcc934a3159f69`;
- source learning report SHA-256:
  `7176ca3a005b7bdbfbdcbc2259fafd11c154ee45b0517eab26894e675aa26b3f`;
- source evidence files: 16;
- source evidence bytes: 7,161,889;
- forensic evidence inventory SHA-256:
  `25e0bae8ee3f3d29e80b095019974071d192c9be84e80cbd33c27b5d623853ad`;
- status: `KRAKEN_AI_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_PASS`;
- learning status: `KRAKEN_AI_V2_BIDIRECTIONAL_NO_VIABLE_HYPOTHESIS_HOLD_CASH`;
- source evidence unchanged: true;
- model artifacts unpickled: false;
- model training executed: false;
- threshold search executed: false;
- polarity flip simulated: false;
- Calibration opened: false;
- Evaluation opened: false;
- Candidate v2 authorized: false;
- real orders submitted: false.

## Verified implementation boundary

The authorized read-only review reconstructed every recorded LONG, SHORT and
`HOLD_CASH` action with zero mismatches. It validated the polarity of both
directional label families and verified identical context/control outcome rows.
It inspected 3,793 labeled decisions, 7,586 directional labels and 4,210 OOF
prediction rows without changing the sixteen-file evidence lock.

## Human interpretation

The review found no retrospective rescue for the frozen bidirectional
hypothesis. SHORT scores were materially optimistic and weakly associated with
realized outcomes. A positive SHORT score was not an 89% success prediction:
680 of 765 positive context SHORT scores and 602 of 674 positive control SHORT
scores were false positives.

| Variant and direction | Score/outcome Spearman | Positive scores | False positives | Top-decile mean net R | Positive every fold |
|---|---:|---:|---:|---:|---|
| Spot-only LONG | 0.180936 | 37 | 30 | -0.333333 | false |
| Spot-only SHORT | 0.151376 | 674 | 602 | -0.600852 | false |
| Spot+context LONG | 0.125449 | 29 | 25 | -0.183210 | false |
| Spot+context SHORT | 0.107854 | 765 | 680 | -0.586292 | false |

Some coarse score ordering existed, but no direction/variant had a profitable
overall top decile in every fold. Context improved the frozen non-overlapping
policy mean from `-0.738814 R` to `-0.656794 R`, yet both variants remained
negative in every fold and asset. This is diagnostic information, not alpha.

## Decision

The frozen 12h bidirectional hypothesis is closed with `HOLD_CASH`.
There is no threshold reinterpretation, top-decile rescue, score-sign flip,
refit or promotion. Calibration, Evaluation, Candidate v2, PAPER, cloud, real
orders and live execution remain closed.

Any future work requires a separately pre-registered, materially different and
bounded Development hypothesis. It is not authorized by this result. The next
hypothesis must have an explicit research stop condition so this failed branch
cannot continue through incremental threshold or indicator changes.
