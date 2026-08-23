import hashlib
import json
import os
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from coinbase_research_dataset import CoinbaseResearchDatasetContract
from sparse_coinbase_research_dataset import (
    SPARSE_DATASET_MANIFEST_SCHEMA_VERSION,
    SPARSE_NATIVE_GAP_POLICY,
    SparseCoinbaseResearchDatasetBuilder,
    SparseCoinbaseResearchDatasetLock,
)


def small_contract(products=("BTC-USD", "ETH-USD"), hours=8):
    return CoinbaseResearchDatasetContract(
        dataset_id="test-observed-native-1h-gap-aware-v2",
        products=products,
        granularity_seconds=3600,
        start="2024-01-01T00:00:00Z",
        end=(pd.Timestamp("2024-01-01T00:00:00Z") + pd.Timedelta(hours=hours))
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def candle_rows(contract, offset=0.0):
    rows = []
    for position, timestamp in enumerate(
        pd.date_range(
            contract.start_timestamp,
            contract.end_timestamp,
            freq="h",
            inclusive="left",
        )
    ):
        open_price = 100.0 + offset + position
        rows.append(
            [
                int(timestamp.timestamp()),
                open_price - 1.0,
                open_price + 1.0,
                open_price,
                open_price + 0.5,
                10.0 + position,
            ]
        )
    return rows


def sparse_builder(contract, missing_by_product, calls=None):
    calls = [] if calls is None else calls

    def request(url, params, timeout):
        assert timeout > 0.0
        product_id = "ETH-USD" if "ETH-USD" in url else "BTC-USD"
        calls.append((product_id, params.copy()))
        missing = set(missing_by_product.get(product_id, ()))
        offset = 100.0 if product_id == "ETH-USD" else 0.0
        return [
            row
            for row in candle_rows(contract, offset)
            if pd.Timestamp(row[0], unit="s", tz="UTC") not in missing
        ]

    return SparseCoinbaseResearchDatasetBuilder(
        contract,
        request_fn=request,
        request_pause_seconds=0.0,
        retry_backoff_seconds=0.0,
        sleep_fn=lambda _seconds: None,
    )


def rewrite_manifest(path, mutator):
    path = Path(path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mutator(manifest)
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    path.with_name("manifest.sha256").write_bytes(
        f"{digest}  manifest.json\n".encode("ascii")
    )


def test_sparse_builder_records_exact_provider_gaps_without_synthetic_rows(tmp_path):
    contract = small_contract()
    btc_gap = contract.start_timestamp + pd.Timedelta(hours=2)
    eth_gap = contract.start_timestamp + pd.Timedelta(hours=5)
    calls = []

    result = sparse_builder(
        contract,
        {"BTC-USD": (btc_gap,), "ETH-USD": (eth_gap,)},
        calls,
    ).build(tmp_path / "1h")

    manifest = json.loads(result["manifest_path"].read_bytes())
    assert manifest["schema_version"] == SPARSE_DATASET_MANIFEST_SCHEMA_VERSION
    assert manifest["gap_policy"] == SPARSE_NATIVE_GAP_POLICY
    assert result["manifest_sha256"] == hashlib.sha256(
        result["manifest_path"].read_bytes()
    ).hexdigest()

    for product_id, missing in (("BTC-USD", btc_gap), ("ETH-USD", eth_gap)):
        evidence = manifest["assets"][product_id]
        frame = pd.read_csv(result["manifest_path"].parent / evidence["file"])
        assert evidence["expected_rows"] == 8
        assert evidence["rows"] == 7
        assert evidence["missing_rows"] == 1
        assert evidence["missing_timestamps"] == [
            missing.strftime("%Y-%m-%dT%H:%M:%SZ")
        ]
        assert evidence["max_consecutive_missing_buckets"] == 1
        assert evidence["recovery_status"] == "exhausted_2_passes"
        assert len(frame) == 7
        assert missing.strftime("%Y-%m-%dT%H:%M:%SZ") not in set(
            frame["Timestamp"]
        )

    assert len(calls) == 6


def test_sparse_builder_can_recover_to_a_complete_grid_and_lock_it(tmp_path):
    contract = small_contract(products=("BTC-USD",))
    rows = candle_rows(contract)
    missing_row = rows[3]
    calls = []

    def transient_gap(_url, params, timeout):
        assert timeout > 0.0
        calls.append(params.copy())
        if len(calls) == 1:
            return rows[:3] + rows[4:]
        return [missing_row]

    builder = SparseCoinbaseResearchDatasetBuilder(
        contract,
        request_fn=transient_gap,
        request_pause_seconds=0.0,
        retry_backoff_seconds=0.0,
        sleep_fn=lambda _seconds: None,
    )
    result = builder.build(tmp_path / "1h")
    evidence = result["assets"]["BTC-USD"]

    assert evidence["rows"] == evidence["expected_rows"] == 8
    assert evidence["missing_rows"] == 0
    assert evidence["missing_timestamps"] == []
    assert evidence["recovery_status"] == "recovered_pass_1"
    locked = SparseCoinbaseResearchDatasetLock(contract).lock(
        result["manifest_path"]
    )
    assert len(locked.assets["BTC-USD"]) == 8


def test_sparse_builder_refuses_too_many_or_too_long_gaps_before_writing(tmp_path):
    too_many_contract = small_contract(products=("BTC-USD",), hours=51)
    all_missing = tuple(
        pd.date_range(
            too_many_contract.start_timestamp,
            too_many_contract.end_timestamp,
            freq="h",
            inclusive="left",
        )
    )
    too_many_output = tmp_path / "too_many"

    with pytest.raises(RuntimeError, match="missing bucket limit"):
        sparse_builder(
            too_many_contract,
            {"BTC-USD": all_missing},
        ).build(too_many_output)
    assert not too_many_output.exists()

    long_contract = small_contract(products=("BTC-USD",), hours=30)
    long_gap = tuple(
        pd.date_range(
            long_contract.start_timestamp,
            periods=25,
            freq="h",
        )
    )
    long_output = tmp_path / "too_long"
    with pytest.raises(RuntimeError, match="consecutive missing bucket limit"):
        sparse_builder(long_contract, {"BTC-USD": long_gap}).build(long_output)
    assert not long_output.exists()


def test_sparse_build_is_atomic_across_assets_and_refuses_staging_retry(tmp_path):
    contract = small_contract()
    output = tmp_path / "1h"

    def failed_eth(url, params, timeout):
        if "ETH-USD" in url:
            raise OSError("provider unavailable")
        return candle_rows(contract)

    builder = SparseCoinbaseResearchDatasetBuilder(
        contract,
        request_fn=failed_eth,
        request_pause_seconds=0.0,
        retry_backoff_seconds=0.0,
        sleep_fn=lambda _seconds: None,
    )
    with pytest.raises(RuntimeError, match="request failed"):
        builder.build(output)
    assert not output.exists()

    staging = output.with_name(".1h.staging")
    staging.mkdir()
    with pytest.raises(FileExistsError, match="staging"):
        sparse_builder(contract, {}).build(output)


def test_sparse_lock_revalidates_exact_missing_grid_and_gap_policy(tmp_path):
    contract = small_contract()
    gaps = {
        "BTC-USD": (contract.start_timestamp + pd.Timedelta(hours=2),),
        "ETH-USD": (contract.start_timestamp + pd.Timedelta(hours=5),),
    }
    result = sparse_builder(contract, gaps).build(tmp_path / "1h")

    locked = SparseCoinbaseResearchDatasetLock(contract).lock(
        result["manifest_path"]
    )

    assert locked.contract == contract
    assert locked.manifest_sha256 == result["manifest_sha256"]
    assert len(locked.assets["BTC-USD"]) == 7
    assert locked.assets["BTC-USD"].index.is_monotonic_increasing
    assert gaps["BTC-USD"][0] not in locked.assets["BTC-USD"].index


@pytest.mark.parametrize(
    "mutator, message",
    [
        (
            lambda manifest: manifest["assets"]["BTC-USD"].__setitem__(
                "missing_timestamps", []
            ),
            "missing timestamp evidence",
        ),
        (
            lambda manifest: manifest["gap_policy"].__setitem__(
                "synthetic_candles_allowed", True
            ),
            "gap policy",
        ),
    ],
)
def test_sparse_lock_rejects_manifest_gap_tampering(tmp_path, mutator, message):
    contract = small_contract()
    gap = contract.start_timestamp + pd.Timedelta(hours=2)
    result = sparse_builder(
        contract,
        {"BTC-USD": (gap,), "ETH-USD": ()},
    ).build(tmp_path / "1h")
    rewrite_manifest(result["manifest_path"], mutator)

    with pytest.raises(ValueError, match=message):
        SparseCoinbaseResearchDatasetLock(contract).lock(result["manifest_path"])
