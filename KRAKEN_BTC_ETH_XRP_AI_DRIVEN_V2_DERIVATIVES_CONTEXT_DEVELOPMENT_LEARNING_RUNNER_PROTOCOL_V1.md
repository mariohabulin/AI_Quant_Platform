# Kraken BTC/ETH/XRP AI-Driven V2 Derivatives Context Development Learning Runner V1

## Purpose and immutable inputs

Protocol ID:
`kraken-btc-eth-xrp-ai-v2-derivatives-context-development-learning-runner-v1`

This runner executes only the four-variant experiment pre-registered by
`kraken-btc-eth-xrp-ai-v2-derivatives-context-learning-hypothesis-v1`.
It binds:

- Kraken native 12h spot execution and outcomes to the existing complete
  archive hash;
- the derivatives-context lock to manifest SHA-256
  `db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`;
- the final independent Dataset Lock Attempt 4 pass;
- the frozen hypothesis protocol, component and static review; and
- implementation parent commit
  `9b23d05eed043c92205e7a2ca62c70312f6b6e8f`.

The common Development interval is 2021-12-01 through 2024-04-01 exclusive.
Calibration and Evaluation remain unopened.

## Frozen learning table

Kraken spot features and cost-aware 3R/1R/30-day next-open labels are rebuilt
from the locked archive. Derivatives features are rebuilt from the independently
verified context lock. Rows outside the common interval are removed.

Exactly nine context features are joined by asset and decision timestamp to
the unchanged sixteen spot features. Rows missing any causal context feature
are removed. Every control and context variant receives the identical ordered
set of context-complete outcome rows. Controls cannot obtain a larger sample.

## Causal folds and fitting

The three pre-registered expanding folds and 30-day purge are unchanged. Each
outer training interval is divided chronologically: the earlier 75% of unique
decision times fits the base learner and the later purged portion fits only its
calibrator. An outcome must finish before the boundary of the data that uses
it. Outer validation fits nothing.

Exactly four variants execute in this order:

1. `SPOT_ONLY_HIST_GBT_CLASSIFIER_CONTROL`;
2. `SPOT_CONTEXT_HIST_GBT_CLASSIFIER`;
3. `SPOT_ONLY_HIST_GBT_NET_R_CONTROL`; and
4. `SPOT_CONTEXT_HIST_GBT_NET_R`.

The matched classifier pair uses the same frozen histogram-GBT and multinomial
probability-calibration parameters. The matched regressor pair uses the same
frozen histogram-GBT and linear score-calibration parameters. The only paired
difference is whether the nine registered context columns are available.
There is no hyperparameter, feature, learner or threshold sweep. The fixed
economic threshold is predicted net R greater than zero.

## Evidence and gates

The run persists twelve base-model/calibrator artifacts, all out-of-fold
predictions, row identities, predictive metrics, economic summaries and
SHA-256 values in one new atomic evidence directory. SHA-256 sidecars are
binary-written ASCII with one canonical LF byte on every operating system. A
separate read-only mode verifies every persisted byte without refitting.

Each context hypothesis must independently pass all absolute gates:

- at least 30 raw and 10 non-overlapping selections in every fold;
- positive mean and cumulative non-overlapping net R in every fold;
- positive cumulative net R on at least two assets; and
- positive mean and cumulative non-overlapping net R overall.

It must also pass every incremental gate against its matched control:

- higher overall mean net R;
- higher worst-fold mean net R, treating an empty control fold as 0.0 R; and
- better primary predictive evidence in at least two folds.

Classifier predictive wins mean lower multiclass log loss. Target PR-AUC is
diagnostic. Regressor predictive wins mean lower net-R mean absolute error.
Spearman correlation is diagnostic. Controls are never eligible for promotion.

If neither context hypothesis passes every gate, the result is `HOLD_CASH` and
the registered derivatives-context bundle closes. If one or both pass, the
result requests human review of the passing Development hypotheses; it does
not automatically select or promote one.

## One-shot authorization and safety

Implementation and declaration are inert. Real Development access and fitting
require the exact, separate phrase:
`EXECUTE_KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_ONCE`.

The run must use a new external evidence root and refuses existing final or
staging output. It performs no network download and never modifies either
input lock.

Automatic model selection, threshold search, Calibration, Evaluation,
Candidate v2, PAPER, cloud execution, real orders and live execution remain
unauthorized.
