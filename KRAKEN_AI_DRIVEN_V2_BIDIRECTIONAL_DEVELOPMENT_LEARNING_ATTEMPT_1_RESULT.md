# Kraken AI-Driven V2 Bidirectional Development Learning Attempt 1 Result

## Immutable execution identity

- execution commit: `ca1cd9186ecfac934d4ad84000da12c572d633a3`;
- run ID: `kraken-ai-v2-bidirectional-development-learning-v1`;
- partition: Development only;
- interval: 12h;
- assets: BTC-USD, ETH-USD and XRP-USD;
- directions: LONG and SHORT;
- final report SHA-256:
  `7176ca3a005b7bdbfbdcbc2259fafd11c154ee45b0517eab26894e675aa26b3f`.

The run used the exact Kraken archive and derivatives-context Dataset Lock
Attempt 4 established by the runner protocol. Source inputs were unchanged.

## Execution result

- status: `KRAKEN_AI_V2_BIDIRECTIONAL_DEVELOPMENT_LEARNING_EVIDENCE_RECORDED`;
- learning status: `KRAKEN_AI_V2_BIDIRECTIONAL_NO_VIABLE_HYPOTHESIS_HOLD_CASH`;
- action: `HOLD_CASH`;
- labeled decision rows: 3,793;
- directional labels: 7,586;
- out-of-fold prediction rows: 4,210;
- trained and locked model artifacts: 12;
- total evidence files: 16.

Both registered variants failed the absolute economic gates. The spot-only
control produced 153 chronological non-overlapping selections with mean
`-0.7388136995607325 R`. The context variant produced 154 with mean
`-0.6567936294655654 R`. All three folds and all three assets were negative.
The context variant improved two fold means and overall mean relative to the
control, but worsened the worst fold and did not pass any absolute
profitability or asset-breadth conclusion.

The selected actions were strongly asymmetric. The control selected 143 SHORT
and 10 LONG events; the context variant selected 148 SHORT and 6 LONG events.
This observation is diagnostic only and does not authorize a polarity change,
threshold change or another experiment.

## Independent evidence review

The existing independent evidence reader passed with the report hash above.
It verified the canonical report, all OOF prediction bytes, all twelve model
artifact hashes and their registry without unpickling a model. Evidence file
count, total bytes and inventory SHA-256 were unchanged before and after the
review.

## Boundary and next step

Attempt 1 is consumed and must not be repeated. The result promotes no model
and opens no Calibration, Evaluation, Candidate v2, PAPER, cloud, real-order
or live boundary.

The only next action is a separately implemented read-only score and polarity
forensic review bound to the exact report hash. It may diagnose prediction
sign, ranking, calibration and action asymmetry, but it may not refit, unpickle,
simulate thresholds or automatically select another experiment.
