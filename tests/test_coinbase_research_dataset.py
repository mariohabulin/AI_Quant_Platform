import hashlib
import json
import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from coinbase_research_dataset import (
    ALLOWED_GRANULARITIES,
    CANONICAL_COLUMN_ORDER,
    DATASET_MANIFEST_SCHEMA_VERSION,
    FIRST_CANDIDATE_DATASET_CONTRACT,
    CoinbaseResearchDatasetBuilder,
    CoinbaseResearchDatasetContract,
    CoinbaseResearchDatasetLock,
    dataset_canonicalization_metadata,
    dataset_source_metadata,
)


def small_contract(products=("BTC-USD", "ETH-USD")):
    return CoinbaseResearchDatasetContract(
        dataset_id="test-native-6h-v1",
        products=products,
        granularity_seconds=21600,
        start="2024-01-01T00:00:00Z",
        end="2024-01-02T00:00:00Z",
    )


def candle_rows(contract, price_offset=0.0):
    rows = []
    for index, timestamp in enumerate(
        pd.date_range(
            contract.start_timestamp,
            contract.end_timestamp,
            freq=pd.Timedelta(seconds=contract.granularity_seconds),
            inclusive="left",
        )
    ):
        open_price = 100.0 + price_offset + index
        rows.append(
            [
                int(timestamp.timestamp()),
                open_price - 2.0,
                open_price + 2.0,
                open_price,
                open_price + 1.0,
                10.0 + index,
            ]
        )
    return rows


def request_for(contract, calls=None):
    calls = [] if calls is None else calls

    def request(url, params, timeout):
        calls.append((url, params.copy(), timeout))
        offset = 100.0 if "ETH-USD" in url else 0.0
        return list(reversed(candle_rows(contract, offset)))

    return request


def builder(contract, request_fn=None, **overrides):
    values = {
        "contract": contract,
        "request_fn": request_fn or request_for(contract),
        "request_pause_seconds": 0.0,
        "retry_backoff_seconds": 0.0,
        "sleep_fn": lambda _seconds: None,
    }
    values.update(overrides)
    return CoinbaseResearchDatasetBuilder(**values)


def test_first_candidate_contract_is_exact_and_continuous():
    contract = FIRST_CANDIDATE_DATASET_CONTRACT

    assert contract.dataset_id == (
        "coinbase-exchange-btc-eth-native-6h-20190101-20260801-v1"
    )
    assert contract.products == ("BTC-USD", "ETH-USD")
    assert contract.granularity_seconds == 21600
    assert contract.timeframe == "6h"
    assert contract.start == "2019-01-01T00:00:00Z"
    assert contract.end == "2026-08-01T00:00:00Z"
    assert contract.expected_rows_per_product == 11076
    assert contract.as_dict()["range_semantics"] == (
        "start_inclusive_end_exclusive"
    )


def test_contract_normalizes_scope_and_rejects_invalid_values():
    contract = small_contract(products=(" eth-usd ", "btc-usd"))
    assert contract.products == ("BTC-USD", "ETH-USD")
    assert contract.expected_rows_per_product == 4
    assert contract.granularity_seconds in ALLOWED_GRANULARITIES

    with pytest.raises(TypeError, match="product ID"):
        small_contract(products=("BTC-USD", 42))
    with pytest.raises(ValueError, match="duplicates"):
        small_contract(products=("BTC-USD", "btc-usd"))
    with pytest.raises(ValueError, match="granularity"):
        CoinbaseResearchDatasetContract(
            "bad", ("BTC-USD",), 7200,
            "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"
        )
    with pytest.raises(ValueError, match="align"):
        CoinbaseResearchDatasetContract(
            "bad", ("BTC-USD",), 21600,
            "2024-01-01T01:00:00Z", "2024-01-02T00:00:00Z"
        )


def test_builder_requests_native_six_hour_rows_and_returns_exact_grid():
    contract = small_contract(products=("BTC-USD",))
    calls = []
    frame = builder(contract, request_for(contract, calls)).fetch_product("btc-usd")

    assert list(frame.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(frame) == 4
    assert frame.index.is_monotonic_increasing
    assert frame.index[0] == contract.start_timestamp
    assert frame.index[-1] == contract.end_timestamp - pd.Timedelta(hours=6)
    assert calls[0][1]["granularity"] == 21600
    assert calls[0][1]["start"] == "2024-01-01T00:00:00Z"
    assert calls[0][1]["end"] == "2024-01-02T00:00:00Z"


def test_builder_rejects_products_outside_frozen_scope():
    with pytest.raises(ValueError, match="outside"):
        builder(small_contract()).fetch_product("SOL-USD")


def test_builder_rejects_missing_candle():
    contract = small_contract(products=("BTC-USD",))

    with pytest.raises(RuntimeError, match="missing=1"):
        builder(contract, lambda *_args, **_kwargs: candle_rows(contract)[:-1]).fetch_product(
            "BTC-USD"
        )


@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda rows: rows.__setitem__(0, rows[0][:-1]), "row is invalid"),
        (lambda rows: rows[0].__setitem__(2, rows[0][1] - 1.0), "geometry"),
        (lambda rows: rows[0].__setitem__(3, float("nan")), "finite"),
        (lambda rows: rows[0].__setitem__(5, -1.0), "volume"),
    ],
)
def test_builder_rejects_invalid_provider_rows(mutator, message):
    contract = small_contract(products=("BTC-USD",))
    rows = candle_rows(contract)
    mutator(rows)

    with pytest.raises(RuntimeError, match=message):
        builder(contract, lambda *_args, **_kwargs: rows).fetch_product("BTC-USD")


def test_builder_rejects_conflicting_duplicate():
    contract = small_contract(products=("BTC-USD",))
    rows = candle_rows(contract)
    duplicate = list(rows[0])
    duplicate[4] += 0.5
    rows.append(duplicate)

    with pytest.raises(RuntimeError, match="Conflicting duplicate"):
        builder(contract, lambda *_args, **_kwargs: rows).fetch_product("BTC-USD")


def test_builder_retries_with_a_finite_attempt_budget():
    contract = small_contract(products=("BTC-USD",))
    attempts = []
    sleeps = []

    def flaky_request(*_args, **_kwargs):
        attempts.append(len(attempts) + 1)
        if len(attempts) < 3:
            raise OSError("temporary network failure")
        return candle_rows(contract)

    frame = builder(
        contract,
        flaky_request,
        max_attempts=3,
        retry_backoff_seconds=1.0,
        sleep_fn=sleeps.append,
    ).fetch_product("BTC-USD")

    assert len(frame) == 4
    assert attempts == [1, 2, 3]
    assert sleeps == [1.0, 2.0]


def test_builder_fails_closed_after_retry_budget_is_exhausted():
    contract = small_contract(products=("BTC-USD",))
    attempts = []

    def failed_request(*_args, **_kwargs):
        attempts.append(1)
        raise OSError("offline")

    with pytest.raises(RuntimeError, match="after 2 attempts"):
        builder(contract, failed_request, max_attempts=2).fetch_product("BTC-USD")
    assert len(attempts) == 2


def test_build_writes_canonical_assets_manifest_and_sha_sidecar(tmp_path):
    contract = small_contract()
    result = builder(contract).build(tmp_path)

    manifest_bytes = result["manifest_path"].read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest_bytes == (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert manifest["schema_version"] == DATASET_MANIFEST_SCHEMA_VERSION
    assert manifest["contract"] == contract.as_dict()
    assert manifest["source"] == dataset_source_metadata()
    assert manifest["canonicalization"] == dataset_canonicalization_metadata()
    assert result["manifest_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
    assert result["checksum_path"].read_text(encoding="ascii") == (
        f"{result['manifest_sha256']}  manifest.json\n"
    )

    for product_id, evidence in result["assets"].items():
        path = tmp_path / evidence["file"]
        assert path.read_bytes().endswith(b"\n")
        assert b"\r\n" not in path.read_bytes()
        assert path.read_text(encoding="utf-8").splitlines()[0].split(",") == list(
            CANONICAL_COLUMN_ORDER
        )
        assert evidence["rows"] == 4
        assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence["sha256"]
        assert product_id in {"BTC-USD", "ETH-USD"}


def test_build_refuses_accidental_overwrite_and_non_boolean_policy(tmp_path):
    frozen_builder = builder(small_contract())
    frozen_builder.build(tmp_path)

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        frozen_builder.build(tmp_path)
    with pytest.raises(TypeError, match="Overwrite"):
        frozen_builder.build(tmp_path, overwrite=1)


def test_build_overwrite_reproduces_identical_manifest_hash(tmp_path):
    frozen_builder = builder(small_contract())
    first = frozen_builder.build(tmp_path)
    second = frozen_builder.build(tmp_path, overwrite=True)

    assert first["manifest_sha256"] == second["manifest_sha256"]
    assert first["assets"] == second["assets"]


def test_generic_dataset_lock_revalidates_canonical_manifest_and_assets(tmp_path):
    contract = small_contract()
    result = builder(contract).build(tmp_path)

    locked = CoinbaseResearchDatasetLock(contract).lock(result["manifest_path"])

    assert locked.contract == contract
    assert locked.manifest_sha256 == result["manifest_sha256"]
    assert locked.manifest["contract"] == contract.as_dict()
    assert set(locked.assets) == {"BTC-USD", "ETH-USD"}
    assert all(len(frame) == 4 for frame in locked.assets.values())


def test_generic_dataset_lock_rejects_invalid_contract_and_tampering(tmp_path):
    with pytest.raises(TypeError, match="CoinbaseResearchDatasetContract"):
        CoinbaseResearchDatasetLock({})

    contract = small_contract()
    result = builder(contract).build(tmp_path)
    asset_path = tmp_path / result["assets"]["BTC-USD"]["file"]
    asset_path.write_bytes(asset_path.read_bytes() + b"tampered")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        CoinbaseResearchDatasetLock(contract).lock(result["manifest_path"])
