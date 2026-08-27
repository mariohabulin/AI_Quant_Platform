import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import zipfile

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_daily_dataset import (
    ARCHIVE_COMPLETE_FILENAME,
    ASSET_ORDER,
    CANONICAL_COLUMN_ORDER,
    DATASET_ID,
    PROVIDER_AUDIT_NORMALIZED_SHA256,
    RESEARCH_END_EXCLUSIVE,
    RESEARCH_START_INCLUSIVE,
    ArchiveInput,
    KrakenDailyDatasetBuilder,
    KrakenDailyDatasetContract,
    KrakenDailyDatasetLock,
    build_review_declaration,
    load_provider_audit,
    main,
    normalized_text_sha256,
)


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_AUDIT = ROOT / "BTC_ETH_XRP_PROVIDER_AND_HISTORICAL_AVAILABILITY_AUDIT_V1.md"
LOCK_PROTOCOL = ROOT / "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_PROTOCOL_V1.md"


PAIR_STEMS = {
    "BTC-USD": "XBTUSD",
    "ETH-USD": "ETHUSD",
    "XRP-USD": "XRPUSD",
}


def unix(day):
    from datetime import datetime, timezone

    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())


def row(day, price, volume="10", trades=5):
    price = str(price)
    return [unix(day), price, price, price, price, str(volume), trades]


def csv_bytes(rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def write_archive(path, rows_by_asset, extra_members=None):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", b"synthetic test archive")
        for asset, rows in rows_by_asset.items():
            archive.writestr(
                f"nested/{PAIR_STEMS[asset]}_1440.csv",
                csv_bytes(rows),
            )
        for name, payload in (extra_members or {}).items():
            archive.writestr(name, payload)
    return path


def rest_bytes(asset, committed_rows, current_row=None, errors=None):
    key = {
        "BTC-USD": "BTC/USD",
        "ETH-USD": "ETH/USD",
        "XRP-USD": "XRP/USD",
    }[asset]

    def rest_row(archive_row):
        timestamp, open_, high, low, close, volume, trades = archive_row
        return [timestamp, open_, high, low, close, close, volume, trades]

    rows = [rest_row(value) for value in committed_rows]
    rows.append(rest_row(current_row or row("2024-01-06", "999")))
    payload = {
        "error": errors or [],
        "result": {key: rows, "last": rows[-1][0]},
    }
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def small_contract():
    return KrakenDailyDatasetContract(
        dataset_id="kraken-test-daily-v1",
        start="2024-01-01T00:00:00Z",
        end="2024-01-06T00:00:00Z",
    )


def fixture_inputs(tmp_path, archive_rows):
    complete = write_archive(
        tmp_path / ARCHIVE_COMPLETE_FILENAME,
        {asset: archive_rows[asset] for asset in ASSET_ORDER},
        extra_members={"nested/XBTUSD_60.csv": b"ignored\n"},
    )
    return (
        ArchiveInput(
            path=complete,
            role="COMPLETE",
            source_url="https://drive.google.com/official-complete",
            retrieved_at="2026-08-27T12:00:00Z",
        ),
    )


def builder(tmp_path, archive_rows, rest_rows=None, **overrides):
    inputs = fixture_inputs(tmp_path, archive_rows)
    rest_rows = archive_rows if rest_rows is None else rest_rows

    def request(asset, _since):
        return rest_bytes(asset, rest_rows[asset])

    values = {
        "contract": small_contract(),
        "archive_inputs": inputs,
        "rest_request_fn": request,
        "provider_audit_path": PROVIDER_AUDIT,
        "retrieved_at": "2026-08-27T12:05:00Z",
    }
    values.update(overrides)
    return KrakenDailyDatasetBuilder(**values)


def base_rows():
    return {
        asset: [
            row("2024-01-01", "100"),
            row("2024-01-02", "101"),
            row("2024-01-03", "102"),
            row("2024-01-04", "103"),
        ]
        for asset in ASSET_ORDER
    }


def test_production_contract_is_exact_and_non_performance():
    contract = KrakenDailyDatasetContract()

    assert contract.dataset_id == DATASET_ID
    assert contract.assets == ASSET_ORDER
    assert contract.start == RESEARCH_START_INCLUSIVE
    assert contract.end == RESEARCH_END_EXCLUSIVE
    assert contract.interval_minutes == 1440
    assert contract.expected_daily_buckets == 2769
    assert contract.as_dict()["range_semantics"] == "START_INCLUSIVE_END_EXCLUSIVE"


def test_review_declaration_authorizes_only_bounded_data_acquisition():
    declaration = build_review_declaration(PROVIDER_AUDIT)

    assert declaration["status"] == "KRAKEN_DAILY_DATASET_BUILDER_REVIEWED_ACQUISITION_REQUIRED"
    assert declaration["provider_audit_sha256_match"] is True
    assert declaration["bounded_data_acquisition_review_eligible"] is True
    assert declaration["data_acquisition_executed"] is False
    assert declaration["byte_level_historical_bucket_inventory_completed"] is False
    assert declaration["all_asset_dataset_locked"] is False
    assert declaration["real_chart_replay_authorized"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["cloud_execution_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_review_cli_is_non_networked_and_reports_json(capsys):
    assert main(["--provider-audit", str(PROVIDER_AUDIT)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == build_review_declaration(PROVIDER_AUDIT)
    assert payload["network_requests_executed"] is False


def test_protocol_and_project_documents_preserve_the_non_performance_boundary():
    protocol = LOCK_PROTOCOL.read_text(encoding="utf-8")
    assert "BUILDER_REVIEWED_ACQUISITION_NOT_EXECUTED" in protocol
    assert PROVIDER_AUDIT_NORMALIZED_SHA256 in protocol
    assert "Q2 2026" in protocol
    assert "did not contain" in protocol
    assert "NO_TRADE_UNAVAILABLE" in protocol
    assert "real chart replay authorized: `false`" in protocol
    assert "performance evaluation executed: `false`" in protocol
    assert "live execution authorized: `false`" in protocol

    for name in ("VISION.md", "ROADMAP.md", "ARCHITECTURE.md", "CURRENT_MISSION.md", "LOG.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "Kraken" in text
        assert "daily" in text.lower()


def test_provider_audit_is_hash_bound_and_tampering_fails(tmp_path):
    _, digest = load_provider_audit(PROVIDER_AUDIT)

    assert digest == PROVIDER_AUDIT_NORMALIZED_SHA256
    assert normalized_text_sha256(PROVIDER_AUDIT) == digest

    changed = tmp_path / "audit.md"
    changed.write_text(
        PROVIDER_AUDIT.read_text(encoding="utf-8") + "\nchanged\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        load_provider_audit(changed)


def test_contract_rejects_scope_or_alignment_changes():
    with pytest.raises(ValueError, match="asset order"):
        KrakenDailyDatasetContract(assets=("BTC-USD",))
    with pytest.raises(ValueError, match="UTC midnight"):
        KrakenDailyDatasetContract(start="2024-01-01T01:00:00Z")
    with pytest.raises(ValueError, match="after start"):
        KrakenDailyDatasetContract(
            start="2024-01-01T00:00:00Z",
            end="2024-01-01T00:00:00Z",
        )


def test_archive_input_requires_existing_zip_explicit_role_url_and_time(tmp_path):
    path = tmp_path / "source.zip"
    write_archive(path, {asset: [] for asset in ASSET_ORDER})
    source = ArchiveInput(path, "complete", "https://example.test/source", "2026-08-27T12:00:00Z")
    assert source.role == "COMPLETE"

    with pytest.raises(ValueError, match="role"):
        ArchiveInput(path, "OTHER", "https://example.test", "2026-08-27T12:00:00Z")
    with pytest.raises(ValueError, match="HTTPS"):
        ArchiveInput(path, "COMPLETE", "http://example.test", "2026-08-27T12:00:00Z")
    with pytest.raises(FileNotFoundError):
        ArchiveInput(tmp_path / "missing.zip", "COMPLETE", "https://example.test", "2026-08-27T12:00:00Z")


def test_builder_requires_exactly_one_complete_archive(tmp_path):
    rows = base_rows()
    source = fixture_inputs(tmp_path, rows)[0]

    with pytest.raises(ValueError, match="exactly one COMPLETE"):
        KrakenDailyDatasetBuilder(
            contract=small_contract(),
            archive_inputs=(ArchiveInput(source.path, "QUARTERLY_UPDATE", source.source_url, source.retrieved_at),),
            rest_request_fn=lambda *_: b"{}",
            provider_audit_path=PROVIDER_AUDIT,
            retrieved_at="2026-08-27T12:00:00Z",
        )


def test_archive_inventory_covers_every_member_but_selects_only_native_daily(tmp_path):
    rows = base_rows()
    frozen = builder(tmp_path, rows)

    inventory, selected = frozen.inventory_archives()

    assert len(inventory["archives"]) == 1
    source = inventory["archives"][0]
    assert source["member_count"] == 5
    assert {member["name"] for member in source["members"]} == {
        "README.txt",
        "nested/XBTUSD_60.csv",
        "nested/XBTUSD_1440.csv",
        "nested/ETHUSD_1440.csv",
        "nested/XRPUSD_1440.csv",
    }
    assert set(selected) == set(ASSET_ORDER)
    assert all(len(items) == 1 for items in selected.values())
    assert source["sha256"] == hashlib.sha256(frozen.archive_inputs[0].path.read_bytes()).hexdigest()


def test_archive_inventory_rejects_missing_or_duplicate_required_member(tmp_path):
    rows = base_rows()
    rows.pop("XRP-USD")
    frozen = builder(tmp_path, {**rows, "XRP-USD": []})
    archive = frozen.archive_inputs[0].path
    archive.unlink()
    write_archive(archive, rows)
    with pytest.raises(RuntimeError, match="XRP-USD.*1440"):
        frozen.inventory_archives()

    archive.unlink()
    write_archive(
        archive,
        base_rows(),
        extra_members={"other/XBTUSD_1440.csv": csv_bytes(base_rows()["BTC-USD"])},
    )
    with pytest.raises(RuntimeError, match="multiple.*BTC-USD"):
        frozen.inventory_archives()


@pytest.mark.parametrize(
    "mutator,message",
    [
        (lambda values: values[0].__setitem__(0, values[0][0] + 3600), "UTC midnight"),
        (lambda values: values[0].__setitem__(2, "99"), "geometry"),
        (lambda values: values[0].__setitem__(5, "-1"), "volume"),
        (lambda values: values[0].__setitem__(6, 0), "trade count"),
        (lambda values: values[0].append("extra"), "seven columns"),
    ],
)
def test_archive_parser_rejects_invalid_native_rows(tmp_path, mutator, message):
    rows = base_rows()
    mutator(rows["BTC-USD"])
    frozen = builder(tmp_path, rows)

    with pytest.raises(RuntimeError, match=message):
        frozen.load_archive_rows()


def test_identical_archive_updates_merge_but_conflicts_fail(tmp_path):
    rows = base_rows()
    frozen = builder(tmp_path, rows)
    update_path = write_archive(
        tmp_path / "Kraken_OHLCVT_Q1_2024.zip",
        {asset: rows[asset][2:] for asset in ASSET_ORDER},
    )
    update = ArchiveInput(
        update_path,
        "QUARTERLY_UPDATE",
        "https://drive.google.com/official-quarter",
        "2026-08-27T12:01:00Z",
    )
    merged = KrakenDailyDatasetBuilder(
        contract=small_contract(),
        archive_inputs=(*frozen.archive_inputs, update),
        rest_request_fn=frozen.rest_request_fn,
        provider_audit_path=PROVIDER_AUDIT,
        retrieved_at="2026-08-27T12:05:00Z",
    ).load_archive_rows()
    assert all(len(asset_rows) == 4 for asset_rows in merged["rows"].values())
    assert all(value == 2 for value in merged["equal_duplicates"].values())

    conflict = base_rows()
    conflict["BTC-USD"][2] = row("2024-01-03", "777")
    update_path.unlink()
    write_archive(update_path, {asset: conflict[asset][2:] for asset in ASSET_ORDER})
    with pytest.raises(RuntimeError, match="Conflicting duplicate.*BTC-USD"):
        KrakenDailyDatasetBuilder(
            contract=small_contract(),
            archive_inputs=(*frozen.archive_inputs, update),
            rest_request_fn=frozen.rest_request_fn,
            provider_audit_path=PROVIDER_AUDIT,
            retrieved_at="2026-08-27T12:05:00Z",
        ).load_archive_rows()


def test_rest_current_bar_is_removed_and_raw_response_is_hashed(tmp_path):
    rows = base_rows()
    frozen = builder(tmp_path, rows)

    result = frozen.load_rest_rows("BTC-USD")

    assert len(result["rows"]) == 4
    assert unix("2024-01-06") not in result["rows"]
    assert result["sha256"] == hashlib.sha256(result["raw_bytes"]).hexdigest()
    assert result["uncommitted_last_bar_removed"] is True


@pytest.mark.parametrize(
    "payload,message",
    [
        (json.dumps({"error": ["EGeneral:Failure"], "result": {}}).encode(), "provider error"),
        (b"not-json", "valid JSON"),
        (json.dumps({"error": [], "result": {"last": 1}}).encode(), "one pair key"),
    ],
)
def test_rest_parser_fails_closed_on_invalid_provider_response(tmp_path, payload, message):
    rows = base_rows()
    frozen = builder(tmp_path, rows, rest_request_fn=lambda *_: payload)
    with pytest.raises(RuntimeError, match=message):
        frozen.load_rest_rows("BTC-USD")


def test_rest_pair_identity_cannot_be_swapped_between_assets(tmp_path):
    rows = base_rows()
    wrong = json.loads(rest_bytes("ETH-USD", rows["ETH-USD"]).decode("utf-8"))
    frozen = builder(
        tmp_path,
        rows,
        rest_request_fn=lambda *_: json.dumps(wrong).encode("utf-8"),
    )

    with pytest.raises(RuntimeError, match="pair identity mismatch.*BTC-USD"):
        frozen.load_rest_rows("BTC-USD")


def test_exact_archive_rest_overlap_is_required_for_every_asset(tmp_path):
    rows = base_rows()
    no_overlap = {
        asset: [row("2024-01-05", "104")]
        for asset in ASSET_ORDER
    }
    frozen = builder(tmp_path, rows, rest_rows=no_overlap)

    with pytest.raises(RuntimeError, match="overlap.*BTC-USD"):
        frozen.build(tmp_path / "out")


def test_archive_rest_overlap_mismatch_writes_no_final_dataset(tmp_path):
    rows = base_rows()
    rest_rows = base_rows()
    rest_rows["ETH-USD"][2] = row("2024-01-03", "999")
    frozen = builder(tmp_path, rows, rest_rows=rest_rows)
    output = tmp_path / "out"

    with pytest.raises(RuntimeError, match="REST overlap mismatch.*ETH-USD"):
        frozen.build(output)

    assert not (output / small_contract().dataset_id).exists()


def test_build_locks_observed_rows_gaps_segments_hashes_and_safety_state(tmp_path):
    rows = base_rows()
    for asset in ASSET_ORDER:
        rows[asset].pop(1)
    rest_rows = {
        asset: [rows[asset][-1], row("2024-01-05", "104")]
        for asset in ASSET_ORDER
    }
    frozen = builder(tmp_path, rows, rest_rows=rest_rows)

    result = frozen.build(tmp_path / "out")
    final = result["dataset_path"]
    manifest_bytes = (final / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)

    assert final.name == small_contract().dataset_id
    assert result["status"] == "LOCKED_NON_PERFORMANCE_DATASET"
    assert manifest_bytes == (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    assert result["manifest_sha256"] == hashlib.sha256(manifest_bytes).hexdigest()
    assert (final / "manifest.sha256").read_text(encoding="ascii") == (
        f"{result['manifest_sha256']}  manifest.json\n"
    )
    assert manifest["provider_audit_sha256"] == PROVIDER_AUDIT_NORMALIZED_SHA256
    assert manifest["byte_level_historical_bucket_inventory_completed"] is True
    assert manifest["all_asset_dataset_locked"] is True
    assert manifest["real_chart_replay_authorized"] is False
    assert manifest["performance_evaluation_executed"] is False
    assert manifest["live_execution_authorized"] is False
    assert manifest["archive_inventory"]["member_count"] == 5
    assert (final / manifest["archive_inventory"]["file"]).exists()

    for asset in ASSET_ORDER:
        evidence = manifest["assets"][asset]
        assert evidence["expected_daily_buckets"] == 5
        assert evidence["observed_rows"] == 4
        assert evidence["missing_timestamps"] == ["2024-01-02T00:00:00Z"]
        assert evidence["missing_interval_trading_state"] == "NO_TRADE_UNAVAILABLE"
        assert len(evidence["continuous_segments"]) == 2
        assert evidence["rest_overlap"]["exact_match"] is True
        assert evidence["rest_overlap"]["row_count"] == 1
        canonical = final / evidence["file"]
        assert hashlib.sha256(canonical.read_bytes()).hexdigest() == evidence["sha256"]
        assert canonical.read_text(encoding="utf-8").splitlines()[0].split(",") == list(CANONICAL_COLUMN_ORDER)
        assert "2024-01-02T00:00:00Z" not in canonical.read_text(encoding="utf-8")


def test_build_refuses_overwrite_and_lock_revalidates_every_hash(tmp_path):
    rows = base_rows()
    rest_rows = {
        asset: [rows[asset][-1], row("2024-01-05", "104")]
        for asset in ASSET_ORDER
    }
    frozen = builder(tmp_path, rows, rest_rows=rest_rows)
    result = frozen.build(tmp_path / "out")

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        frozen.build(tmp_path / "out")

    lock = KrakenDailyDatasetLock(small_contract()).lock(result["dataset_path"])
    assert lock.manifest_sha256 == result["manifest_sha256"]
    assert tuple(lock.assets) == ASSET_ORDER

    target = result["dataset_path"] / lock.manifest["assets"]["XRP-USD"]["file"]
    target.write_bytes(target.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        KrakenDailyDatasetLock(small_contract()).lock(result["dataset_path"])
