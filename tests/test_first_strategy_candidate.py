import hashlib
import json
import os
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from coinbase_research_dataset import (
    CoinbaseResearchDatasetBuilder,
    CoinbaseResearchDatasetContract,
)
from first_strategy_candidate import (
    BASELINE_COSTS,
    CANDIDATE_ID,
    PARAMETER_SET_ID,
    STRESSED_COSTS,
    STRATEGY_NAME,
    FirstStrategyCandidatePreregistration,
    first_candidate_configuration,
    first_candidate_strategy_engine,
    main,
)


def small_contract():
    return CoinbaseResearchDatasetContract(
        dataset_id="test-native-6h-lock-v1",
        products=("BTC-USD", "ETH-USD"),
        granularity_seconds=21600,
        start="2024-01-01T00:00:00Z",
        end="2024-01-02T00:00:00Z",
    )


def request_for(contract):
    rows = []
    for index, timestamp in enumerate(
        pd.date_range(
            contract.start_timestamp,
            contract.end_timestamp,
            freq="6h",
            inclusive="left",
        )
    ):
        open_price = 100.0 + index
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

    def request(_url, params, timeout):
        assert params["granularity"] == 21600
        assert timeout > 0.0
        return list(reversed(rows))

    return request


def build_dataset(tmp_path, contract=None):
    contract = contract or small_contract()
    result = CoinbaseResearchDatasetBuilder(
        contract=contract,
        request_fn=request_for(contract),
        request_pause_seconds=0.0,
        retry_backoff_seconds=0.0,
        sleep_fn=lambda _seconds: None,
    ).build(tmp_path)
    return contract, result


def rewrite_manifest(manifest_path, mutate):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mutate(manifest)
    payload = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    manifest_path.with_name("manifest.sha256").write_bytes(
        f"{digest}  manifest.json\n".encode("ascii")
    )


def test_declaration_freezes_candidate_before_any_evaluation():
    declaration = FirstStrategyCandidatePreregistration().declaration()

    assert declaration["status"] == "DATASET_LOCK_PENDING"
    assert declaration["candidate_id"] == CANDIDATE_ID
    assert declaration["strategy_name"] == STRATEGY_NAME == "ema_crossover"
    assert declaration["parameter_set_id"] == PARAMETER_SET_ID
    assert declaration["assets"] == ["BTC-USD", "ETH-USD"]
    assert declaration["timeframe"] == "6h"
    assert declaration["dataset_contract"]["expected_rows_per_product"] == 11076
    assert declaration["optimization_authorized"] is False
    assert declaration["evaluation_authorized_before_dataset_lock"] is False
    assert declaration["live_execution_authorized"] is False


def test_configuration_freezes_timing_windows_thresholds_and_costs():
    configuration = first_candidate_configuration()

    assert configuration.train_size == 2880
    assert configuration.test_size == configuration.step_size == 720
    assert configuration.expanding is True
    assert configuration.in_sample_fraction == pytest.approx(0.70)
    assert configuration.initial_capital == pytest.approx(5000.0)
    assert configuration.simulations == 5000
    assert configuration.confidence_level == pytest.approx(0.95)
    assert configuration.random_seed == 20260822
    assert configuration.min_positive_walk_forward_excess_rate == pytest.approx(0.60)
    assert configuration.min_assets == 2
    assert configuration.min_validated_asset_rate == pytest.approx(1.0)
    assert configuration.max_rejected_asset_rate == pytest.approx(0.0)
    assert configuration.min_walk_forward_windows == 5
    assert configuration.min_unseen_trades_per_asset == 30
    assert configuration.max_oos_drawdown_percent == pytest.approx(20.0)
    assert configuration.execution_timing == "next_bar_open"
    assert configuration.terminal_position_policy == "force_close_at_final_close"


def test_cost_profiles_are_conservative_and_stress_every_execution_component():
    assert BASELINE_COSTS.commission_rate == pytest.approx(0.006)
    assert BASELINE_COSTS.slippage_rate == pytest.approx(0.0005)
    assert BASELINE_COSTS.spread_rate == pytest.approx(0.001)
    assert STRESSED_COSTS.commission_rate == pytest.approx(0.006)
    assert STRESSED_COSTS.slippage_rate == pytest.approx(0.0015)
    assert STRESSED_COSTS.spread_rate == pytest.approx(0.003)
    assert STRESSED_COSTS.total_rate > BASELINE_COSTS.total_rate > 0.0


def test_strategy_engine_is_the_existing_ema_twenty_fifty_implementation():
    engine = first_candidate_strategy_engine()

    assert engine.strategy_name == "ema_crossover"
    assert engine.strategy.fast_period == 20
    assert engine.strategy.slow_period == 50


def test_preregistration_rejects_non_contract_input():
    with pytest.raises(TypeError, match="CoinbaseResearchDatasetContract"):
        FirstStrategyCandidatePreregistration(contract={})


def test_lock_binds_candidate_identity_to_verified_manifest_and_assets(tmp_path):
    contract, result = build_dataset(tmp_path)
    locked = FirstStrategyCandidatePreregistration(contract).lock(
        result["manifest_path"]
    )

    assert locked.manifest_sha256 == result["manifest_sha256"]
    assert locked.candidate.candidate_id == CANDIDATE_ID
    assert locked.candidate.strategy_name == STRATEGY_NAME
    assert locked.candidate.parameter_set_id == PARAMETER_SET_ID
    assert locked.candidate.assets == contract.products
    assert locked.candidate.timeframe == "6h"
    assert locked.candidate.data_version == (
        f"{contract.dataset_id};manifest_sha256={result['manifest_sha256']}"
    )
    assert locked.configuration == first_candidate_configuration()
    assert locked.strategy_engine.strategy.fast_period == 20
    assert set(locked.assets) == {"BTC-USD", "ETH-USD"}
    assert all(len(frame) == 4 for frame in locked.assets.values())
    assert all(frame.index.tz is not None for frame in locked.assets.values())


def test_lock_rejects_csv_tampering(tmp_path):
    contract, result = build_dataset(tmp_path)
    evidence = result["assets"]["BTC-USD"]
    path = tmp_path / evidence["file"]
    path.write_bytes(path.read_bytes().replace(b"100,102", b"101,102", 1))

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        FirstStrategyCandidatePreregistration(contract).lock(result["manifest_path"])


def test_lock_rejects_missing_or_invalid_manifest_sidecar(tmp_path):
    contract, result = build_dataset(tmp_path)
    checksum_path = result["checksum_path"]
    checksum_path.unlink()

    with pytest.raises(ValueError, match="sidecar is missing"):
        FirstStrategyCandidatePreregistration(contract).lock(result["manifest_path"])

    checksum_path.write_text("0" * 64 + "  manifest.json\n", encoding="ascii")
    with pytest.raises(ValueError, match="sidecar is invalid"):
        FirstStrategyCandidatePreregistration(contract).lock(result["manifest_path"])


def test_lock_rejects_noncanonical_or_wrong_contract_manifest(tmp_path):
    contract, result = build_dataset(tmp_path)
    manifest = json.loads(result["manifest_path"].read_text(encoding="utf-8"))
    result["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="not canonical"):
        FirstStrategyCandidatePreregistration(contract).lock(result["manifest_path"])


def test_lock_rejects_manifest_source_drift_even_with_recomputed_checksum(tmp_path):
    contract, result = build_dataset(tmp_path)
    rewrite_manifest(
        result["manifest_path"],
        lambda manifest: manifest["source"].__setitem__("provider", "different"),
    )

    with pytest.raises(ValueError, match="source contract"):
        FirstStrategyCandidatePreregistration(contract).lock(result["manifest_path"])


def test_lock_rejects_contract_drift_even_with_recomputed_checksum(tmp_path):
    contract, result = build_dataset(tmp_path)
    rewrite_manifest(
        result["manifest_path"],
        lambda manifest: manifest["contract"].__setitem__(
            "dataset_id", "post-result-mutation"
        ),
    )

    with pytest.raises(ValueError, match="frozen contract"):
        FirstStrategyCandidatePreregistration(contract).lock(result["manifest_path"])


def test_lock_revalidates_ohlcv_geometry_after_hashes_are_recomputed(tmp_path):
    contract, result = build_dataset(tmp_path)
    evidence = result["assets"]["BTC-USD"]
    csv_path = tmp_path / evidence["file"]
    frame = pd.read_csv(csv_path)
    frame.loc[0, "High"] = frame.loc[0, "Low"] - 1.0
    frame.to_csv(csv_path, index=False, lineterminator="\n")
    new_digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()

    def mutate(manifest):
        manifest["assets"]["BTC-USD"]["sha256"] = new_digest

    rewrite_manifest(result["manifest_path"], mutate)

    with pytest.raises(ValueError, match="OHLC geometry"):
        FirstStrategyCandidatePreregistration(contract).lock(result["manifest_path"])


def test_lock_rejects_path_escape_and_non_integer_row_evidence(tmp_path):
    contract, result = build_dataset(tmp_path)
    rewrite_manifest(
        result["manifest_path"],
        lambda manifest: manifest["assets"]["BTC-USD"].__setitem__(
            "file", "../btc.csv"
        ),
    )
    with pytest.raises(ValueError, match="basenames"):
        FirstStrategyCandidatePreregistration(contract).lock(result["manifest_path"])

    clean_dir = tmp_path / "clean"
    _, clean_result = build_dataset(clean_dir, contract)
    rewrite_manifest(
        clean_result["manifest_path"],
        lambda manifest: manifest["assets"]["BTC-USD"].__setitem__("rows", True),
    )
    with pytest.raises(ValueError, match="row evidence"):
        FirstStrategyCandidatePreregistration(contract).lock(
            clean_result["manifest_path"]
        )


def test_declaration_cli_prints_pending_identity_without_evaluation(capsys):
    assert main([]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "DATASET_LOCK_PENDING"
    assert output["candidate_id"] == CANDIDATE_ID
    assert output["evaluation_authorized_before_dataset_lock"] is False


def test_lock_cli_validates_default_contract_and_does_not_evaluate(
    tmp_path, capsys, monkeypatch
):
    contract, result = build_dataset(tmp_path)
    monkeypatch.setattr(
        "first_strategy_candidate.FIRST_CANDIDATE_DATASET_CONTRACT", contract
    )
    original_init = FirstStrategyCandidatePreregistration.__init__

    def test_init(self, contract_override=contract):
        original_init(self, contract_override)

    monkeypatch.setattr(FirstStrategyCandidatePreregistration, "__init__", test_init)

    assert main(["--manifest", str(result["manifest_path"])]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "DATASET_LOCKED"
    assert output["manifest_sha256"] == result["manifest_sha256"]
    assert output["asset_rows"] == {"BTC-USD": 4, "ETH-USD": 4}
    assert output["evaluation_executed"] is False
    assert output["optimization_authorized"] is False
    assert output["live_execution_authorized"] is False
