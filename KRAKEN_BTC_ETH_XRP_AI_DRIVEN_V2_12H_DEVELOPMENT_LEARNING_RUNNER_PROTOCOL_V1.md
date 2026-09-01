# Kraken BTC/ETH/XRP AI-Driven V2 12h Development Learning Runner Protocol V1

Protocol ID:
`kraken-btc-eth-xrp-ai-driven-v2-12h-development-learning-runner-v1`

Run ID:
`kraken-ai-v2-12h-development-learning-v1`

Parent implementation commit: `2a09363`.

## Purpose

This is the first component authorized to turn real Kraken Development OHLCV
into learned AI-Driven V2 model parameters. It is not another manual strategy
round. It calls the frozen causal feature, cost-aware label and walk-forward
model code from Learning Core V1.

The implemented component is inert. A run requires a separate exact operator
authorization:

`EXECUTE_KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_ONCE`

Reviewing, testing, committing or downloading this component does not activate
that phrase.

## Frozen source and partition

The only accepted source is:

- filename: `Kraken_OHLCVT.zip`;
- bytes: `7885068519`;
- SHA-256: `e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d`.

The reader requires exactly one member with each basename:

- `XBTUSD_720.csv` for `BTC-USD`;
- `ETHUSD_720.csv` for `ETH-USD`;
- `XRPUSD_720.csv` for `XRP-USD`.

Only rows in Development
`[2019-01-01T00:00:00Z, 2024-04-01T00:00:00Z)` may have OHLCV values parsed.
Rows outside that interval may have their timestamp token read to verify member
ordering and to hash opaque member bytes; their market-value columns remain
unparsed.

Expected Development rows are 3,833 BTC, 3,834 ETH and 3,830 XRP. The reader
does not fill the one BTC or four XRP missing 12h buckets. Frame validation
rejects malformed timestamps, non-finite values, nonpositive prices, negative
volume and invalid OHLC geometry.

Calibration and Evaluation market values remain unopened.

## Fixed learning operation

After source validation, the runner performs exactly this operation:

1. build the 16 frozen causal features and asset identity;
2. generate next-open adverse-cost `3R/-1R/30-day` triple-barrier labels;
3. record valid labels and censoring reasons by asset;
4. measure all three class counts in each fixed training and validation fold;
5. if every fold has at least 30 training and 10 validation examples per class,
   fit `LOGISTIC_BASELINE` and `HIST_GBT_CHALLENGER` independently in each fold;
6. record out-of-fold probabilities and predictive metrics; and
7. persist the six fitted fold-model pickle artifacts.

Each fold creates a new preprocessing/model pipeline. Training events must end
before the fold boundary. Validation data never refits the model that predicts
it.

If any fold lacks required class support, model fitting does not start. The run
still closes atomically with status
`KRAKEN_AI_V2_12H_DEVELOPMENT_CLASS_SUPPORT_INSUFFICIENT_HOLD_CASH`, zero model
artifacts and zero out-of-fold predictions. The criterion is not weakened and
the same attempt is not silently repeated.

## Immutable evidence

The final external evidence directory is
`v2_12h_development_learning_v1`; staging is
`.v2_12h_development_learning_v1.staging`.

The evidence package contains:

- canonical JSON report and SHA-256 sidecar;
- canonical out-of-fold prediction JSON and SHA-256 sidecar;
- zero models for the class-support `HOLD_CASH` branch, or exactly six learned
  `.pkl` fold-model artifacts for a completed training branch;
- complete-archive identity;
- decompressed member-byte SHA-256, timestamp-identity SHA-256 and row counts;
- Learning Core configuration and component hashes;
- labeled-table identity SHA-256, censoring/label diagnostics and fold support;
- predictive metrics and exact artifact manifests; and
- explicit negative authorization fields.

All content is written under staging and renamed to final only after complete
serialization. Existing final or staging evidence blocks a repeat. The
independent lock rehashes every file, validates the exact file manifest and
does not unpickle learned artifacts.

## Deliberate nonselection

This runner produces evidence; it does not declare alpha or choose a winner.
No decision threshold, automatic ranking, automatic model selection or
Candidate promotion occurs in the run. Economic decision/stress review follows
only from the recorded out-of-fold evidence and remains a separate read-only
milestone.

## Prohibitions

This protocol does not authorize:

- Calibration or Evaluation access;
- an additional resolution or strategy search;
- automatic model ranking or promotion;
- Candidate v2 status;
- PAPER, cloud or runtime learning;
- real orders or live execution; or
- deletion, overwrite or rerun of prior evidence.

The safe action is always `HOLD_CASH` when learning cannot produce reviewable
evidence.
