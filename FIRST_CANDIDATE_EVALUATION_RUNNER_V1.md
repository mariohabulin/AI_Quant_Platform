# First Candidate Evaluation Runner v1

## Purpose

This runner connects the already frozen first-candidate dataset lock to the
existing Strategy Evaluation Protocol. It adds no strategy parameters, gates,
cost assumptions or evaluation mathematics.

The runner exists to make the first real evaluation one-shot, deterministic,
fail-closed and audit-friendly. Integrating and testing this code does not
authorize evaluation. The real command remains blocked until focused tests,
the full suite, code review, Git commit and Git push are complete.

## Frozen flow

1. Refuse execution if final or incomplete evaluation evidence already exists.
2. Revalidate the canonical manifest, SHA-256 sidecar, asset hashes, row counts,
   exact UTC grid and OHLCV through `FirstStrategyCandidatePreregistration`.
3. Require the exact frozen manifest SHA-256
   `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`;
   another internally valid dataset is still rejected for candidate v1.
4. Construct `StrategyEvaluationProtocol` from the locked candidate, strategy
   engine and configuration.
5. Run the protocol once. The protocol itself owns both baseline and stressed
   evaluation, all statistical evidence and the promotion decision.
6. Normalize expected Pandas/NumPy timestamps, timedeltas, arrays and scalar
   values into deterministic JSON primitives.
7. Reject an unknown outcome, missing baseline/stress evidence, any report that
   authorizes live execution, any missing time value, or any non-finite JSON
   value.
8. Write canonical JSON and its SHA-256 into a staging directory.
9. Rename the complete staging directory to `evaluation_v1`; existing evidence
   is never overwritten.

No partial evaluation result is printed. The CLI prints only a persisted
summary after both evidence files have been written successfully.

## Authorization boundary

An outcome of `PAPER_CANDIDATE` means only that the candidate is eligible for a
separate bounded forward-PAPER review. The evidence envelope always retains:

- `optimization_authorized=false`
- `bounded_forward_paper_authorized=false`
- `live_execution_authorized=false`

`RESEARCH_HOLD` and `REJECTED` remain research outcomes. None of the three
outcomes can place or authorize an order.

## Output contract

For a manifest at:

```text
data/research/first_candidate_v1/manifest.json
```

the fixed evidence location is:

```text
data/research/first_candidate_v1/evaluation_v1/evaluation_report.json
data/research/first_candidate_v1/evaluation_v1/evaluation_report.sha256
```

An interrupted evidence write leaves `.evaluation_v1.staging`. The runner then
fails closed and requires manual review; it never silently retries or deletes
the incomplete evidence.

## Controlled command after repository integration

Do not run this command merely because the patch has been applied. It becomes
authorized only after the new focused tests and full suite pass, the diff is
reviewed, and the exact runner commit is pushed with a clean working tree:

```powershell
python src/first_candidate_evaluation.py --manifest data/research/first_candidate_v1/manifest.json
```

The command has no output-directory override. This deliberately prevents a
second evaluation from bypassing the fixed evidence directory.

## Recovery boundary

A failed attempt that prints or persists no strategy result may be recovered
only after its technical cause is documented, regression-tested, reviewed,
committed and pushed. Recovery must reuse the exact frozen candidate, manifest,
configuration and random seed. It is not an authorization to modify the
hypothesis or tune parameters after execution.
