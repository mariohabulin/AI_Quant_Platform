# Kraken AI-Driven V2 Regime-Gated Selective Development Attempt 1 Result

## Immutable identity

- execution commit: `40d98117613d3f4a74e809f76dcd371804b3fc31`;
- report SHA-256: `a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286`;
- prediction SHA-256: `728b60750ed9de5070281d8d3cebecddbef701f2f6ea604dbeec7c2ea7015400`;
- Development decisions: 3,793;
- OOF predictions: 291;
- trained artifacts: two base models and two sigmoid calibrators; and
- evidence reader status:
  `KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_EVIDENCE_READER_PASS`.

The one-shot execution completed atomically. Final evidence exists, staging
does not, and the independent reader verified every declared byte without
unpickling a model.

## Observed support

The sparse gates produced 933 LONG regimes, 1,200 SHORT regimes and 1,660
neutral decisions. Derivatives context confirmed 201 LONG and 237 SHORT rows.

Only two of twelve variant/fold/direction cells had both base-fit and
calibration class support:

| Variant | Fold/direction | Validation rows | Brier vs prevalence | Required probability | Maximum probability | Selections |
|---|---|---:|---:|---:|---:|---:|
| Spot control | Fold 1 SHORT | 134 | 0.079266 vs 0.106763 | 0.312509 | 0.164130 | 0 |
| Spot control | Fold 2 SHORT | 157 | 0.013519 vs 0.046368 | 0.328033 | 0.211623 | 0 |

Control LONG lacked frozen class support in all three folds; Fold 3 SHORT also
lacked calibration support. Every context direction-fold cell lacked frozen
base-fit or calibration support, so the context variant fitted no artifact and
created no OOF prediction. Unsupported cells failed closed as registered.

All 291 OOF probabilities belonged to the two supported control SHORT cells.
Every probability was below its independently derived payoff break-even
threshold plus `0.05`, so every reconstructed action was `HOLD_CASH`.

## Frozen gate result

Both variants had:

- zero raw and zero non-overlapping selections in every fold and asset;
- zero cumulative selected net R and no defined selected mean net R;
- zero positive assets;
- failed raw support, non-overlap support, all-fold positive-net-R, overall
  positive-net-R, asset-breadth and all-direction Brier gates; and
- `development_viable=false`.

The context variant also won zero fold means and failed all three incremental
comparisons with its matched control. No hypothesis entered the passer list.

## Terminal conclusion

Action: `HOLD_CASH`.

Status:
`KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_NO_VIABLE_HYPOTHESIS_STOP_KRAKEN_12H_RESEARCH`.

This is a valid economic result, not a recoverable implementation incident.
The authorization is consumed and the Kraken BTC/ETH/XRP 12h research branch
is closed. There is no rerun, refit, threshold rescue, additional indicator or
automatic successor.

Calibration and Evaluation were not opened. Candidate v2, PAPER, cloud, real
orders and live execution remain unauthorized.
