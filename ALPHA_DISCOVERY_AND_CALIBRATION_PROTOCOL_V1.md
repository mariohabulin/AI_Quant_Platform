# Alpha Discovery and Calibration Protocol v1

## Purpose

This protocol turns the closed Alpha Development v2 result into a bounded,
live-equivalent discovery procedure. It is designed to answer two questions:

1. Does the closed v2 mechanism retain any gross signal before costs, and what
   do winning and losing trade paths reveal about entry and exit quality?
2. Can a small pre-declared parameter catalog be selected using only prior
   chronological evidence and then behave persistently on untouched outer
   development windows?

The protocol is development research, not formal candidate validation. It
cannot create Candidate v2, authorize optimization outside its exact catalog,
start PAPER, activate cloud services or enable live execution.

## Evidence boundary

The declaration locks:

- native Coinbase BTC-USD and ETH-USD six-hour data manifest SHA-256
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`
- closed Alpha Development v2 report SHA-256
  `19627f7002fc3159729ea61d22ead0fa25deca455612764121ea96fd3eaf71a0`
- all three Alpha v2 outcomes as `SCREEN_OUT`
- zero retained v2 mechanisms
- the exact v2 passed and failed gate basis

The dataset is explicitly `INSPECTED_DEVELOPMENT_ONLY`. Neither inner nor outer
results from this procedure may later be described as genuinely unseen formal
candidate evidence.

## Phase 1 — diagnostic replay

Before calibrating anything, a future separately reviewed runner must replay
the exact three closed v2 variants at zero modeled cost and derive bounded
trade-path evidence:

- maximum favorable excursion in initial-risk units
- maximum adverse excursion in initial-risk units
- realized return in initial-risk units
- holding bars
- bars to maximum favorable excursion
- signal, stop, target or terminal exit reason

Zero-cost evidence may attribute residual gross signal but may not select a
parameter set, rescue v2 or authorize deployment. Raw trade paths are used to
derive summaries and hashes but are not persisted in the canonical report.

## Phase 2 — fixed parameter catalog

The complete catalog contains exactly eight configurations:

```text
2 ADX entry/exit hysteresis bands
x 2 ATR initial-risk distances
x 2 protective-management modes
= 8 parameter sets
```

The ADX bands are `20/15` and `25/20`. Initial risk is `1.5 ATR` or `2 ATR`.
Protective management is either the existing static 3R target or a completed-
bar transition to break-even after reaching +1R while retaining the 3R target.

Every configuration shares these non-calibrated causal conditions:

- ADX and ATR period 14
- `BULLISH_NORMAL` market regime
- mandatory `HIGH` relative volume against a one-bar-lagged 20-bar baseline
- close above EMA 200 and positive four-bar EMA 50 slope
- four-bar cooldown
- long-only, no leverage
- completed-bar signal and following-open entry
- 0.50% equity risk and 50% maximum position fraction
- 3:1 target preserved in every catalog member
- OBV retained only as diagnostic evidence, not an entry gate

No additional combination, continuous parameter, hidden trial or result-driven
catalog mutation is permitted.

## Nested chronological calibration

The adaptive procedure uses expanding outer windows:

- 5,760 bars available before the first outer test
- 720-bar outer test
- 720-bar non-overlapping outer step
- at least five outer windows

Inside every outer training prefix, selection uses only the four most recent
non-overlapping inner validation windows:

- initial 2,880-bar inner train
- 720-bar inner validation
- 720-bar step
- maximum four recent inner validation windows

For the exact 11,076-row BTC/ETH dataset this creates seven outer development
tests and leaves 276 terminal rows unused. Each outer-window parameter choice
is completed at the exact outer-test boundary. No outer candle, result,
classification or trade may be available to selection.

## Inner eligibility gates

One shared parameter set must satisfy the gates on both BTC and ETH under both
Coinbase baseline and stress assumptions:

- positive median baseline net return
- nonnegative median stress net return
- at least 60% positive inner windows under baseline and stress
- at least 12 completed inner-validation trades per asset
- no more than 20% drawdown
- no more than 12x annualized executed-notional turnover
- no more than 10% annualized baseline modeled cost fraction
- exact active protective policy

If no catalog member passes every gate, the live-equivalent action for that
outer test is `HOLD_CASH`. Selecting the least bad failing configuration is
prohibited.

## Deterministic inner selection

When multiple configurations are eligible, selection uses this pre-declared
order:

1. maximize the worst-asset stressed median net return;
2. maximize the worst-asset baseline median net return;
3. minimize mean annualized turnover; and
4. use immutable catalog order only as the final exact tie-break.

This selection is part of the adaptive algorithm and must be repeated using
only then-available evidence in every outer window. The protocol prohibits a
global hindsight leaderboard or choosing one configuration after inspecting
all outer tests.

## Component implementation status

This protocol intentionally does not execute diagnostics or calibration. A
separate reviewed component patch now provides and tests:

- causal EMA trend-structure features from completed Close values
- completed-bar +1R break-even transitions that become active only at the
  following Open
- MFE/MAE, realized-R, holding-bar and time-to-MFE evidence from the executable
  post-entry path

The nested calibration runner, its exact inner-only evaluation interface and
atomic one-shot evidence with raw-evaluation hashes remain a separate review.
Break-even means the stop trigger moves to the entry execution price; sell
costs or a gap through that stop can still produce a negative net result.

Until that runner is implemented, reproduced and committed, execution remains
unauthorized.

## Outcome interpretation

The future development report may describe whether the complete adaptive
procedure retains research interest. It may not identify a formal candidate.
Outer development results can generate one new falsifiable hypothesis, but any
later candidate requires:

- a new immutable identity
- a new pre-registration
- current venue/execution assumptions
- the same hard risk and cost-survival boundary
- genuinely unseen validation data
- separate bounded forward-PAPER review

Cloud services and all real execution remain parked.

## Controlled non-evaluating commands

Print the declaration:

```powershell
python src/alpha_discovery_protocol.py
```

Lock the exact dataset and Alpha v2 evidence without running diagnostics or
calibration:

```powershell
python src/alpha_discovery_protocol.py `
    --manifest data/research/first_candidate_v1/manifest.json `
    --alpha-report data/research/alpha_development_v2/development_v2/alpha_development_report.json
```

Both commands retain every Candidate v2, optimization, PAPER and live flag as
false.
