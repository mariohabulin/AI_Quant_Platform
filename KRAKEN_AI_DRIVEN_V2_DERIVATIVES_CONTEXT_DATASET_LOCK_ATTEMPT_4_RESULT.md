# Kraken AI-Driven V2 Derivatives Context Dataset Lock — Attempt 4 Result

## Result

Recovery Attempt 4 completed the frozen derivatives-context dataset lock and
the final independent read-only review passed.

- acquisition execution commit: `40b5943442c96d5ef26434db95d9dc955ca41c12`;
- final reader/review commit: `9b23d05eed043c92205e7a2ca62c70312f6b6e8f`;
- dataset ID:
  `binance-usdm-btc-eth-xrp-derivatives-context-20211201-20240401-v1`;
- final manifest SHA-256:
  `db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916`;
- official source-object count: `2808`;
- normalized file count: `12`;
- final file count: `5630`;
- final byte count: `63045508`;
- verified Attempt 3 resume objects: `695`;
- newly downloaded Attempt 4 objects: `2113`;
- exact paired open-interest zero sentinels omitted without fill: `399`.

## Independent reader conclusion

The final reader returned
`KRAKEN_AI_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_PASS` while the
manifest, its sidecar, file count and byte count remained unchanged. It opened
no network connection and modified no dataset byte.

Exact mark/index inner alignment retained only common completed native 12h
bars. BTC has 1,680 common rows and 18 mark-only rows. ETH and XRP each have
1,698 common rows and two mark-only rows. Every index timestamp is present in
mark, common close timestamps agree, and no interpolation, backfill or forward
fill is used.

Blank values in four unused ratio columns are counted as source evidence but
are not learning inputs and are not filled. Funding rate, positive open
interest, mark close and index close are the only locked values exposed to the
registered feature engine.

## Safety boundary

Dataset acquisition is closed and must not be repeated. This result authorizes
only implementation and later separate execution of the frozen four-variant
Development experiment. It does not authorize Calibration, Evaluation,
Candidate v2, PAPER, cloud execution, real orders or live trading.
