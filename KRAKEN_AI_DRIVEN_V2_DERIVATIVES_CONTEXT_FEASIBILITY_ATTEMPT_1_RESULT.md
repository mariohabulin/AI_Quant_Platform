# Kraken AI-Driven V2 Derivatives Context Feasibility Attempt 1 Result

## Immutable identity

- execution commit: `99f62423d19d7684c80ed67ed99666e2f48b0fbc`;
- protocol: `kraken-btc-eth-xrp-ai-v2-derivatives-context-feasibility-v1`;
- protocol SHA-256:
  `08523d94d47f9e47f71b30e8f64f8dfd0108cf43cef6b6f36f6db6c9f93d6698`;
- component SHA-256:
  `cb9d37eca11a3d7295feecb330d15b3a9417f4d9240a7725f95dd6371b872c6b`;
- external report SHA-256:
  `3c84fba6034790ae59761f3fba23affca80fca0c8b7d29b3e3f3762c789d8e29`.

## Observed source coverage

The read-only audit listed public Binance USD-M archive object names without
opening any market-value row. All twelve source/asset identities were present.
The shared interval was `2021-12-01T00:00:00Z` through
`2024-04-01T00:00:00Z` exclusive, or 852 calendar days.

| Source | Assets | Common expected periods | Common missing | Coverage |
|---|---:|---:|---:|---:|
| Funding rate, monthly archives | 3 | 28 each | 0 | 100% |
| Open-interest metrics, daily archives | 3 | 852 each | 0 | 100% |
| Native 12h mark price, monthly archives | 3 | 28 each | 0 | 100% |
| Native 12h index price, monthly archives | 3 | 28 each | 0 | 100% |

No duplicate archive period was observed. Funding, mark and index history began
in January 2020 for all assets. The common start is constrained by ETHUSDT and
XRPUSDT open-interest metrics beginning on 1 December 2021.

## Frozen conclusion

Status:
`KRAKEN_AI_V2_DERIVATIVES_CONTEXT_SOURCE_FEASIBLE_HYPOTHESIS_DESIGN_REQUIRED`

Action: `DESIGN_NEW_INFORMATION_HYPOTHESIS`

All four feasibility gates passed. This proves only that the candidate source
has enough continuous archive history to justify one pre-registered
derivatives-context hypothesis. It does not prove predictive value or alpha.

Market values, labels, model fitting, Calibration and Evaluation remained
unopened. Candidate v2, PAPER, cloud, real orders and live execution remained
unauthorized.
