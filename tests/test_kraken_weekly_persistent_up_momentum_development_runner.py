from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_weekly_persistent_up_momentum_development_runner as runner_module
from kraken_weekly_persistent_up_momentum_development_runner import (
    ASSET_ORDER,
    AUTHORIZATION_PHRASE,
    COMPONENT_ID,
    CONTROL_ORDER,
    DECISIONS_FILENAME,
    DECLARATION_FALSE_FLAGS,
    EVIDENCE_FILE_ORDER,
    EXPECTED_DEVELOPMENT_CALENDAR_ROWS,
    EXPECTED_DEVELOPMENT_SOURCE,
    FAILURE_STATUS,
    FINAL_DIRECTORY_NAME,
    FROZEN_ARCHIVE_SPEC,
    IMPLEMENTATION_TRUE_FLAGS,
    MEMBER_BASENAME_BY_ASSET,
    PARENT_COMMIT,
    PASS_STATUS,
    PRIMARY_RULE_ID,
    PROTOCOL_ID,
    READER_PASS_STATUS,
    REPORT_FILENAME,
    RULE_ORDER,
    RUNNER_SYNTHETIC_TEST_TOKEN,
    STAGING_DIRECTORY_NAME,
    KrakenWeeklyPersistentUpMomentumDevelopmentRunner,
    _evaluate_trusted_development_rows,
    _TRUSTED_ADAPTER_CAPABILITY,
    canonical_json_bytes,
    evaluate_development_gates_synthetic_fixture,
    evaluate_runner_adapter_synthetic_fixture,
    read_weekly_development_evidence,
    runner_declaration,
)
from kraken_weekly_persistent_up_momentum_synthetic import (
    SYNTHETIC_AUTHORIZATION_TOKEN,
    evaluate_synthetic_weekly_fixture,
)


ROOT = Path(__file__).resolve().parents[1]


def _iso(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _synthetic_daily_rows(week_count=10):
    start = datetime(2019, 2, 4, tzinfo=timezone.utc)
    rows = {asset: [] for asset in ASSET_ORDER}
    for asset_number, asset in enumerate(ASSET_ORDER):
        for day in range(week_count * 7):
            timestamp = start + timedelta(days=day)
            week = day // 7
            price = Decimal(100 + asset_number * 20 + week)
            rows[asset].append(
                {
                    "timestamp": _iso(timestamp),
                    "open": str(price),
                    "high": str(price + 1),
                    "low": str(price - 1),
                    "close": str(price),
                    "volume": str(1000 + day),
                    "trades": 10 + day,
                }
            )
    return rows


def _normalized_decisions(decisions, *, synthetic):
    result = deepcopy(decisions)
    if synthetic:
        for decision in result:
            for action in decision["rule_actions"].values():
                if action["outcome"].get("status") == "VALID_SYNTHETIC_OUTCOME":
                    action["outcome"]["status"] = "VALID_DEVELOPMENT_OUTCOME"
    return result


def _valid_outcome(baseline, stress):
    return {
        "status": "VALID_DEVELOPMENT_OUTCOME",
        "cost_profiles": {
            "KRAKEN_BASELINE_ADVERSE": {"net_return": str(baseline)},
            "KRAKEN_STRESS_ADVERSE": {"net_return": str(stress)},
        },
    }


def _gate_decision(asset, timestamp, primary="0.10", control_1="0.01", control_2="0.02"):
    return {
        "asset": asset,
        "decision_week_start": timestamp,
        "rule_actions": {
            PRIMARY_RULE_ID: {
                "action": "LONG",
                "outcome": _valid_outcome(primary, primary),
            },
            CONTROL_ORDER[0]: {
                "action": "LONG",
                "outcome": _valid_outcome(control_1, control_1),
            },
            CONTROL_ORDER[1]: {
                "action": "LONG",
                "outcome": _valid_outcome(control_2, control_2),
            },
        },
    }


def _passing_gate_decisions():
    starts = (
        datetime(2019, 2, 11, tzinfo=timezone.utc),
        datetime(2020, 1, 6, tzinfo=timezone.utc),
        datetime(2021, 1, 4, tzinfo=timezone.utc),
        datetime(2022, 1, 3, tzinfo=timezone.utc),
        datetime(2023, 1, 2, tzinfo=timezone.utc),
    )
    decisions = []
    for asset in ASSET_ORDER[:2]:
        for start in starts:
            for week in range(6):
                decisions.append(_gate_decision(asset, _iso(start + timedelta(weeks=week))))
    return decisions


def _member_evidence():
    result = []
    for asset in ASSET_ORDER:
        expected = EXPECTED_DEVELOPMENT_SOURCE[asset]
        result.append(
            {
                "asset": asset,
                "member_name": f"nested/{MEMBER_BASENAME_BY_ASSET[asset]}",
                "member_basename": MEMBER_BASENAME_BY_ASSET[asset],
                "compressed_bytes": 100,
                "uncompressed_bytes": 200,
                "crc32": "0123abcd",
                "member_uncompressed_sha256": "a" * 64,
                "development_rows": expected["observed_rows"],
                "expected_calendar_rows": EXPECTED_DEVELOPMENT_CALENDAR_ROWS,
                "missing_development_timestamps": list(expected["missing_timestamps"]),
                "first_development_timestamp": expected["first_timestamp"],
                "last_development_timestamp": expected["last_timestamp"],
                "nondevelopment_timestamp_tokens_read": True,
                "nondevelopment_market_values_parsed": False,
            }
        )
    return result


def _small_archive_rows(start, days, bad_value=None):
    result = {}
    for asset_number, asset in enumerate(ASSET_ORDER):
        lines = []
        before = int((start - timedelta(days=1)).timestamp())
        after = int((start + timedelta(days=days)).timestamp())
        lines.append(f"{before},NOT_PARSED,x,x,x,x,x\n")
        for day in range(days):
            timestamp = int((start + timedelta(days=day)).timestamp())
            value = 100 + asset_number + day
            open_value = bad_value if bad_value is not None and day == 2 and asset_number == 0 else value
            lines.append(
                f"{timestamp},{open_value},{value + 2},{value - 2},{value + 1},{1000 + day},{10 + day}\n"
            )
        lines.append(f"{after},NOT_PARSED,x,x,x,x,x\n")
        result[asset] = "".join(lines).encode("ascii")
    return result


def _write_archive(path, member_bytes, extra_members=None):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for asset in ASSET_ORDER:
            archive.writestr(
                f"nested/{MEMBER_BASENAME_BY_ASSET[asset]}", member_bytes[asset]
            )
        for name, payload in (extra_members or {}).items():
            archive.writestr(name, payload)
    return path


def _patch_small_contract(monkeypatch, archive_path, start, days):
    end = start + timedelta(days=days)
    expected = {
        asset: {
            "observed_rows": days,
            "first_timestamp": _iso(start),
            "last_timestamp": _iso(end - timedelta(days=1)),
            "missing_timestamps": (),
        }
        for asset in ASSET_ORDER
    }
    payload = archive_path.read_bytes()
    monkeypatch.setattr(runner_module, "DEVELOPMENT_START", _iso(start))
    monkeypatch.setattr(runner_module, "DEVELOPMENT_END_EXCLUSIVE", _iso(end))
    monkeypatch.setattr(runner_module, "EXPECTED_DEVELOPMENT_CALENDAR_ROWS", days)
    monkeypatch.setattr(runner_module, "EXPECTED_DEVELOPMENT_SOURCE", expected)
    monkeypatch.setattr(
        runner_module,
        "FROZEN_ARCHIVE_SPEC",
        {
            "filename": archive_path.name,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
    )


def _run_synthetic_package(tmp_path, monkeypatch):
    archive = tmp_path / "Kraken_OHLCVT.zip"
    archive.write_bytes(b"synthetic archive placeholder")
    evidence_root = tmp_path / "evidence"
    monkeypatch.setattr(runner_module, "EXPECTED_INVALID_MARKET_WEEK_STARTS", ())
    monkeypatch.setattr(
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner,
        "_validate_archive",
        staticmethod(lambda _path: dict(FROZEN_ARCHIVE_SPEC)),
    )
    monkeypatch.setattr(
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner,
        "_load_development_rows",
        classmethod(lambda cls, _path: (_synthetic_daily_rows(), _member_evidence())),
    )
    recorded = KrakenWeeklyPersistentUpMomentumDevelopmentRunner().run(
        archive, evidence_root, AUTHORIZATION_PHRASE
    )
    return evidence_root / FINAL_DIRECTORY_NAME, recorded


def test_runner_declaration_is_implemented_but_inert():
    result = runner_declaration()

    assert result["protocol_id"] == PROTOCOL_ID
    assert result["component_id"] == COMPONENT_ID
    assert result["parent_commit"] == PARENT_COMMIT
    assert PARENT_COMMIT == "0b51b8455f218793605cc6da086862e96776e50d"
    assert result["authorization_phrase"] == AUTHORIZATION_PHRASE
    assert result["synthetic_engine_token_reused"] is False
    assert result["model_artifact_count"] == 0
    assert all(result[name] is True for name in IMPLEMENTATION_TRUE_FLAGS)
    assert all(result[name] is False for name in DECLARATION_FALSE_FLAGS)
    assert result["next_stage"] == "SEPARATE_READ_ONLY_DEVELOPMENT_PREFLIGHT_DECISION"


def test_runner_synthetic_token_is_distinct_and_required():
    rows = _synthetic_daily_rows()

    assert RUNNER_SYNTHETIC_TEST_TOKEN != SYNTHETIC_AUTHORIZATION_TOKEN
    with pytest.raises(PermissionError, match="runner synthetic-fixture"):
        evaluate_runner_adapter_synthetic_fixture(rows, authorization_token="wrong")
    with pytest.raises(PermissionError, match="runner synthetic-fixture"):
        evaluate_runner_adapter_synthetic_fixture(
            rows, authorization_token=SYNTHETIC_AUTHORIZATION_TOKEN
        )


def test_private_trusted_adapter_requires_unforgeable_capability():
    with pytest.raises(PermissionError, match="capability"):
        _evaluate_trusted_development_rows(_synthetic_daily_rows(), capability=object())


def test_trusted_adapter_has_exact_synthetic_engine_parity():
    rows = _synthetic_daily_rows()
    synthetic = evaluate_synthetic_weekly_fixture(
        rows, authorization_token=SYNTHETIC_AUTHORIZATION_TOKEN
    )
    trusted = evaluate_runner_adapter_synthetic_fixture(
        rows, authorization_token=RUNNER_SYNTHETIC_TEST_TOKEN
    )

    synthetic_aggregation = deepcopy(synthetic["aggregation"])
    trusted_aggregation = deepcopy(trusted["aggregation"])
    for payload in (synthetic_aggregation, trusted_aggregation):
        payload.pop("status")
        payload.pop("input_mode")
    assert trusted_aggregation == synthetic_aggregation
    assert trusted["decision_count"] == synthetic["decision_count"]
    assert trusted["long_decision_count_by_rule"] == synthetic["long_decision_count_by_rule"]
    assert trusted["valid_outcome_count_by_rule"] == synthetic[
        "valid_synthetic_outcome_count_by_rule"
    ]
    assert trusted["invalid_outcome_count_by_rule"] == synthetic[
        "invalid_synthetic_outcome_count_by_rule"
    ]
    assert trusted["decisions"] == _normalized_decisions(
        synthetic["decisions"], synthetic=True
    )
    assert trusted["source_values_opened"] is False
    assert trusted["development_run_executed"] is False


def test_gate_evaluator_passes_only_the_exact_cross_asset_contract():
    result = evaluate_development_gates_synthetic_fixture(
        _passing_gate_decisions(), authorization_token=RUNNER_SYNTHETIC_TEST_TOKEN
    )

    assert result["development_viable"] is True
    assert result["learning_status"] == PASS_STATUS
    assert result["action"] == "HOLD_CASH"
    assert result["passing_asset_order"] == ["BTC-USD", "ETH-USD"]
    assert result["control_comparison_win_asset_order"] == ["BTC-USD", "ETH-USD"]
    assert all(result["cross_asset_gates"].values())
    assert result["candidate_v2_authorized"] is False
    assert result["development_gates_executed_on_real_data"] is False


def test_gate_evaluator_records_exact_means_slices_and_concentration():
    result = evaluate_development_gates_synthetic_fixture(
        _passing_gate_decisions(), authorization_token=RUNNER_SYNTHETIC_TEST_TOKEN
    )
    review = result["primary_asset_reviews"]["BTC-USD"]

    assert review["valid_event_count"] == 30
    assert review["overall_mean_net_return"]["KRAKEN_BASELINE_ADVERSE"] == "0.1"
    assert [item["valid_event_count"] for item in review["slice_summaries"]] == [
        6,
        6,
        6,
        6,
        6,
    ]
    assert review["largest_positive_baseline_event_share"] == (
        "0.033333333333333333333333333333333333333333333333333"
    )
    assert all(review["gates"].values())


def test_gate_evaluator_keeps_empty_means_null_and_fails_closed():
    result = evaluate_development_gates_synthetic_fixture(
        [], authorization_token=RUNNER_SYNTHETIC_TEST_TOKEN
    )
    summary = result["rule_summaries"][PRIMARY_RULE_ID]["BTC-USD"]

    assert summary["valid_event_count"] == 0
    assert summary["overall_mean_net_return"]["KRAKEN_BASELINE_ADVERSE"] is None
    assert result["development_viable"] is False
    assert result["learning_status"] == FAILURE_STATUS
    assert result["action"] == "HOLD_CASH"


def test_invalid_future_boundary_is_diagnostic_not_gate_support():
    decision = _gate_decision("BTC-USD", "2019-02-11T00:00:00Z")
    decision["rule_actions"][PRIMARY_RULE_ID]["outcome"] = {
        "status": "INVALID_MISSING_FUTURE_BOUNDARY"
    }
    result = evaluate_development_gates_synthetic_fixture(
        [decision], authorization_token=RUNNER_SYNTHETIC_TEST_TOKEN
    )
    summary = result["rule_summaries"][PRIMARY_RULE_ID]["BTC-USD"]

    assert summary["valid_event_count"] == 0
    assert summary["invalid_future_boundary_count"] == 1


def test_gate_evaluator_rejects_nonfinite_returns():
    decision = _gate_decision("BTC-USD", "2019-02-11T00:00:00Z")
    decision["rule_actions"][PRIMARY_RULE_ID]["outcome"]["cost_profiles"][
        "KRAKEN_BASELINE_ADVERSE"
    ]["net_return"] = "NaN"

    with pytest.raises(RuntimeError, match="non-finite"):
        evaluate_development_gates_synthetic_fixture(
            [decision], authorization_token=RUNNER_SYNTHETIC_TEST_TOKEN
        )


def test_large_single_winner_fails_concentration_gate():
    decisions = _passing_gate_decisions()
    first = next(
        item
        for item in decisions
        if item["asset"] == "BTC-USD"
    )
    first["rule_actions"][PRIMARY_RULE_ID]["outcome"] = _valid_outcome("100", "0.1")
    result = evaluate_development_gates_synthetic_fixture(
        decisions, authorization_token=RUNNER_SYNTHETIC_TEST_TOKEN
    )

    review = result["primary_asset_reviews"]["BTC-USD"]
    assert review["gates"]["positive_profit_concentration"] is False
    assert review["passes_all_asset_gates"] is False


def test_controls_can_block_cross_asset_viability_but_never_become_candidate():
    decisions = _passing_gate_decisions()
    for decision in decisions:
        if decision["asset"] == "ETH-USD":
            decision["rule_actions"][CONTROL_ORDER[0]]["outcome"] = _valid_outcome(
                "0.20", "0.20"
            )
    result = evaluate_development_gates_synthetic_fixture(
        decisions, authorization_token=RUNNER_SYNTHETIC_TEST_TOKEN
    )

    assert result["passing_asset_order"] == ["BTC-USD", "ETH-USD"]
    assert result["control_comparison_win_asset_order"] == ["BTC-USD"]
    assert result["development_viable"] is False
    assert result["candidate_v2_authorized"] is False


def test_archive_validator_accepts_only_exact_filename_size_and_hash(tmp_path, monkeypatch):
    archive = tmp_path / "Kraken_OHLCVT.zip"
    archive.write_bytes(b"fixture")
    monkeypatch.setattr(
        runner_module,
        "FROZEN_ARCHIVE_SPEC",
        {
            "filename": archive.name,
            "bytes": len(archive.read_bytes()),
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        },
    )

    assert KrakenWeeklyPersistentUpMomentumDevelopmentRunner._validate_archive(
        archive
    ) == runner_module.FROZEN_ARCHIVE_SPEC


@pytest.mark.parametrize("failure", ("filename", "bytes", "sha256"))
def test_archive_validator_rejects_each_identity_mismatch(tmp_path, monkeypatch, failure):
    archive = tmp_path / "Kraken_OHLCVT.zip"
    archive.write_bytes(b"fixture")
    spec = {
        "filename": archive.name,
        "bytes": len(archive.read_bytes()),
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    }
    if failure == "filename":
        spec["filename"] = "wrong.zip"
    elif failure == "bytes":
        spec["bytes"] += 1
    else:
        spec["sha256"] = "0" * 64
    monkeypatch.setattr(runner_module, "FROZEN_ARCHIVE_SPEC", spec)

    with pytest.raises((ValueError, RuntimeError), match="filename|byte-size|SHA256"):
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner._validate_archive(archive)


def test_member_reader_parses_only_development_values_and_hashes_whole_member(
    tmp_path, monkeypatch
):
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    archive = _write_archive(
        tmp_path / "Kraken_OHLCVT.zip", _small_archive_rows(start, 7)
    )
    _patch_small_contract(monkeypatch, archive, start, 7)

    source_evidence = KrakenWeeklyPersistentUpMomentumDevelopmentRunner._validate_archive(
        archive
    )
    rows, member_evidence = (
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner._load_development_rows(
            archive
        )
    )

    assert source_evidence == runner_module.FROZEN_ARCHIVE_SPEC
    assert {asset: len(values) for asset, values in rows.items()} == {
        asset: 7 for asset in ASSET_ORDER
    }
    assert all(len(item["member_uncompressed_sha256"]) == 64 for item in member_evidence)
    assert all(item["nondevelopment_timestamp_tokens_read"] is True for item in member_evidence)
    assert all(item["nondevelopment_market_values_parsed"] is False for item in member_evidence)


def test_member_reader_rejects_duplicate_required_basename(tmp_path, monkeypatch):
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    source = _small_archive_rows(start, 7)
    archive = _write_archive(
        tmp_path / "Kraken_OHLCVT.zip",
        source,
        {"duplicate/XBTUSD_1440.csv": source["BTC-USD"]},
    )
    _patch_small_contract(monkeypatch, archive, start, 7)

    with pytest.raises(RuntimeError, match="exactly one XBTUSD"):
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner._load_development_rows(
            archive
        )


def test_member_reader_rejects_invalid_development_value(tmp_path, monkeypatch):
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    archive = _write_archive(
        tmp_path / "Kraken_OHLCVT.zip",
        _small_archive_rows(start, 7, bad_value="NOT_A_DECIMAL"),
    )
    _patch_small_contract(monkeypatch, archive, start, 7)

    with pytest.raises(RuntimeError, match="Invalid exact decimal Open"):
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner._load_development_rows(
            archive
        )


def test_wrong_authorization_fails_before_any_path_access(monkeypatch):
    monkeypatch.setattr(
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner,
        "_external_paths",
        staticmethod(lambda *_args: (_ for _ in ()).throw(AssertionError("opened"))),
    )

    with pytest.raises(PermissionError, match="authorization"):
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner().run(
            "missing.zip", "missing-evidence", "wrong"
        )


def test_synthetic_end_to_end_package_is_atomic_and_reader_recomputes(
    tmp_path, monkeypatch
):
    final, recorded = _run_synthetic_package(tmp_path, monkeypatch)

    assert final.is_dir()
    assert not (tmp_path / "evidence" / STAGING_DIRECTORY_NAME).exists()
    assert {item.name for item in final.iterdir()} == set(EVIDENCE_FILE_ORDER)
    assert recorded.report_path == final / REPORT_FILENAME
    locked = read_weekly_development_evidence(final)
    assert locked["status"] == READER_PASS_STATUS
    assert locked["report_sha256"] == recorded.report_sha256
    assert locked["learning_status"] == FAILURE_STATUS
    assert locked["action"] == "HOLD_CASH"
    assert locked["source_archive_opened_by_reader"] is False
    assert locked["evidence_files_written_by_reader"] is False


def test_evidence_sidecars_are_binary_canonical_lf(tmp_path, monkeypatch):
    final, _ = _run_synthetic_package(tmp_path, monkeypatch)

    for filename in (REPORT_FILENAME, DECISIONS_FILENAME):
        sidecar = (final / f"{filename}.sha256").read_bytes()
        assert sidecar.endswith(b"\n")
        assert b"\r\n" not in sidecar
        digest = hashlib.sha256((final / filename).read_bytes()).hexdigest()
        assert sidecar == f"{digest}  {filename}\n".encode("ascii")


def test_independent_reader_writes_nothing_and_never_opens_archive(
    tmp_path, monkeypatch
):
    final, _ = _run_synthetic_package(tmp_path, monkeypatch)
    before = {item.name: item.read_bytes() for item in final.iterdir()}
    monkeypatch.setattr(
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner,
        "_validate_archive",
        staticmethod(lambda _path: (_ for _ in ()).throw(AssertionError("opened"))),
    )

    read_weekly_development_evidence(final)

    after = {item.name: item.read_bytes() for item in final.iterdir()}
    assert after == before


def test_independent_reader_rejects_sidecar_tamper(tmp_path, monkeypatch):
    final, _ = _run_synthetic_package(tmp_path, monkeypatch)
    sidecar = final / f"{REPORT_FILENAME}.sha256"
    sidecar.write_bytes(b"0" * 64 + f"  {REPORT_FILENAME}\n".encode("ascii"))

    with pytest.raises(RuntimeError, match="sidecar mismatch"):
        read_weekly_development_evidence(final)


def test_independent_reader_rejects_extra_file(tmp_path, monkeypatch):
    final, _ = _run_synthetic_package(tmp_path, monkeypatch)
    (final / "unexpected.txt").write_bytes(b"unexpected")

    with pytest.raises(RuntimeError, match="file registry"):
        read_weekly_development_evidence(final)


def test_independent_reader_rejects_recomputed_gate_mismatch(tmp_path, monkeypatch):
    final, _ = _run_synthetic_package(tmp_path, monkeypatch)
    report_path = final / REPORT_FILENAME
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["gate_review"]["development_viable"] = True
    raw = canonical_json_bytes(report)
    report_path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (final / f"{REPORT_FILENAME}.sha256").write_bytes(
        f"{digest}  {REPORT_FILENAME}\n".encode("ascii")
    )

    with pytest.raises(RuntimeError, match="gate recomputation"):
        read_weekly_development_evidence(final)


def test_one_shot_refuses_existing_final_evidence(tmp_path):
    evidence = tmp_path / "evidence"
    (evidence / FINAL_DIRECTORY_NAME).mkdir(parents=True)

    with pytest.raises(FileExistsError, match="final evidence"):
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner._assert_one_shot(evidence)


def test_one_shot_refuses_existing_staging_evidence(tmp_path):
    evidence = tmp_path / "evidence"
    (evidence / STAGING_DIRECTORY_NAME).mkdir(parents=True)

    with pytest.raises(FileExistsError, match="staging evidence"):
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner._assert_one_shot(evidence)


def test_failure_preserves_staging_and_publishes_no_final(tmp_path, monkeypatch):
    archive = tmp_path / "Kraken_OHLCVT.zip"
    archive.write_bytes(b"fixture")
    evidence_root = tmp_path / "evidence"
    monkeypatch.setattr(
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner,
        "_validate_archive",
        staticmethod(lambda _path: (_ for _ in ()).throw(RuntimeError("synthetic failure"))),
    )

    with pytest.raises(RuntimeError, match="synthetic failure"):
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner().run(
            archive, evidence_root, AUTHORIZATION_PHRASE
        )

    assert (evidence_root / STAGING_DIRECTORY_NAME).is_dir()
    assert not (evidence_root / FINAL_DIRECTORY_NAME).exists()


def test_external_path_guard_rejects_repository_paths():
    source = ROOT / "Kraken_OHLCVT.zip"
    evidence = ROOT.parent / "external-evidence"

    with pytest.raises(ValueError, match="external"):
        KrakenWeeklyPersistentUpMomentumDevelopmentRunner._external_paths(
            source, evidence
        )
