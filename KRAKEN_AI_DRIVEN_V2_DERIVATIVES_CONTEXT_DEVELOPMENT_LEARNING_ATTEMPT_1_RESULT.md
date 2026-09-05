# Kraken AI-Driven V2 Derivatives Context Development Learning Attempt 1 Result

## Immutable evidence identity

- Execution commit: `4e3867dfadc9795ca39e24ebafc7f405d40f3c8d`
- Protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-derivatives-context-development-learning-runner-v1`
- Run ID: `kraken-ai-v2-derivatives-context-development-learning-v1`
- Report SHA-256:
  `bddb6f7c0a9b056dcf8a4ca79fc3b8128dbf4ded4aac47e19022a84222215fb4`
- Context dataset manifest SHA-256:
  `db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`
- Partition: Development, 12h, common interval 2021-12-01 through
  2024-04-01 exclusive.

The final atomic evidence contains sixteen files, twelve model artifacts and
8,468 exact out-of-fold predictions. The independent reader verified every
report, prediction and model byte without unpickling a model. It recorded
`KRAKEN_AI_V2_DERIVATIVES_CONTEXT_LEARNING_EVIDENCE_READER_PASS`.

## Result

The run built 3,793 context-complete labeled rows and trained exactly twelve
fold models. Its terminal learning status is
`KRAKEN_AI_V2_DERIVATIVES_CONTEXT_NO_VIABLE_HYPOTHESIS_HOLD_CASH` and its action
is `HOLD_CASH`.

Neither context hypothesis passed the frozen absolute after-cost gates:

- the context classifier selected zero eligible rows;
- the context net-R regressor selected zero eligible rows;
- the spot-only classifier control selected 130 raw and 27 non-overlapping
  rows for `-15.13457371200541 R`; and
- the spot-only net-R control selected five raw and one non-overlapping row for
  `-1.0 R`.

Both context variants improved their frozen predictive comparisons and their
zero-selection outcome exceeded losing controls, so their incremental gates
passed. That is not evidence of an executable strategy: zero selections cannot
satisfy the absolute support, fold, asset-breadth or positive-net-R gates.

## Decision boundary

No hypothesis is promoted. Automatic model selection, threshold search,
Calibration, Evaluation, Candidate v2, PAPER, cloud, real orders and live
execution remain unauthorized.

The only next action is a hash-bound, read-only score-forensic review of the
same immutable out-of-fold predictions. It may diagnose ranking shape, fold
stability, event duration and class support. It may not refit models, select a
threshold, modify evidence or automatically choose Experiment 2.
