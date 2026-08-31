# Kraken AI-Driven V2 Scope-Gap Correction V1

## Why this correction exists

The project goal was described as a system that learns from market context and
improves a versioned strategy from feedback. The implementation delivered so
far is a strong, bounded and auditable rule-research foundation, but its
parameters were written by us. Calling that mechanism a learning engine was
incorrect.

True Learning Engine is not implemented. This document records that fact
without rewriting historical, hash-bound protocols or evidence.

## What has actually been built

The existing components provide:

- locked Kraken BTC, ETH and XRP data partitions;
- causal feature, state and risk/execution contracts;
- deterministic simulation with baseline and stress costs;
- immutable evidence, report hashes and one-shot authorization boundaries;
- bounded Round 1 and Round 2 rule discovery; and
- safe `HOLD_CASH` behavior when no route passes.

Together these components are the **Rule Discovery Foundation**. They remain
useful input infrastructure and historical evidence. Rule Discovery Foundation
is not a Learning Engine because it does not fit model parameters from labeled
market examples, produce an independently versioned learned model artifact or
change a challenger reproducibly from recorded training feedback.

## What the True Learning Engine must do

The learning system must learn parameters offline from Development data. Its
initial supervised target will be defined before training in plain language;
the proposed target is the probability that a causal entry context reaches a
frozen positive reward boundary before a frozen loss boundary within a frozen
horizon. Exact label, ambiguity and no-event handling belong to the True
Learning Contract, not to an improvised training script.

Inputs may include only information available at the decision timestamp:
returns and momentum, trend and structure, volatility and ATR-normalized
distance, relative volume, causal support/resistance, market regime and asset
identity. The model must output a calibrated score or probability plus enough
metadata to reconstruct the exact feature, label and training versions.

The system uses offline learning and versioned artifacts. Runtime may select only an already
approved immutable model; it may not mutate weights, retrain itself, promote a
challenger, send real orders or open Calibration/Evaluation.

## Required stages

### Stage 0 — close evidence and correct scope

Close Round 2 against the exact report SHA-256, preserve `HOLD_CASH`, prohibit a
rerun and rename the existing subsystem to Rule Discovery Foundation. This is
the current stage.

### Stage 1 — freeze the True Learning Contract

Specify prediction timestamp, label, horizon, feature availability, missing
data behavior, model families, training budget, deterministic seeds, metrics,
walk-forward rules, cost application and rejection criteria. No dataset is
opened and no model is trained during contract review.

### Stage 2 — audit data sufficiency and resolution

Measure how many independent labeled examples each candidate resolution can
support after causality, gaps and horizon rules. Daily, 12-hour, 8-hour, 6-hour
or another source-native resolution is selected from sufficiency and leakage
constraints, not because an earlier hand-written strategy used it.

### Stage 3 — implement the offline Learning Engine

Build deterministic Development-only feature/label generation, bounded model
training, later-period prediction, calibration diagnostics and serialization of
a learned model artifact with SHA-256 identity. Unlimited AutoML and unbounded
parameter search remain prohibited.

### Stage 4 — Development walk-forward learning

Train only on earlier Development rows and predict later Development rows over
multiple chronological folds. Record prediction-level evidence, costs,
stability across assets/regimes and all rejected candidates. Feedback may create
a new versioned challenger only through a new pre-registered run.

### Stage 5 — freeze Candidate v2

If and only if Development gates pass, freeze one complete candidate: feature,
label, model, threshold, execution, risk, costs and artifact hashes. Otherwise
the valid outcome remains `HOLD_CASH` or a separately authorized new hypothesis.

### Stage 6 — one-time Calibration

Open only the frozen Calibration partition (`2024-04-01` inclusive to
`2025-04-01` exclusive) once. Calibration may validate or reject the candidate;
it may not become a tuning loop.

### Stage 7 — untouched Evaluation

Only a Calibration-approved frozen candidate may open Evaluation
(`2025-04-01` inclusive to `2026-04-01` exclusive) once. This is the final
historical generalization test, not training data.

### Stage 8 — bounded PAPER and challenger/champion learning

Only an Evaluation-approved candidate may enter bounded PAPER. New feedback is
stored immutably and may later train an offline challenger. Promotion requires a
separate review and explicit operator decision; production never self-modifies.

## Acceptance boundary

The system may be called a True Learning Engine only when all of these are true:

1. model parameters are learned from labeled Development examples;
2. training is causal, chronological and reproducible from frozen inputs;
3. the learned model artifact and its metadata have deterministic hashes;
4. predictions are generated on rows not used to fit that model instance;
5. recorded feedback can reproducibly create a different versioned challenger;
6. leakage tests prove that future, Calibration and Evaluation data are absent;
7. runtime models remain immutable; and
8. Candidate v2 promotion is explicit and separately authorized.

Until then, the honest status is: Rule Discovery Foundation complete, True
Learning Engine pending, Candidate v2 unauthorized.
