# Kraken AI-Driven V2 Context Score Forensic Review Attempt 1 Result

## Immutable execution identity

- execution commit: `bde314d47e30804a7380493f959f61e8f3a40212`;
- source learning report SHA-256:
  `bddb6f7c0a9b056dcf8a4ca79fc3b8128dbf4ded4aac47e19022a84222215fb4`;
- forensic report SHA-256:
  `ed4ee096a9d45eee4d1ee0970dbb062473e74c9caad3597f20eda17cb4dba91f`;
- status: `KRAKEN_AI_V2_CONTEXT_SCORE_FORENSIC_REVIEW_PASS`;
- source evidence unchanged: true;
- model artifacts unpickled: false;
- model training executed: false;
- threshold sweep executed: false;
- Calibration opened: false;
- Evaluation opened: false;
- Candidate v2 authorized: false;
- real orders submitted: false.

## Human interpretation

The read-only review found no stable hidden long-only alpha. Both context score
families had negative overall score/outcome rank association, zero positive
scores and negative economics in every equal-count score decile. The apparent
incremental predictive wins only compared one losing representation with
another and do not satisfy an absolute trading gate.

| Context variant | Overall Spearman | Decile-mean Spearman | Top-decile non-overlap mean net R | Positive every fold |
|---|---:|---:|---:|---|
| `SPOT_CONTEXT_HIST_GBT_CLASSIFIER` | -0.041083 | 0.006061 | -0.683682 | false |
| `SPOT_CONTEXT_HIST_GBT_NET_R` | -0.037840 | -0.187879 | -0.990291 | false |

The classifier top decile contained 37 non-overlapping events for `-25.2962 R`.
The net-R regressor top decile contained 66 for `-65.3592 R`. Neither ranking
was stable across folds or assets. Fold class support was also dominated by
`STOP_1R_FIRST`: `467/496`, `655/704` and `738/917` validation rows.

## Decision

The frozen derivatives-context long-only hypothesis is closed with
`HOLD_CASH`. There is no threshold reinterpretation, top-k rescue, refit or
automatic Experiment 2. One separately pre-registered bidirectional
Development hypothesis may test whether the constrained long-only action space
was the material limitation while keeping features, costs, horizon and folds
unchanged.
