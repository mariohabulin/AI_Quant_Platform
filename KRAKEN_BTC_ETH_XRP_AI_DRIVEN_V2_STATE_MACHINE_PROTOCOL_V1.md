# Kraken BTC/ETH/XRP AI-Driven v2 State Machine Protocol v1

## Status

`AI_DRIVEN_V2_STATE_MACHINE_REVIEWED_SYNTHETIC_TESTS_ONLY`

This protocol freezes the first deterministic
`FLAT -> ARMED -> LONG -> FLAT` signal-state hypothesis before market
performance is inspected. It does not execute an order, calculate a fill, size
a position, set a tradable stop/target, optimize a parameter, open the external
Kraken dataset or authorize Candidate v2, PAPER, cloud or live operation.

## Frozen identity and prerequisites

- state protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-state-machine-v1`;
- feature protocol ID:
  `kraken-btc-eth-xrp-ai-driven-v2-causal-feature-contract-v1`;
- dataset ID:
  `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- dataset manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- feature protocol normalized SHA-256:
  `cd387d4fa07f55b45004ccddb40bf53932882e1af7ef1d413101ed9a982aefd5`;
- feature component normalized SHA-256:
  `4a00ce71f96a1c17c6ec04b9d5e5befb9e5a94a78e3695fa4bffc35030769893`;
- supervised v1 BTC evidence SHA-256:
  `56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`;
- reference parameter-set ID:
  `kraken-ai-v2-ccvr-reference-a-v1`;
- observation timing: `COMPLETED_DAILY_BAR_CLOSE`;
- state role: `SIGNAL_STATE_NOT_EXECUTED_POSITION`;
- future-bar access: `PROHIBITED`.

The BTC supervised episode remains inspected context and is not unseen
evidence. ETH and XRP supervised v1 participant views remain unopened. This
state milestone uses synthetic bars only.

## Reference parameter set A

The following values are pre-registered as one interpretable starting
hypothesis, not as optimized or profitable settings:

- prior-close decline lookback: `30` completed bars;
- prior-volume median lookback: `30` completed bars;
- prior-true-range mean lookback: `14` completed bars;
- minimum drawdown from prior close high: `0.15`;
- maximum capitulation one-bar close return: `-0.05`;
- minimum capitulation relative volume: `2.0`;
- minimum capitulation range expansion: `1.5`;
- maximum capitulation close location: `0.35`;
- maximum confirmation delay: `5` completed bars after the event;
- confirmation close return: strictly greater than `0.0`;
- minimum confirmation relative volume: `1.2`;
- minimum confirmation close location: `0.60`;
- confirmation price rule: close strictly above the immediately previous
  completed bar high;
- maximum bearish-volume exit close return: `-0.03`;
- minimum bearish-volume exit relative volume: `1.5`;
- maximum bearish-volume exit close location: `0.35`.

The 30-bar context matches the reviewed daily observation horizon, 14 bars is a
conventional volatility-measurement window, and all event thresholds require a
joint price, volume, range and close-location exception. These are design
rationales only. No result may be used to retroactively describe the values as
validated.

## State contract

### FLAT

`FLAT` means no active signal setup. A bar arms the setup only when all five
capitulation conditions are true on the same completed bar:

1. drawdown from the prior 30-bar close high is at least `0.15`;
2. one-bar close return is at most `-0.05`;
3. relative volume is at least `2.0`;
4. range expansion is at least `1.5`;
5. close location is at most `0.35`.

The event timestamp, event low and current setup low are captured. The setup
becomes `ARMED` with age `0`. The event bar can never also confirm entry.

If a required feature is unavailable, the state remains `FLAT` with an
explicit unavailable reason. Missing values never become zero or pass a gate.

### ARMED

On each later completed bar, age increases by one. Confirmation is eligible at
ages `1` through `5` inclusive and requires all four conditions:

1. close return is strictly positive;
2. relative volume is at least `1.2`;
3. close location is at least `0.60`;
4. close is strictly above the immediately previous completed bar high.

Confirmation moves the signal state to `LONG` and emits only
`ENTER_NEXT_OPEN`. That text is an intent for a later execution adapter; this
milestone opens no position and assumes no fill.

The setup low is the minimum low observed from the event through confirmation.
A completed close below the previously recorded setup low invalidates the
setup. If a new full capitulation event occurs first, it replaces the prior
anchor and restarts age at `0`. This re-arm decision has priority over ordinary
invalidation because it is a new independently complete event.

If age becomes greater than `5`, the setup expires before confirmation can be
accepted. Unavailable confirmation features keep the state armed only until
normal expiry; they never create confirmation.

The frozen `ARMED` priority is:

1. new capitulation re-arm;
2. completed-close structural invalidation;
3. expiry;
4. confirmation;
5. continue waiting.

### LONG

`LONG` is an active signal state, not proof of an executed holding. The
original setup low remains fixed. The state emits `EXIT_NEXT_OPEN` and returns
to `FLAT` if either:

- completed close is below the fixed setup low; or
- close return is at most `-0.03`, relative volume is at least `1.5`, and
  close location is at most `0.35`.

If both occur together, the explanation must record both. Otherwise the signal
remains `LONG`. No profit target, trailing stop, break-even transition or
maximum holding period is defined here; those belong to the next risk and
execution protocol.

The frozen `LONG` priority is:

1. combined structural and bearish-volume exit;
2. structural exit;
3. bearish-volume exit;
4. continue holding the signal state.

## Explanation contract

Every completed bar must retain:

- state before and after;
- one canonical transition/reason code;
- action intent: `NONE`, `ENTER_NEXT_OPEN` or `EXIT_NEXT_OPEN`;
- capitulation, confirmation, structural-failure and bearish-volume booleans;
- setup age, signal-long age, fixed setup low and event timestamp when
  applicable;
- the causal feature values already present on that row.

The complete path must be prefix-stable. Appending or mutating a later bar
cannot alter any earlier feature, condition, state or reason.

## Explicit non-execution boundary

The state machine is not a backtest. `ENTER_NEXT_OPEN` and `EXIT_NEXT_OPEN` are
unfilled causal intents. A later protocol must separately freeze signal-to-fill
timing, gaps, fees, spread, slippage, structural stop placement, risk per
trade, position size, `3R` causal room, stop-first same-bar ambiguity, profit
management and maximum holding behavior.

The generic `RiskEngine` and `ProtectiveExitPolicy` may later be adapted, but
they are not called by this milestone. No account equity, unit quantity, entry
price, exit price, return, P&L, benchmark or drawdown is produced.

## Synthetic verification requirements

Tests must prove:

- the exact reference parameter values and validation;
- event bars arm but cannot confirm on the same bar;
- confirmation works only at ages `1` through `5`;
- re-arm, structural invalidation and expiry priority;
- setup-low capture through confirmation;
- structural, bearish-volume and combined exits;
- unavailable features fail closed;
- input data remains unchanged;
- the entire real feature-to-state path is prefix-causal and future-stable;
- output contains no fill, position-size, P&L or optimization field.

## Next boundary

After Windows integration and full regression, pre-register a V2 risk and
execution adapter. It must resolve next-open fills and gaps, convert the setup
low into an executable stop, enforce bounded position risk and minimum causal
reward room, and apply conservative protective exits. It must still execute
synthetic tests only before any real-data performance runner is separately
reviewed.

## Authorization state

- causal feature component implemented: `true`;
- deterministic signal state machine implemented: `true`;
- reference state parameters frozen: `true`;
- action intents emitted: `true`;
- real order fills executed: `false`;
- risk adapter implemented: `false`;
- external dataset opened: `false`;
- performance evaluation executed: `false`;
- optimization authorized: `false`;
- Candidate v2 authorized: `false`;
- bounded forward PAPER authorized: `false`;
- cloud execution authorized: `false`;
- live execution authorized: `false`.
