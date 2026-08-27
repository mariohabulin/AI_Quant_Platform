# Kraken BTC/ETH/XRP Daily Dataset Lock Evidence v2

## Status

`LOCKED_NON_PERFORMANCE_DATASET_INDEPENDENTLY_REVALIDATED`

This compact record closes only the archive-only data-provenance boundary from
`KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_PROTOCOL_V2.md`. The source ZIP files,
published dataset directory and canonical CSV files remain external to Git.

## Locked identity

- dataset: `kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2`;
- provider: `Kraken Spot`;
- source mode: `OFFICIAL_OHLCVT_ARCHIVES_ONLY`;
- research window: `2019-01-01T00:00:00Z` inclusive through
  `2026-04-01T00:00:00Z` exclusive;
- provider-audit normalized SHA-256:
  `fc71ff88e11b5984ebf5168fdbe09446554f720fc3ec0241eef0839ca90b3fca`;
- v2 protocol normalized SHA-256:
  `814cd561e1869023832315050683665c142f3b216ae354d45019a28edcc6a05a`;
- manifest SHA-256:
  `8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c`;
- network requests executed: `false`.

## Exact source evidence

| Filename | Role | Bytes | Members | SHA-256 |
|---|---|---:|---:|---|
| `Kraken_OHLCVT.zip` | `COMPLETE` | 7,885,068,519 | 24,056 | `e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d` |
| `Kraken_OHLCVT_Q1_2026.zip` | `QUARTERLY_UPDATE` | 545,431,093 | 10,269 | `95b2fec056bbacdfb5426e859a756d269bb19ba31eac7ea9e814759dfccd77b1` |

Both inputs were inventoried at `2026-08-27T19:18:31Z`. The canonical
`archive_inventory.json` records 34,325 members in 7,061,389 bytes with
SHA-256
`cbfc0963b5966a5f94f97ff90a1bd52761167e9846515aad2abe7a85f27882b2`.
The recorded and independently calculated inventory hashes matched exactly.

## Asset evidence

| Asset | Expected | Observed | Explicit missing UTC buckets | Canonical SHA-256 |
|---|---:|---:|---|---|
| `BTC-USD` | 2,647 | 2,646 | `2024-03-31T00:00:00Z` | `322fedfeac2857062ec54860554fe13bc4a285aeb46e47fd0597cc6d07f07657` |
| `ETH-USD` | 2,647 | 2,647 | none | `e810cbcf847fa9b44b30ac5671fa5b7c95816d0763762ccf3f7a33433d56f69c` |
| `XRP-USD` | 2,647 | 2,645 | `2022-05-11T00:00:00Z`; `2022-05-12T00:00:00Z` | `ad55ee7670417d69bf1cc9301afd359bd19ce3d9331b405027e8cf191247992c` |

Every asset begins at `2019-01-01T00:00:00Z` and ends at
`2026-03-31T00:00:00Z`. The complete archive contributed 2,556 BTC, 2,557 ETH
and 2,555 XRP rows. The Q1 update contributed exactly 90 additional rows per
asset from 2026-01-01 through 2026-03-31. No equal or conflicting cross-archive
duplicate occurred. Missing provider-native buckets remain
`NO_TRADE_UNAVAILABLE`; none was synthesized, forward-filled or replaced.

## Independent re-lock

`KrakenDailyDatasetLock` independently re-read the canonical manifest and
sidecar, revalidated both frozen contract-document hashes, exact source
identity, archive-inventory hash and all three canonical CSV hashes. It returned
`INDEPENDENT_RELOCK_PASS` with the same manifest SHA-256 and row counts above.

This proves data provenance only. Real chart replay, strategy execution,
performance evaluation, optimization, Candidate v2, PAPER, cloud and live
execution remain unauthorized and unexecuted. Real blinded-replay review is a
separate next authorization boundary.
