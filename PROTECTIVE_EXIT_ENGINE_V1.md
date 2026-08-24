# Protective Exit Engine v1

## Purpose

Protective Exit Engine v1 converts a reviewed risk distance into active,
costed historical stop and target exits. It removes the gap between calculating
position size from Stop/Target levels and merely recording those levels without
ever allowing them to close the position.

The engine is an optional Backtesting Engine policy. Legacy behavior is
unchanged when the policy is absent. Protocol v1 supports long positions under
`next_bar_open` execution only.

## Causal timing

For an entry signal observed after bar `t` closes:

1. the signal-bar risk distance is frozen from information available at `t`
2. entry executes at bar `t+1` Open
3. stop and target are resolved around that execution Open
4. protection is active during the remainder of bar `t+1`
5. later bars check gaps at Open before pending signal execution
6. intrabar High/Low touches are evaluated only after Open processing

No Open, High or Low from `t+1` changes the signal-bar ATR distance. The
following bar supplies execution and realized path evidence, not signal input.

## Frozen Alpha v2 levels

The reviewed Alpha Development Protocol v2 adapter uses:

```text
risk_distance = 2 * ATR_14 from the completed signal bar
stop = following_bar_open - risk_distance
target = following_bar_open + 3 * risk_distance
```

Risk Engine checks that the stop is below entry, the target is above entry and
the reward/risk ratio matches 3:1. Position sizing uses 0.50% equity risk and a
50% maximum position fraction in the Alpha v2 factory.

The signal frame must retain:

- `ALPHA_V2_ATR_RISK_DISTANCE`
- `ALPHA_V2_REWARD_RISK_RATIO`

Missing, non-finite, non-positive or policy-drifted evidence fails closed.

## Bar-ordering semantics

### Gap through stop

If an existing long position opens at or below its stop, it exits at that first
available Open. It is not filled retroactively at the better stop price.

### Gap through target

If the bar opens at or above the target, v1 records the target price rather
than assuming favorable Open-price improvement. This is deliberately
conservative.

### Pending signal at the same Open

An already-triggered protective gap has priority over a pending signal exit at
the same Open. The trade is attributed to protection and does not invent an
exit-signal timestamp.

### Intrabar touch

After Open processing:

- Low at or below stop triggers a stop exit
- High at or above target triggers a target exit
- when both are touched in one candle, the unknown path is resolved as
  `STOP_FIRST`

The stop-first rule prevents an OHLC bar from selecting the favorable path
without tick evidence. Protection is active on the entry bar.

### Optional completed-bar break-even ratchet

Discovery Protocol v1 may enable a frozen `1R` trigger. A surviving bar whose
High reaches entry plus the initial risk distance records the trigger only
after that bar is complete. The stop moves to the entry execution price for
the following Open and later bars; the trigger bar is never reprocessed with
the tighter stop. A final bar cannot activate the ratchet because no following
Open exists. Gap-through-stop behavior remains unchanged, so this is a price-
level break-even rule rather than a guarantee of zero net loss.

## Execution costs and evidence

Every protective sell uses the normal Backtesting Engine sell path. Commission,
slippage and half-spread are applied exactly as for a signal or terminal exit.
Consequently, a gross 3R target is expected to realize less than 3R net after
costs, and a stop may lose more than planned monetary risk after friction or a
gap.

Each trade now records:

- `exit_reason`: signal, protective stop, protective target or terminal close
- protective exit type: stop/target and gap/intrabar
- trigger price and fill reference
- same-bar stop/target conflict flag
- entry/exit signal and execution timestamps
- planned stop, target, monetary risk and reward/risk
- gross P/L, execution cost, commission, total costs and net P/L
- active stop at exit and break-even enabled/triggered evidence
- maximum favorable and adverse excursion in initial-risk units
- net and gross realized R, holding bars and bars to maximum favorable excursion

Surviving bars contribute their complete High/Low because the position was
active for the full bar. On an exit bar, excursion evidence uses only the
executable conservative path: the stop/target fill or gap Open. It does not use
an unreachable favorable extreme after a stop-first exit.

The additional fields are present on legacy trades with inactive/null
protective evidence, preserving a stable report shape without activating the
new behavior.

## Validation-stack propagation

The optional Risk Engine and Protective Exit Policy are forwarded unchanged
through:

- `OutOfSampleValidator`
- `WalkForwardValidator`
- `StrategyValidationPipeline`
- `MultiAssetValidator`

Every Backtesting Engine run resets Risk Engine protection state, including
between chronological partitions and assets. Compact research evidence retains
the exact protective-policy declaration while raw trade evidence remains
available to the metrics layer before compaction.

## Validation and failure boundaries

Protective mode requires:

- a `RiskEngine`
- `next_bar_open` execution
- exact matching Risk Engine and policy reward/risk requirements
- finite positive OHLC data with valid candle geometry
- complete signal-bar risk distance and reward/risk evidence

It rejects same-close protective execution, optimistic target-first ambiguity,
stop-price gap fills and guaranteed maker fills. Version 1 models full taker
execution only; partial fills and maker order behavior remain outside this
engine.

## Authorization state

Implementation and local tests do not by themselves authorize Alpha v2
performance. The separate Alpha Development Runner v2 binds the exact three
variants, Risk Engine, Protective Exit Policy, turnover/cost budgets and
permitted taker scenarios behind its own one-shot evidence lock.

Candidate v2, optimization, bounded forward PAPER and live execution remain
false. Cloud services remain parked.
