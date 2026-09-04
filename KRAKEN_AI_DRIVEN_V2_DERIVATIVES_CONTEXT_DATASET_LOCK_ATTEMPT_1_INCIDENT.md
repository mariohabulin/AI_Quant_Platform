# Kraken AI-Driven V2 Derivatives Context Dataset Lock Attempt 1 Incident

## Immutable execution identity

- execution commit: `970ce17a90e8de601f072ca4b9c62704d81511ce`;
- authorized attempt: `1`;
- authorization phrase consumed:
  `EXECUTE_KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_ONCE`;
- target dataset:
  `binance-usdm-btc-eth-xrp-derivatives-context-20211201-20240401-v1`;
- final dataset lock created: false;
- Attempt 1 staging preserved: true;
- labels generated: false;
- model training executed: false;
- Calibration opened: false;
- Evaluation opened: false;
- Candidate v2 authorized: false;
- real orders submitted: false.

## Observed failure

The authorized acquisition passed the content-based repository gate and began
downloading the exact 2,808-object registry. The last emitted progress marker
was `100/2808`. Acquisition then failed closed while validating a daily BTCUSDT
metrics archive:

```text
ValueError: count_toptrader_long_short_ratio must be a finite decimal.
RUN_EXIT_CODE=1
```

No final dataset directory was created. The non-final Attempt 1 staging
directory is retained as incident evidence and must never be renamed, deleted
or reused by a recovery run.

## Root cause established from the official object

The first triggering object is registry object `114`:

- object: `BTCUSDT-metrics-2021-12-30.zip`;
- official ZIP SHA-256:
  `5ff089f1d6427237a24301ec5189b0318f169ecf16c579c41fd33e576841d87d`;
- decompressed CSV SHA-256:
  `7f4ce04716e5e1b8ba97ff097fc4d403f696b9daef99e2cfbc6c3c56518dd821`;
- source rows: `288`;
- first affected timestamp: `2021-12-30T14:35:00Z`;
- affected rows in that object: `113`;
- blank optional ratio cells in that object: `452`.

At the first affected timestamp, the retained learning input
`sum_open_interest` is the valid positive value `72516.05400000`, and
`sum_open_interest_value` is also present. Binance leaves the four ancillary
long/short-ratio fields blank. The frozen hypothesis uses only
`sum_open_interest` from this source; none of the blank ancillary ratio fields
is normalized or learned.

The implementation mistake was requiring finite decimals in every ancillary
ratio cell even though the official schema permits blank cells in those
unused fields. This was a reader/validator assumption error, not evidence of a
bad checksum, corrupted archive, missing open interest, model failure or
strategy result.

## Frozen recovery rule

Recovery may not fill a blank with zero, forward-fill, interpolate, drop the
valid open-interest row, alter the hypothesis or reuse Attempt 1 staging.
Instead it must:

1. retain exact schema, symbol, timestamp, chronology and period validation;
2. continue requiring positive finite `sum_open_interest` and finite
   `sum_open_interest_value`;
3. accept only an exact blank or a finite decimal in the four unused ancillary
   ratio fields;
4. record optional blank counts by field in every object and in the final
   manifest;
5. fail closed on any other sentinel or malformed value;
6. hash and preserve Attempt 1 staging before and after recovery;
7. use a new output root and a separate one-shot Attempt 2 authorization.

Attempt 1 is consumed and must not be rerun.
