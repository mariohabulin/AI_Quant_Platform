import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_development_runner as development_module
from kraken_ai_driven_v2_development_runner import (
    AUTHORIZATION_PHRASE,
    CANONICAL_COLUMNS,
    DEVELOPMENT_RUN_ID,
    INITIAL_CAPITAL,
    REPORT_FILENAME,
    REPORT_SHA256_FILENAME,
    KrakenAIDrivenV2DevelopmentDatasetReader,
    KrakenAIDrivenV2DevelopmentEvidenceLock,
    KrakenAIDrivenV2DevelopmentRunner,
    LockedDevelopmentDataset,
    development_configuration,
)
from kraken_daily_dataset import CANONICAL_COLUMN_ORDER
from kraken_ai_driven_v2_features import FEATURE_COLUMNS
from kraken_ai_driven_v2_partition import (
    ASSET_ORDER,
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    KNOWN_GAPS_UTC,
    REFERENCE_PARTITION_CONTRACT,
)
from kraken_ai_driven_v2_state_machine import (
    ACTION_INTENT_COLUMN,
    INTENT_ENTER_NEXT_OPEN,
    INTENT_NONE,
    PARAMETER_SET_COLUMN,
    PARAMETER_SET_ID,
    SETUP_LOW_COLUMN,
    STATE_AFTER_COLUMN,
    STATE_FLAT,
    STATE_LONG,
    TRANSITION_COLUMN,
)


def development_frame(asset, price=100.0):
    index = REFERENCE_PARTITION_CONTRACT.expected_index(asset, "DEVELOPMENT")
    return pd.DataFrame(
        {
            "Open": price,
            "High": price + 2.0,
            "Low": price - 2.0,
            "Close": price,
            "Volume": 100.0,
        },
        index=index,
    )


def development_frames():
    return {asset: development_frame(asset) for asset in ASSET_ORDER}


class ControlledStateMachine:
    def __init__(self, asset, calls, signals=None):
        self.asset = asset
        self.calls = calls
        self.signals = signals or {}

    def generate(self, frame):
        self.calls.append((self.asset, frame.index.copy()))
        result = frame.copy(deep=True)
        result[ACTION_INTENT_COLUMN] = INTENT_NONE
        result[STATE_AFTER_COLUMN] = STATE_FLAT
        result[TRANSITION_COLUMN] = "FLAT_WAIT"
        result[SETUP_LOW_COLUMN] = float("nan")
        result[FEATURE_COLUMNS[2]] = 150.0
        result[FEATURE_COLUMNS[7]] = 4.0
        result[PARAMETER_SET_COLUMN] = PARAMETER_SET_ID
        for timestamp in self.signals.get(self.asset, ()):
            timestamp = pd.Timestamp(timestamp)
            if timestamp in result.index:
                result.loc[timestamp, ACTION_INTENT_COLUMN] = INTENT_ENTER_NEXT_OPEN
                result.loc[timestamp, STATE_AFTER_COLUMN] = STATE_LONG
                result.loc[timestamp, TRANSITION_COLUMN] = "CONFIRMATION_LONG"
                result.loc[timestamp, SETUP_LOW_COLUMN] = 90.0
        return result


def controlled_factory(calls, signals=None):
    return lambda asset: ControlledStateMachine(asset, calls, signals)


def locked_dataset(frames=None):
    selected = frames or development_frames()
    return LockedDevelopmentDataset(
        dataset_id=DATASET_ID,
        manifest_sha256=DATASET_MANIFEST_SHA256,
        source_mode="OFFICIAL_OHLCVT_ARCHIVES_ONLY",
        development_frames=selected,
        asset_file_sha256={asset: "a" * 64 for asset in ASSET_ORDER},
        full_observed_rows={"BTC-USD": 2646, "ETH-USD": 2647, "XRP-USD": 2645},
        opaque_non_development_rows={asset: 730 for asset in ASSET_ORDER},
        calibration_rows_parsed=0,
        evaluation_rows_parsed=0,
    )


def test_development_configuration_is_exact_and_nonpromoting():
    configuration = development_configuration()

    assert CANONICAL_COLUMNS == CANONICAL_COLUMN_ORDER
    assert configuration["development_run_id"] == DEVELOPMENT_RUN_ID
    assert configuration["partition"] == "DEVELOPMENT"
    assert configuration["initial_capital"] == INITIAL_CAPITAL == 5000.0
    assert configuration["quote_currency"] == "USD_RESEARCH_NOTIONAL"
    assert configuration["asset_order"] == list(ASSET_ORDER)
    assert configuration["same_timestamp_phase_order"] == [
        "EXISTING_POSITION_OPEN_EXITS",
        "PENDING_ENTRIES_IN_ASSET_ORDER",
        "ACTIVE_POSITION_INTRABAR_PROTECTION",
        "COMPLETED_BAR_EXIT_SCHEDULING",
        "CLOSE_LIQUIDATION_MARK",
    ]
    assert configuration["terminal_position_policy"] == (
        "PRESERVE_UNRESOLVED_NO_SYNTHETIC_FORCE_CLOSE"
    )
    assert configuration["parameter_sweep_authorized"] is False
    assert configuration["automatic_promotion_authorized"] is False
    assert configuration["calibration_access_authorized"] is False
    assert configuration["evaluation_access_authorized"] is False
    assert configuration["live_execution_authorized"] is False


def test_runner_validates_exact_development_rows_and_resets_every_segment():
    calls = []
    runner = KrakenAIDrivenV2DevelopmentRunner(
        state_machine_factory=controlled_factory(calls)
    )

    result = runner.execute_development(development_frames())

    assert result["status"] == "KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_FLAT"
    assert result["development_rows"] == {
        "BTC-USD": 1916,
        "ETH-USD": 1917,
        "XRP-USD": 1915,
    }
    assert [(asset, len(index)) for asset, index in calls] == [
        ("BTC-USD", 1916),
        ("ETH-USD", 1917),
        ("XRP-USD", 1226),
        ("XRP-USD", 689),
    ]
    assert result["continuous_segment_rows"] == {
        "BTC-USD": [1916],
        "ETH-USD": [1917],
        "XRP-USD": [1226, 689],
    }
    assert result["closed_trade_count"] == 0
    assert result["terminal_open_position_count"] == 0
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False


def test_calibration_or_evaluation_row_is_rejected_before_state_generation():
    frames = development_frames()
    extra = frames["ETH-USD"].iloc[[-1]].copy()
    extra.index = pd.DatetimeIndex([pd.Timestamp("2024-04-01T00:00:00Z")])
    frames["ETH-USD"] = pd.concat([frames["ETH-USD"], extra])
    calls = []
    runner = KrakenAIDrivenV2DevelopmentRunner(
        state_machine_factory=controlled_factory(calls)
    )

    with pytest.raises(ValueError, match="exact expected"):
        runner.execute_development(frames)

    assert calls == []


def test_source_frames_are_not_mutated():
    frames = development_frames()
    before = {asset: frame.copy(deep=True) for asset, frame in frames.items()}

    KrakenAIDrivenV2DevelopmentRunner(
        state_machine_factory=controlled_factory([])
    ).execute_development(frames)

    for asset in ASSET_ORDER:
        pd.testing.assert_frame_equal(frames[asset], before[asset])


def test_same_day_entries_use_fixed_asset_order_and_shared_portfolio_caps():
    signal_day = "2019-02-01T00:00:00Z"
    calls = []
    signals = {asset: (signal_day,) for asset in ASSET_ORDER}
    result = KrakenAIDrivenV2DevelopmentRunner(
        state_machine_factory=controlled_factory(calls, signals)
    ).execute_development(development_frames())

    assert result["approved_entry_count"] == 3
    assert [entry["asset"] for entry in result["entry_ledger"]] == list(ASSET_ORDER)
    assert result["maximum_concurrent_positions"] == 3
    assert result["maximum_planned_open_risk_fraction"] <= 0.015 + 1e-12
    assert result["real_orders_submitted"] is False


def test_entry_intent_is_canceled_when_following_day_is_known_gap():
    calls = []
    signals = {"XRP-USD": ("2022-05-10T00:00:00Z",)}
    result = KrakenAIDrivenV2DevelopmentRunner(
        state_machine_factory=controlled_factory(calls, signals)
    ).execute_development(development_frames())

    assert result["approved_entry_count"] == 0
    assert result["canceled_entry_intent_count"] == 1
    assert result["canceled_entry_intents"][0]["reason"] == (
        "FOLLOWING_OPEN_UNAVAILABLE_AT_RECORDED_GAP"
    )
    assert result["canceled_entry_intents"][0]["asset"] == "XRP-USD"


def test_open_position_at_gap_halts_fail_closed_without_fabricated_exit():
    calls = []
    signals = {"XRP-USD": ("2022-05-09T00:00:00Z",)}
    result = KrakenAIDrivenV2DevelopmentRunner(
        state_machine_factory=controlled_factory(calls, signals)
    ).execute_development(development_frames())

    assert result["status"] == (
        "KRAKEN_AI_V2_DEVELOPMENT_INCONCLUSIVE_OPEN_POSITION_AT_GAP"
    )
    assert result["path_completed"] is False
    assert result["halt_timestamp"] == "2022-05-11T00:00:00+00:00"
    assert result["halt_asset"] == "XRP-USD"
    assert result["terminal_open_position_count"] == 1
    assert result["synthetic_terminal_force_close_executed"] is False
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False


def test_terminal_position_is_marked_but_never_force_closed():
    calls = []
    signals = {"ETH-USD": ("2024-03-30T00:00:00Z",)}
    result = KrakenAIDrivenV2DevelopmentRunner(
        state_machine_factory=controlled_factory(calls, signals)
    ).execute_development(development_frames())

    assert result["status"] == (
        "KRAKEN_AI_V2_DEVELOPMENT_COMPLETED_WITH_UNRESOLVED_TERMINAL_POSITION"
    )
    assert result["path_completed"] is True
    assert result["terminal_open_position_count"] == 1
    assert result["synthetic_terminal_force_close_executed"] is False
    assert result["terminal_marked_equity"] < INITIAL_CAPITAL


class FakeReader:
    def __init__(self, locked):
        self.locked = locked
        self.calls = []

    def read(self, path):
        self.calls.append(Path(path))
        return self.locked


def test_wrong_authorization_phrase_touches_neither_dataset_nor_evidence(tmp_path):
    reader = FakeReader(locked_dataset())
    dataset = tmp_path / "dataset"
    evidence = tmp_path / "evidence"
    dataset.mkdir()

    with pytest.raises(PermissionError, match="authorization phrase"):
        KrakenAIDrivenV2DevelopmentRunner(
            dataset_reader=reader,
            state_machine_factory=controlled_factory([]),
        ).run(dataset, evidence, "WRONG")

    assert reader.calls == []
    assert not evidence.exists()


def test_one_shot_run_writes_canonical_atomic_evidence_and_refuses_repeat(tmp_path):
    reader = FakeReader(locked_dataset())
    dataset = tmp_path / "dataset"
    evidence = tmp_path / "evidence"
    dataset.mkdir()
    runner = KrakenAIDrivenV2DevelopmentRunner(
        dataset_reader=reader,
        state_machine_factory=controlled_factory([]),
    )

    recorded = runner.run(dataset, evidence, AUTHORIZATION_PHRASE)
    report_bytes = recorded.report_path.read_bytes()
    payload = json.loads(report_bytes.decode("utf-8"))

    assert recorded.status == "KRAKEN_AI_V2_DEVELOPMENT_EVIDENCE_RECORDED"
    assert hashlib.sha256(report_bytes).hexdigest() == recorded.report_sha256
    assert recorded.checksum_path.read_text(encoding="ascii") == (
        f"{recorded.report_sha256}  {REPORT_FILENAME}\n"
    )
    assert recorded.report_path.name == REPORT_FILENAME
    assert recorded.checksum_path.name == REPORT_SHA256_FILENAME
    assert payload["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert payload["dataset_opened"] is True
    assert payload["development_data_opened"] is True
    assert payload["calibration_data_opened"] is False
    assert payload["evaluation_data_opened"] is False
    assert payload["performance_evaluation_executed"] is True
    assert payload["development_run_authorized"] is True
    assert payload["development_run_executed"] is True
    assert payload["candidate_v2_authorized"] is False
    assert payload["live_execution_authorized"] is False

    with pytest.raises(FileExistsError, match="already exists"):
        runner.run(dataset, evidence, AUTHORIZATION_PHRASE)

    locked = KrakenAIDrivenV2DevelopmentEvidenceLock().lock(
        recorded.report_path.parent
    )
    assert locked.report_sha256 == recorded.report_sha256


def test_development_evidence_lock_rejects_report_tampering(tmp_path):
    reader = FakeReader(locked_dataset())
    dataset = tmp_path / "dataset"
    evidence = tmp_path / "evidence"
    dataset.mkdir()
    recorded = KrakenAIDrivenV2DevelopmentRunner(
        dataset_reader=reader,
        state_machine_factory=controlled_factory([]),
    ).run(dataset, evidence, AUTHORIZATION_PHRASE)
    recorded.report_path.write_bytes(recorded.report_path.read_bytes() + b"changed\n")

    with pytest.raises(ValueError, match="sidecar mismatch"):
        KrakenAIDrivenV2DevelopmentEvidenceLock().lock(
            recorded.report_path.parent
        )


def test_dataset_and_evidence_must_remain_external_and_disjoint(tmp_path):
    runner = KrakenAIDrivenV2DevelopmentRunner(
        dataset_reader=FakeReader(locked_dataset()),
        state_machine_factory=controlled_factory([]),
    )
    project_root = Path(development_module.__file__).resolve().parents[1]

    with pytest.raises(ValueError, match="outside the repository"):
        runner.run(project_root, tmp_path / "evidence", AUTHORIZATION_PHRASE)

    dataset = tmp_path / "dataset"
    dataset.mkdir()
    with pytest.raises(ValueError, match="must not overlap"):
        runner.run(dataset, dataset / "evidence", AUTHORIZATION_PHRASE)


def _canonical_manifest_bytes(payload):
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_synthetic_locked_dataset(root):
    root.mkdir()
    assets = {}
    full_counts = {"BTC-USD": 2646, "ETH-USD": 2647, "XRP-USD": 2645}
    full_index = pd.date_range(
        "2019-01-01T00:00:00Z",
        "2026-04-01T00:00:00Z",
        freq="D",
        inclusive="left",
    )
    for asset in ASSET_ORDER:
        gaps = pd.DatetimeIndex(
            [pd.Timestamp(value) for value in KNOWN_GAPS_UTC[asset]]
        )
        index = full_index.drop(gaps) if len(gaps) else full_index
        lines = ["Date,Open,High,Low,Close,Volume\n"]
        lines.extend(
            f"{timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')},100,102,98,100,10\n"
            for timestamp in index
        )
        raw = "".join(lines).encode("utf-8")
        filename = f"{asset.lower().replace('-', '_')}.csv"
        (root / filename).write_bytes(raw)
        assets[asset] = {
            "file": filename,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "observed_rows": full_counts[asset],
            "missing_timestamps": list(KNOWN_GAPS_UTC[asset]),
        }
    inventory = b"{}\n"
    (root / "archive_inventory.json").write_bytes(inventory)
    manifest = {
        "schema_version": 2,
        "dataset_id": DATASET_ID,
        "source_mode": "OFFICIAL_OHLCVT_ARCHIVES_ONLY",
        "network_requests_executed": False,
        "asset_order": list(ASSET_ORDER),
        "canonical_columns": ["Date", "Open", "High", "Low", "Close", "Volume"],
        "archive_inventory": {
            "file": "archive_inventory.json",
            "sha256": hashlib.sha256(inventory).hexdigest(),
        },
        "assets": assets,
    }
    manifest_bytes = _canonical_manifest_bytes(manifest)
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    (root / "manifest.json").write_bytes(manifest_bytes)
    (root / "manifest.sha256").write_text(
        f"{digest}  manifest.json\n", encoding="ascii"
    )
    return digest


def test_dataset_reader_hashes_full_files_but_parses_development_only(
    tmp_path, monkeypatch
):
    dataset = tmp_path / "locked"
    digest = _write_synthetic_locked_dataset(dataset)
    monkeypatch.setattr(development_module, "DATASET_MANIFEST_SHA256", digest)

    locked = KrakenAIDrivenV2DevelopmentDatasetReader().read(dataset)

    assert locked.manifest_sha256 == digest
    assert locked.full_observed_rows == {
        "BTC-USD": 2646,
        "ETH-USD": 2647,
        "XRP-USD": 2645,
    }
    assert locked.opaque_non_development_rows == {
        "BTC-USD": 730,
        "ETH-USD": 730,
        "XRP-USD": 730,
    }
    assert locked.calibration_rows_parsed == 0
    assert locked.evaluation_rows_parsed == 0
    for asset in ASSET_ORDER:
        frame = locked.frame(asset)
        assert len(frame) == {"BTC-USD": 1916, "ETH-USD": 1917, "XRP-USD": 1915}[asset]
        assert frame.index.max() < pd.Timestamp("2024-04-01T00:00:00Z")
        assert frame.dtypes.eq("float64").all()


def test_real_reader_rows_reach_risk_adapter_as_supported_numeric_values(
    tmp_path, monkeypatch
):
    dataset = tmp_path / "locked"
    evidence = tmp_path / "evidence"
    digest = _write_synthetic_locked_dataset(dataset)
    monkeypatch.setattr(development_module, "DATASET_MANIFEST_SHA256", digest)
    signal_day = "2019-02-01T00:00:00Z"
    signals = {asset: (signal_day,) for asset in ASSET_ORDER}
    runner = KrakenAIDrivenV2DevelopmentRunner(
        state_machine_factory=controlled_factory([], signals)
    )

    recorded = runner.run(dataset, evidence, AUTHORIZATION_PHRASE)

    assert recorded.status == "KRAKEN_AI_V2_DEVELOPMENT_EVIDENCE_RECORDED"
    assert recorded.closed_trade_count == 3


def test_dataset_reader_rejects_asset_byte_tampering(tmp_path, monkeypatch):
    dataset = tmp_path / "locked"
    digest = _write_synthetic_locked_dataset(dataset)
    monkeypatch.setattr(development_module, "DATASET_MANIFEST_SHA256", digest)
    with (dataset / "btc_usd.csv").open("ab") as target:
        target.write(b"changed\n")

    with pytest.raises(ValueError, match="asset SHA-256"):
        KrakenAIDrivenV2DevelopmentDatasetReader().read(dataset)
