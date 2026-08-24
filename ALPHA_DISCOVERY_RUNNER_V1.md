# Alpha Discovery Runner v1

## Purpose

This runner executes the frozen Alpha Discovery and Calibration Protocol v1
exactly once. It tests whether the complete adaptive procedure, including
`HOLD_CASH`, retains development interest on the inspected BTC/ETH six-hour
dataset.

It is not a formal Candidate v2 evaluation. It cannot rank configurations
globally, reinterpret outer development results as unseen evidence, start
PAPER, enable cloud services or authorize live execution.

## Exact evidence lock

The process revalidates in the same invocation:

- dataset manifest SHA-256
  `6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f`;
- closed Alpha Development v2 report SHA-256
  `19627f7002fc3159729ea61d22ead0fa25deca455612764121ea96fd3eaf71a0`;
- exact BTC-USD and ETH-USD asset scope and equal row counts;
- the immutable eight-member parameter catalog and fingerprint; and
- the complete frozen discovery configuration.

A declaration alone never authorizes execution. The runner obtains the lock
again in the same process before reading market evidence.

## Phase 1 — zero-cost path diagnostic

The exact three closed Alpha v2 variants are replayed once at zero modeled
cost. The diagnostic derives bounded MFE, MAE, net realized R, holding bars,
bars to MFE and exit-reason summaries. It may explain gross-signal behavior,
but its API and report state explicitly prohibit parameter selection from
zero-cost results.

Complete raw evaluations are canonicalized and hashed. Raw trade histories and
equity arrays are not persisted in the report.

## Phase 2 — nested chronological calibration

For each of seven outer windows, the runner evaluates all eight configurations
under Coinbase baseline and Coinbase stress on only the four most recent inner
validation windows available at that boundary. One configuration must pass all
cross-asset gates before it is eligible.

Selection occurs before the outer evaluation call. The selector receives no
outer market result. When nothing qualifies, the outer action is `HOLD_CASH`
and no strategy evaluation is executed on that outer window.

Repeated inner windows are evaluated once and reused only by later selection
boundaries for which that same historical window is already available. Every
piece of window evidence is bound to:

- asset;
- parameter-set ID;
- baseline or stress profile;
- inner or outer phase;
- exact start and end positions;
- protective policy; and
- the SHA-256 of the complete canonical partition result.

## Development review

The outer review evaluates the adaptive procedure, not a hindsight winner. It
includes `HOLD_CASH` as zero return, zero drawdown, zero turnover and zero cost
for the applicable outer window. Development interest requires all frozen
baseline/stress, persistence, drawdown, turnover and cost gates.

Even a retained-interest result would only support a new hypothesis. It would
not create Candidate v2 or make inspected outer windows genuinely unseen.

## Atomic evidence

The final files are:

```text
data/research/alpha_discovery_v1/discovery_v1/alpha_discovery_report.json
data/research/alpha_discovery_v1/discovery_v1/alpha_discovery_report.sha256
```

The runner writes both files into `.discovery_v1.staging` and renames that
directory only after complete evaluation, canonical serialization and SHA-256
construction. Existing final or staging evidence blocks a repeat.

## Controlled command after integration

Only after focused/full Windows reproduction, commit/push, clean working-tree
verification, exact input-hash verification and confirmation that final and
staging output are absent:

```powershell
python src/alpha_discovery_runner.py `
    --manifest data/research/first_candidate_v1/manifest.json `
    --alpha-report data/research/alpha_development_v2/development_v2/alpha_development_report.json
```

The command executes development research. It keeps optimization, Candidate
v2, bounded forward-PAPER, cloud and live authorization false.
