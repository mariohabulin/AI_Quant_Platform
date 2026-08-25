# Trend Pullback and Volume Re-expansion Strategy v1

## Purpose

This component makes the four-member pre-registered catalog executable without
running market performance. It implements only signal construction and exposes
the existing static 2 ATR / 3R protective inputs for a future separately
reviewed runner.

Candidate v2, parameter selection, PAPER and live execution remain
unauthorized.

## Completed-bar setup state

`src/trend_pullback_state.py` owns the causal setup lifecycle. For each catalog
member it derives:

1. prior ADX strength from exactly the preceding eight completed bars;
2. an armed pullback when price is within the frozen ATR distance of EMA 50 and
   relative volume is no greater than 1.0;
3. a later recovery when price closes above the prior High and EMA 50, ADX is
   at least 20, `+DI > -DI` and relative volume reaches the frozen expansion
   threshold; and
4. expiry after eight subsequent completed bars.

A pullback bar cannot trigger itself. Loss of causal EMA trend structure,
evaluation-window reset, an open signal position or cooldown clears setup
state. Prior bars remain available only for causal feature warm-up.

## Executable strategy adapter

`src/trend_pullback_volume_strategy.py` combines existing reviewed components:

- ADX 14 and ATR 14 features;
- lagged 20-bar trailing-median relative volume;
- EMA 50 / EMA 200 and four-bar EMA 50 slope structure; and
- the new ordered setup state.

The completed recovery bar emits `Signal = 1`; normal execution timing remains
the following Open. A completed bar emits `Signal = -1` when Close falls below
EMA 50, ADX falls below 15 or `+DI <= -DI`. The Protective Exit Engine will
remain responsible for active stop/target execution when a future runner
injects the exact policy and Risk Engine.

Market-regime and OBV entry gates are intentionally absent. They were not
silently carried from the closed impulse strategy. OBV remains diagnostic only.

## Identity and safety

The adapter constructs exactly the four parameter-set IDs in immutable catalog
order. Supplied volume, EMA or setup-state components must match the catalog or
construction fails closed.

No performance evaluation, nested calibration, ranking or selection exists in
these modules. The future runner remains a separate implementation and review
boundary, and no final or staging evidence is created here.
