# Kraken BTC/ETH/XRP AI-Driven V2 Alpha Research Lab Protocol V1

## Frozen purpose

Protocol ID: `kraken-btc-eth-xrp-ai-driven-v2-alpha-research-lab-v1`

The Alpha Research Lab is the single active Development experimentation loop.
It replaces one-component-per-experiment ceremony. Development may be read,
modeled and compared repeatedly inside this one bounded run. Calibration and
Evaluation remain sealed.

The 12h Learning Core V1 economic result is an immutable negative benchmark:
`KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_HOLD_CASH`. Its learned evidence
report SHA-256 is
`30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf`.

## Data, labels and costs

- assets: BTC-USD, ETH-USD and XRP-USD;
- resolution: native Kraken 12h;
- Development: 2019-01-01 through 2024-04-01 exclusive;
- input: the existing 16 causal market-context features plus asset identity;
- outcome: the already cost-aware next-open `outcome_net_r` and its
  target/stop/timeout class;
- Calibration and Evaluation: prohibited.

The timeframe, label geometry, adverse baseline costs, feature schema and
outer folds cannot change inside this lab version.

## Exactly six variants

The lab executes every registered variant; it cannot stop after finding an
attractive result.

### Calibrated natural-frequency classification

1. natural multinomial logistic regression;
2. histogram gradient-boosted classifier;
3. extra-trees classifier.

No classifier uses balanced class weights. Each outer training window is split
chronologically: the earlier portion fits the base learner and the later
purged portion fits a multinomial probability calibrator. The fixed economic
score is `3 * P(target) - P(stop)` and eligibility requires a value above zero.

### Direct expected-net-R learning

4. ridge net-R regressor;
5. histogram gradient-boosted net-R regressor;
6. extra-trees net-R regressor.

The same chronological inner split fits a base regressor and a linear mapping
from its later inner predictions to realized net R. Eligibility requires the
calibrated expected net R to be above zero.

## Nested chronological boundary

The three existing outer walk-forward folds remain fixed. Inside each outer
training window, the first 75% of unique decision timestamps is the base-fit
region and the final 25% is the calibration region. An event must end before
the boundary it belongs to. Outer validation never fits the base model,
preprocessor or calibrator that predicts it.

## Frozen economic gates and ranking

Every variant is evaluated with both all eligible decisions and a chronological
view allowing at most one open event per asset. Development viability requires:

- at least 30 raw and 10 non-overlapping eligible decisions in every fold;
- positive cumulative and mean non-overlapping net R in every outer fold;
- positive cumulative net R on at least two of three assets; and
- positive cumulative and mean non-overlapping net R overall.

Among variants passing every gate, deterministic Development ranking maximizes
worst-fold mean net R, then overall mean net R, then uses the frozen registry
order. This selects only a Development research winner. It does not authorize
Candidate v2.

If no variant passes, the 12h OHLCV hypothesis closes with `HOLD_CASH`; there is
no seventh variant. If one passes, it is frozen before any Calibration access.
No Development result may be described as untouched out-of-sample evidence
because V1 results have already informed this one allowed correction.

## Permanent boundary

- variant count: exactly six;
- hyperparameter or threshold sweep: prohibited;
- AutoML and runtime learning: prohibited;
- automatic Candidate promotion: prohibited;
- Calibration and Evaluation access: prohibited;
- PAPER, cloud, real orders and live execution: prohibited.
