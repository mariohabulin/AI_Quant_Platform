# Kraken BTC/ETH/XRP AI-Driven v2 Causal Feature Protocol v1

## Status

`AI_DRIVEN_V2_CAUSAL_FEATURE_CONTRACT_REVIEWED_SYNTHETIC_TESTS_ONLY`

This protocol begins AI-driven v2 without evaluating market performance. It
freezes the first deterministic measurement boundary that will replace
unassisted chart guessing. It does not yet define a complete setup, emit a
trading action, choose a production parameter set, size a position, execute a
replay or authorize Candidate v2, PAPER, cloud or live operation.

## Frozen identity and source boundary

- protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1`;
- source dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- source manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- assets: `BTC-USD`, `ETH-USD`, `XRP-USD`;
- source mode: `OFFICIAL_OHLCVT_ARCHIVES_ONLY`;
- completed observation timing: `COMPLETED_DAILY_BAR_CLOSE`;
- future access: `PROHIBITED`;
- missing-bar policy: `SPLIT_AT_RECORDED_GAP`;
- feature implementation:
  `src/kraken_ai_driven_v2_features.py`;
- supervised v1 BTC aggregate evidence SHA-256:
  `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`;
- v1 evidence role: `INSPECTED_DEVELOPMENT_CONTEXT_ONLY`.

The existing locked dataset may be reused because v2 does not alter any source
row, gap or manifest. A later quarterly archive update must create a new
dataset identity and manifest; it must never modify the v2 source lock in
place.

## Architecture boundary

The v2 path is deliberately layered:

1. exact locked OHLCV and explicit availability gaps;
2. one continuous daily segment at a time;
3. completed-bar causal feature measurements;
4. a future pre-registered `FLAT -> ARMED -> LONG -> FLAT` state machine;
5. a future risk gate, next-open execution and conservative protective exits;
6. a future durable per-decision explanation and hash chain;
7. development, calibration and genuinely untouched evaluation boundaries;
8. only then a separate promotion review.

The language model may help offline with architecture, code, diagnostics and
research review. Runtime decisions must come from an exact versioned program;
the model may not improvise a live rule, silently change a threshold or read a
future outcome.

## Causal feature contract

The feature engine accepts exact ordered `Open`, `High`, `Low`, `Close` and
`Volume` columns on a unique, increasing, UTC-midnight, continuous daily
segment. It validates finite prices, nonnegative volume and OHLC geometry. A
recorded missing daily bucket is never filled; the caller must split the asset
at every gap before feature generation.

For completed bar `t`, the engine emits:

- previous close: `Close[t-1]`;
- one-bar close return: `Close[t] / Close[t-1] - 1`;
- prior close high: maximum of `Close` over the explicit decline lookback,
  ending at `t-1`;
- drawdown from prior high: nonnegative
  `(prior_high - Close[t]) / prior_high`;
- prior volume median: median `Volume` over the explicit volume lookback,
  ending at `t-1`;
- relative volume: `Volume[t] / prior_volume_median`;
- true range: maximum of `High-Low`, `abs(High-Close[t-1])` and
  `abs(Low-Close[t-1])`;
- prior ATR mean: mean true range over the explicit ATR lookback, ending at
  `t-1`;
- range expansion: `true_range[t] / prior_ATR_mean`;
- close location: `(Close-Low) / (High-Low)`.

All rolling comparison baselines exclude the current bar. This allows the
current completed bar to be measured against information that was already
available before it began. Warm-up values remain unavailable. A zero prior
volume baseline makes relative volume unavailable; a zero-range bar makes
close location unavailable. Future gates must reject unavailable required
features rather than invent values.

## Parameters deliberately not frozen

The implementation requires explicit decline, volume and ATR lookback integers
and supplies no production defaults. This milestone does not select their
values or define capitulation, exceptional volume, stabilization,
confirmation, stop distance, maximum holding period or exit thresholds.

Those rules must be frozen in the next state-machine protocol before a real
market performance run. A small hypothesis-led development catalog may compare
only pre-registered alternatives inside a development boundary. The BTC v1
episode dates are already inspected and cannot be counted as unseen evidence.

## Reuse and non-reuse decision

Reusable neutral infrastructure includes the Kraken archive-only lock, public
continuous-segment splitting, the generic risk-sizing mathematics and the
conservative stop-first protective-exit semantics. Each reuse still requires a
v2 adapter and exact tests before execution.

The previously rejected trend-pullback and Alpha strategy conditions are not
copied into v2. Their code and reports remain historical evidence. Copying a
rejected signal and renaming it would not create a new hypothesis.

## Synthetic verification requirements

Before Windows integration, tests must demonstrate:

- exact configuration validation without implicit defaults;
- strict daily OHLCV and continuous-segment validation;
- correct lagged-baseline formulas;
- current-bar exclusion from every rolling baseline;
- prefix causality and immunity to future-row mutation;
- source-frame immutability;
- unavailable rather than infinite zero-denominator features;
- no strategy signal, action, position, P&L or optimization output.

No external dataset is opened by the review declaration or this first test
milestone.

## Next boundary

After integration and full regression, define the smallest deterministic
capitulation/stabilization/confirmation state machine. It must explain every
state transition from named feature values and separately freeze next-open
entry, structural invalidation, position sizing, minimum causal reward room,
protective exits and maximum holding behavior before any performance runner is
built.

## Authorization state

- v1 BTC reconstruction closed as inspected context: `true`;
- additional supervised v1 replay authorized: `false`;
- causal feature component implemented: `true`;
- production feature parameters frozen: `false`;
- v2 state machine implemented: `false`;
- crypto strategy implemented: `false`;
- real dataset feature run executed: `false`;
- performance evaluation executed: `false`;
- optimization authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- live execution authorized: `false`.
