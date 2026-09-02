# Kraken BTC/ETH/XRP AI-Driven V2 Derivatives Context Learning Hypothesis V1

## Frozen purpose

Protocol ID:
`kraken-btc-eth-xrp-ai-v2-derivatives-context-learning-hypothesis-v1`

The feasibility audit passed all source gates over 852 common calendar days.
Its external report SHA-256 is
`3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29`.
This protocol freezes one causal experiment before any derivatives market
value is downloaded or parsed.

The hypothesis is that funding, open-interest change and futures basis contain
incremental information about cost-aware 3R/1R spot outcomes that was absent
from the closed Kraken spot-OHLCV representation. The null is that matched
context-aware models do not improve stable unseen Development evidence.

## Data and time identity

- execution and labels: Kraken native 12h spot BTC-USD, ETH-USD and XRP-USD;
- explanatory context: Binance USD-M BTCUSDT, ETHUSDT and XRPUSDT;
- common Development interval: 2021-12-01 through 2024-04-01 exclusive;
- first usable row: only after 60 consecutive context-complete 12h bars;
- label: unchanged next-open, adverse-cost, 3R target, 1R stop, 30-day timeout;
- Calibration and Evaluation: unopened.

Every record retains its venue. Binance context may explain a Kraken spot
decision but may never replace the Kraken execution or outcome price.

## Causal availability and missing data

A Kraken candle timestamp identifies its 12h bar opening time. Its decision is
made only after that candle completes. A derivatives observation may enter the
same decision only when its event or bar-completion timestamp is no later than
that decision time.

- funding is backward-as-of joined with a maximum age of 12 hours;
- open interest is backward-as-of joined with a maximum age of 30 minutes;
- mark and index prices must be the exact matching completed native 12h bar;
- no backward join may select a future timestamp;
- no interpolation, backfill or cross-partition fill is allowed;
- any stale or absent source value invalidates that row and its 60-bar rolling
  context until a complete causal window exists.

Control and context variants use the same context-complete rows. This prevents
the control from receiving a different or easier sample.

## Frozen derivatives feature schema

Exactly nine new features are computed independently per asset:

1. latest funding rate;
2. six-bar funding-rate mean;
3. 60-bar funding-rate z-score;
4. one-bar log open-interest change;
5. six-bar log open-interest change;
6. 60-bar log-open-interest z-score;
7. mark-to-index basis fraction;
8. one-bar basis change; and
9. 60-bar basis z-score.

Rolling means and population standard deviations end at the current available
observation. A complete constant window has z-score zero. The existing 16 spot
features are not changed. Context models therefore receive 25 numeric features
plus asset identity; controls receive the original 16 plus asset identity.

## Frozen walk-forward experiment

Three expanding outer folds use a 30-day purge:

| Fold | Training ends before | Validation interval |
|---|---|---|
| 1 | 2022-11-01 | 2022-12-01 to 2023-04-01 exclusive |
| 2 | 2023-04-01 | 2023-05-01 to 2023-09-01 exclusive |
| 3 | 2023-09-01 | 2023-10-01 to 2024-04-01 exclusive |

Inside each outer training window, the earlier 75% of unique decision times
fits the base learner and the later purged 25% fits its calibrator. Outer
validation fits nothing.

Exactly four matched variants execute:

1. spot-only histogram-GBT three-class control;
2. spot plus context histogram-GBT three-class hypothesis;
3. spot-only histogram-GBT direct-net-R control; and
4. spot plus context histogram-GBT direct-net-R hypothesis.

Each matched pair uses identical frozen model and calibration parameters. The
two spot-only controls are attribution controls and can never become a new
candidate. There is no learner, hyperparameter or threshold sweep.

## Economic and incremental gates

The eligibility threshold remains zero expected net R. A context hypothesis is
Development-viable only if it has:

- at least 30 raw and 10 non-overlapping selections in every fold;
- positive mean and cumulative non-overlapping net R in every fold;
- positive cumulative net R on at least two assets;
- positive mean and cumulative non-overlapping net R overall;
- higher overall and worst-fold mean net R than its matched control; and
- better objective-specific predictive evidence than its control in at least
  two of three folds.

Classification comparison uses lower multiclass log loss, with target PR-AUC
as a reported diagnostic. Regression comparison uses lower net-R mean absolute
error, with Spearman correlation as a reported diagnostic. A control result is
never promotable. A control fold with zero eligible trades represents
`HOLD_CASH` and has a frozen economic comparator of `0.0 R`; it is not assigned
an invented trade mean. If neither context hypothesis passes every absolute
and incremental gate, the action is `HOLD_CASH` and this bundle closes.

## Frozen next stage and safety boundary

The next stage may implement only a hash-bound reader and dataset lock for the
four already-audited source series. It must validate source schemas and causal
timestamps before creating a real learning runner.

No market values, labels or models are opened by this protocol component.
Automatic selection, runtime learning, Calibration, Evaluation, Candidate v2,
PAPER, cloud, real orders and live execution remain unauthorized.
