# Alpha Development Closure v2

## Closure decision

Alpha Development v2 is closed as a completed inspected-development study.
All three frozen joint ADX, relative-volume, market-regime and OBV variants are
`SCREEN_OUT`. No mechanism retains development interest under the exact v2
promotion gates.

This result does not authorize Candidate v2, optimization, bounded forward
PAPER, cloud activation or live execution. It also does not claim that market
regime, volume or protective exits are useless. It rejects only the exact
frozen v2 configurations as profitable deployable mechanisms.

## Immutable evidence

| Item | Recorded value |
| --- | --- |
| Runner implementation revision | `5a9018b` |
| Evidence revision | `b2a5e60` |
| Dataset manifest SHA-256 | `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f` |
| Failure Attribution report SHA-256 | `e4193bff907a2121701e7ddc1d740894641c7bf427c9501fd4ecd4392a1f81f4` |
| Alpha Development report SHA-256 | `19627f7002fc3159729ea61d22ead0fa25deca455612764121ea96fd3eaf71a0` |
| Canonical report bytes | `878013` |
| Development dataset | BTC-USD and ETH-USD, native Coinbase 6h |
| Development matrix | 3 variants x 3 taker scenarios = 9 multi-asset evaluations |

Windows reproduced 203/203 focused tests and 944/944 complete tests before the
one-shot run. The absent-final/absent-staging preflight passed, the runner
completed all nine evaluations and the canonical report checksum was verified.
No staging directory remains.

## Frozen outcomes

| Variant | Outcome | Baseline BTC OOS / DD | Baseline ETH OOS / DD |
| --- | --- | ---: | ---: |
| ADX plus high relative volume | `SCREEN_OUT` | -12.76% / 13.60% | -3.14% / 6.51% |
| Plus `BULLISH_NORMAL` regime | `SCREEN_OUT` | -6.30% / 6.59% | -2.91% / 5.80% |
| Plus rising OBV | `SCREEN_OUT` | -6.30% / 6.59% | -2.29% / 5.19% |

Every variant failed the same three development gates:

- baseline multi-asset validation
- cost-stress multi-asset validation
- positive baseline OOS return on both assets

Every variant passed the frozen evidence-volume, drawdown, annual-turnover,
annual-baseline-cost and exact protective-policy gates. All asset/profile
classifications remain `REJECTED`, the positive walk-forward excess rate is
36.36% rather than the required 60%, and statistical falsification fails.

Kraken taker sensitivity improves the v3 OOS returns to -4.46% BTC and -1.02%
ETH but does not create positive absolute returns. A cheaper venue therefore
cannot rescue the frozen signal. Maker economics remain unevaluated because a
causal placement, fill, non-fill and partial-fill model does not exist.

## Operational findings

Baseline annualized turnover and modeled-cost burden are now bounded:

| Variant / asset | Annual turnover | Annual cost | OOS trades |
| --- | ---: | ---: | ---: |
| Volume / BTC | 5.59x | 3.91% | 44 |
| Volume / ETH | 3.72x | 2.61% | 38 |
| Regime-volume / BTC | 3.78x | 2.64% | 25 |
| Regime-volume / ETH | 2.67x | 1.87% | 26 |
| Regime-volume-OBV / BTC | 3.78x | 2.64% | 25 |
| Regime-volume-OBV / ETH | 2.59x | 1.81% | 25 |

These values are well below the frozen maximums of 24x annual executed
notional and 20% annual baseline cost fraction. The prior standalone-strategy
cost explosion is no longer the controlling failure.

The active protective engine materially bounds risk, but the exact 3R target
is reached infrequently. Baseline target exits range from two to five per
asset/variant, while protective-stop exits range from ten to eighteen and many
positions leave through the ADX/DI signal. This is evidence for a separate
exit-quality and trade-path study, not permission to alter the recorded run.

## What was learned

The experiment separated a useful engineering improvement from an absent alpha
claim:

- Risk Engine and active stop/target execution keep drawdown within the frozen
  limit.
- Market-regime filtering reduces trades, turnover, costs and loss magnitude.
- Rising OBV adds a small ETH improvement but no observable BTC improvement in
  this exact intersection.
- The remaining failure is primarily negative net expectancy, inadequate
  temporal persistence and failed statistical falsification.
- Position sizing cannot convert negative expectancy into edge, and lower
  taker fees alone do not make the mechanism profitable.

Comparison with the old standalone ADX evidence is descriptive rather than a
single-variable causal estimate because v2 simultaneously activates risk
sizing and protective exits. It is nevertheless clear that the new execution
and filtering stack substantially reduces loss and drawdown while still
failing to produce positive absolute return.

## Closed boundaries

- The three v2 variants may not be rerun, silently tuned, ranked or promoted.
- The canonical report and its SHA-256 sidecar are immutable evidence.
- The inspected BTC/ETH history is development data, not genuinely unseen
  future validation.
- Alpha Development v2 creates no Candidate v2 identity.
- No PAPER, cloud or live-money execution is authorized.
- Any changed parameter, entry, exit, regime, asset, timeframe or cost contract
  belongs to a new pre-registered development study.

## Next research boundary

The next mission is a bounded Alpha Discovery and Calibration Protocol. Before
performance it must pre-register:

1. trade-path and exit attribution for stop, target and signal exits;
2. a zero-cost diagnostic that separates residual signal from remaining costs;
3. a small hypothesis-led calibration set for entry quality, ATR risk distance
   and reward/risk behavior;
4. calibration confined to chronological training/validation boundaries;
5. market-regime-specific strategy roles rather than one universal rule;
6. unchanged hard risk, turnover and cost-survival constraints; and
7. a genuinely unseen final-validation boundary for any later candidate.

The next protocol may learn from v2 but may not rewrite v2. Its purpose is to
test a complete live-equivalent adaptive procedure, not search the inspected
report for a hindsight winner.
