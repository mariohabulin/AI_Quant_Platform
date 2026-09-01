# KRAKEN AI-DRIVEN V2 12H DEVELOPMENT LEARNING ATTEMPT 2 INCIDENT

## Identity

- execution commit: `203b4c5b81434be3edab7ec5372448cd12472288`;
- partition: `DEVELOPMENT` only;
- resolution: Kraken native `12h`;
- operator authorization: one Recovery Attempt 2;
- final evidence created: `false`;
- Attempt 2 staging created: `true`;
- Attempt 2 authorization consumed: `true`.

## Exact failure

The runner validated the complete archive identity and parsed the BTC
Development source member using the correct seven-field Kraken schema. It then
stopped with:

`RuntimeError: 12h Development boundary coverage mismatch for BTC-USD.`

The failure occurred inside source-frame construction, before the Learning Core
received any frame. No feature table, label, fold-support result, fitted model,
out-of-fold prediction, performance conclusion or final evidence was created.
Calibration and Evaluation remained unopened. No order was submitted.

## Root cause

The source contract already freezes the exact Development counts as:

- BTC-USD: `3833` observed rows and `1` missing calendar bucket;
- ETH-USD: `3834` observed rows and `0` missing calendar buckets;
- XRP-USD: `3830` observed rows and `4` missing calendar buckets.

Stage 2 had also recorded BTC as one continuous 3,833-row segment with no
internal gap. That pattern means the single missing bucket is at a Development
edge. Despite accepting the frozen count, the runner imposed an additional and
contradictory assertion that both the first and final calendar bucket must be
present. The synthetic fixture removed BTC's bucket from the interior, so it
did not reproduce the real boundary-gap pattern and allowed the contradiction
to pass tests.

This is an adapter-validation defect. It is not evidence that the archive is
invalid and it is not a learning or profitability result.

## Recovery rule

Attempt 2 must not be rerun. Its staging directory must remain untouched as an
incident marker, alongside the preserved empty Attempt 1 marker.

Recovery Attempt 3 may proceed only after all of the following are complete:

1. replace mandatory endpoint presence with full Development-grid validation;
2. retain exact archive byte size and SHA-256 validation;
3. retain exact per-asset observed-row and missing-bucket counts;
4. record the exact missing Development timestamps in source evidence;
5. add a regression fixture with BTC's missing bucket at the calendar edge;
6. require both prior attempt staging markers to exist, be distinct and empty;
7. use a new Attempt 3 evidence root and a new one-shot authorization phrase;
8. pass focused tests, the full regression suite and an independent hash-bound
   static review before any new source access.

No criterion is lowered. The correction removes only the logically impossible
requirement that a source with one acknowledged edge bucket missing must also
contain that same endpoint.

## Authorization boundary

- Recovery Attempt 3 authorized: `false`;
- real Development source reopened: `false`;
- labels generated: `false`;
- model training executed: `false`;
- automatic model selection: `false`;
- Calibration opened: `false`;
- Evaluation opened: `false`;
- Candidate v2 authorized: `false`;
- PAPER, cloud, real orders and live execution authorized: `false`.
