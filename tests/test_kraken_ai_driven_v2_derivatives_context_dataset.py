import csv
import hashlib
import io
import os
from pathlib import Path
import sys
import zipfile

import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_derivatives_context_dataset as dataset
from kraken_ai_driven_v2_derivatives_context_dataset import (
    ASSET_SYMBOLS,
    AUTHORIZATION_PHRASE,
    COMMON_END_EXCLUSIVE_UTC,
    COMMON_START_UTC,
    DATASET_ID,
    DerivativesContextDatasetLocker,
    FUNDING_HEADER,
    KLINE_HEADER,
    KLINE_DOCUMENTED_HEADER,
    METRICS_HEADER,
    SOURCE_SPECS,
    dataset_lock_declaration,
    expected_object_registry,
    parse_official_checksum,
    read_locked_derivatives_context_dataset,
    validate_source_archive,
)


def _csv_bytes(rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _zip_payload(spec, member_bytes, member_name=None):
    member_name = spec["filename"][:-4] + ".csv" if member_name is None else member_name
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member_name, member_bytes)
    payload = output.getvalue()
    checksum = f"{hashlib.sha256(payload).hexdigest()}  {spec['filename']}\n".encode()
    return payload, checksum


def _spec(source_id, asset="BTC-USD", period=None):
    for item in expected_object_registry():
        if item["source_id"] != source_id or item["asset"] != asset:
            continue
        if period is None or item["period"] == period:
            return item
    raise AssertionError("Synthetic source object not found.")


def _funding_payload(spec, *, interval="8", rate="0.00010000"):
    timestamp = int(pd.Timestamp(spec["period"], tz="UTC").timestamp() * 1000)
    return _zip_payload(
        spec,
        _csv_bytes([FUNDING_HEADER, [str(timestamp), interval, rate]]),
    )


def _metrics_payload(spec, *, symbol=None, open_interest="10000.50"):
    symbol = spec["symbol"] if symbol is None else symbol
    timestamp = pd.Timestamp(spec["period"], tz="UTC").strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, symbol, open_interest, "1000000", "1", "1", "1", "1"]
    return _zip_payload(spec, _csv_bytes([METRICS_HEADER, row]))


def _kline_payload(spec, *, aligned=True, close="101.25", header=False):
    start = pd.Timestamp(spec["period"], tz="UTC")
    if not aligned:
        start += pd.Timedelta(hours=1)
    end = start + pd.Timedelta(hours=12) - pd.Timedelta(milliseconds=1)
    row = [
        str(int(start.timestamp() * 1000)),
        "100",
        "102",
        "99",
        close,
        "1234.5",
        str(int(end.timestamp() * 1000)),
        "123456",
        "42",
        "600",
        "60000",
        "0",
    ]
    if header == "documented":
        rows = [KLINE_DOCUMENTED_HEADER, row]
    else:
        rows = [KLINE_HEADER, row] if header else [row]
    return _zip_payload(spec, _csv_bytes(rows))


def _payload_for_spec(spec):
    if spec["source_id"] == "FUNDING_RATE":
        return _funding_payload(spec)
    if spec["source_id"] == "OPEN_INTEREST_METRICS":
        return _metrics_payload(spec)
    close = "101.25" if spec["source_id"] == "MARK_PRICE_12H" else "100.00"
    return _kline_payload(spec, close=close)


def test_declaration_freezes_exact_registry_and_keeps_run_inert():
    declaration = dataset_lock_declaration()

    assert declaration["dataset_id"] == DATASET_ID
    assert declaration["parent_commit"] == "af0af86"
    assert declaration["common_start_utc"] == COMMON_START_UTC
    assert declaration["common_end_exclusive_utc"] == COMMON_END_EXCLUSIVE_UTC
    assert declaration["expected_object_count"] == 2808
    assert declaration["expected_object_counts_by_source"] == {
        "FUNDING_RATE": 84,
        "OPEN_INTEREST_METRICS": 2556,
        "MARK_PRICE_12H": 84,
        "INDEX_PRICE_12H": 84,
    }
    assert declaration["authorization_phrase_active"] is False
    assert declaration["source_objects_downloaded"] is False
    assert declaration["market_values_opened"] is False
    assert declaration["model_training_executed"] is False


def test_registry_is_deterministic_complete_and_development_only():
    registry = expected_object_registry()

    assert len(registry) == len({item["key"] for item in registry}) == 2808
    assert list(dict.fromkeys(item["source_id"] for item in registry)) == list(SOURCE_SPECS)
    assert set(item["asset"] for item in registry) == set(ASSET_SYMBOLS)
    assert registry[0]["period"] == "2021-12"
    assert registry[-1]["period"] == "2024-03"
    assert all(item["key"].startswith("data/futures/um/") for item in registry)
    assert not any("2024-04" in item["period"] for item in registry)


def test_official_checksum_parser_binds_hash_and_basename():
    digest = "a" * 64
    assert parse_official_checksum(f"{digest}  file.zip\n".encode(), "file.zip") == digest
    assert parse_official_checksum(f"{digest} *file.zip".encode(), "file.zip") == digest

    with pytest.raises(ValueError, match="filename"):
        parse_official_checksum(f"{digest}  other.zip\n".encode(), "file.zip")
    with pytest.raises(ValueError, match="format"):
        parse_official_checksum(b"not a checksum", "file.zip")


def test_funding_archive_validates_exact_schema_and_normalizes_decimal_text():
    spec = _spec("FUNDING_RATE")
    payload, checksum = _funding_payload(spec, rate="0.00010000")

    result = validate_source_archive(spec, payload, checksum)

    assert result["row_count"] == 1
    assert result["zip_sha256"] == hashlib.sha256(payload).hexdigest()
    assert b"source_timestamp,funding_rate\n" in result["normalized_bytes"]
    assert b",0.00010000\n" in result["normalized_bytes"]


def test_open_interest_archive_requires_exact_symbol_and_positive_value():
    spec = _spec("OPEN_INTEREST_METRICS", period="2021-12-01")
    payload, checksum = _metrics_payload(spec)
    result = validate_source_archive(spec, payload, checksum)
    assert result["row_count"] == 1
    assert b",10000.50\n" in result["normalized_bytes"]

    payload, checksum = _metrics_payload(spec, symbol="ETHUSDT")
    with pytest.raises(ValueError, match="symbol"):
        validate_source_archive(spec, payload, checksum)
    payload, checksum = _metrics_payload(spec, open_interest="0")
    with pytest.raises(ValueError, match="positive"):
        validate_source_archive(spec, payload, checksum)


@pytest.mark.parametrize("header", [False, True, "documented"])
def test_kline_archive_accepts_headerless_or_exact_header_and_requires_grid(header):
    spec = _spec("MARK_PRICE_12H")
    payload, checksum = _kline_payload(spec, header=header)
    result = validate_source_archive(spec, payload, checksum)
    assert result["row_count"] == 1
    assert b"open_timestamp,close_timestamp,close\n" in result["normalized_bytes"]

    payload, checksum = _kline_payload(spec, aligned=False)
    with pytest.raises(ValueError, match="12h grid"):
        validate_source_archive(spec, payload, checksum)


def test_validation_rejects_checksum_mismatch_extra_member_and_path_traversal():
    spec = _spec("FUNDING_RATE")
    payload, checksum = _funding_payload(spec)
    with pytest.raises(ValueError, match="official checksum"):
        validate_source_archive(spec, payload + b"tamper", checksum)

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(spec["filename"][:-4] + ".csv", b"one")
        archive.writestr("extra.csv", b"two")
    payload = output.getvalue()
    checksum = f"{hashlib.sha256(payload).hexdigest()}  {spec['filename']}\n".encode()
    with pytest.raises(ValueError, match="exactly one"):
        validate_source_archive(spec, payload, checksum)

    member = "../" + spec["filename"][:-4] + ".csv"
    payload, checksum = _zip_payload(spec, b"unsafe", member_name=member)
    with pytest.raises(ValueError, match="unsafe"):
        validate_source_archive(spec, payload, checksum)


def test_schema_period_duplicates_and_funding_age_fail_closed():
    funding = _spec("FUNDING_RATE")
    payload, checksum = _funding_payload(funding, interval="24")
    with pytest.raises(ValueError, match="12-hour"):
        validate_source_archive(funding, payload, checksum)

    metrics = _spec("OPEN_INTEREST_METRICS", period="2021-12-01")
    timestamp = "2021-12-01 00:00:00"
    row = [timestamp, metrics["symbol"], "100", "1000", "1", "1", "1", "1"]
    payload, checksum = _zip_payload(metrics, _csv_bytes([METRICS_HEADER, row, row]))
    with pytest.raises(ValueError, match="strictly increasing and unique"):
        validate_source_archive(metrics, payload, checksum)

    foreign = row.copy()
    foreign[0] = "2021-12-02 00:00:00"
    payload, checksum = _zip_payload(metrics, _csv_bytes([METRICS_HEADER, foreign]))
    with pytest.raises(ValueError, match="archive period"):
        validate_source_archive(metrics, payload, checksum)


def test_locker_is_one_shot_atomic_and_reader_reconstructs_exact_parent_frames(
    tmp_path, monkeypatch
):
    tiny_registry = []
    for source_id in SOURCE_SPECS:
        for asset in ASSET_SYMBOLS:
            period = "2021-12-01" if source_id == "OPEN_INTEREST_METRICS" else "2021-12"
            tiny_registry.append(_spec(source_id, asset, period))
    monkeypatch.setattr(dataset, "expected_object_registry", lambda: tiny_registry)

    payloads = {}
    for spec in tiny_registry:
        payload, checksum = _payload_for_spec(spec)
        payloads[spec["url"]] = payload
        payloads[spec["checksum_url"]] = checksum
    calls = []

    def fetch(url):
        calls.append(url)
        return payloads[url]

    final = tmp_path / "context_lock"
    with pytest.raises(PermissionError):
        DerivativesContextDatasetLocker(fetch).run(final, "wrong")
    summary = DerivativesContextDatasetLocker(fetch).run(final, AUTHORIZATION_PHRASE)

    assert summary["object_count"] == 12
    assert summary["normalized_file_count"] == 12
    assert summary["model_training_executed"] is False
    assert len(calls) == 24
    assert final.is_dir()
    assert not (tmp_path / ".context_lock.staging").exists()

    sources, manifest, digest = read_locked_derivatives_context_dataset(
        final, expected_manifest_sha256=summary["manifest_sha256"]
    )
    assert digest == summary["manifest_sha256"]
    assert manifest["dataset_id"] == DATASET_ID
    assert set(sources) == set(ASSET_SYMBOLS)
    for asset in ASSET_SYMBOLS:
        assert list(sources[asset]) == ["funding", "open_interest", "mark_index_12h"]
        assert sources[asset]["funding"].columns.tolist() == ["funding_rate"]
        assert sources[asset]["open_interest"].columns.tolist() == ["open_interest"]
        assert sources[asset]["mark_index_12h"].columns.tolist() == [
            "mark_close",
            "index_close",
        ]
    with pytest.raises(FileExistsError):
        DerivativesContextDatasetLocker(fetch).run(final, AUTHORIZATION_PHRASE)


def test_reader_rejects_manifest_identity_or_normalized_tamper(tmp_path, monkeypatch):
    tiny_registry = []
    for source_id in SOURCE_SPECS:
        for asset in ASSET_SYMBOLS:
            period = "2021-12-01" if source_id == "OPEN_INTEREST_METRICS" else "2021-12"
            tiny_registry.append(_spec(source_id, asset, period))
    monkeypatch.setattr(dataset, "expected_object_registry", lambda: tiny_registry)
    payloads = {}
    for spec in tiny_registry:
        payload, checksum = _payload_for_spec(spec)
        payloads[spec["url"]] = payload
        payloads[spec["checksum_url"]] = checksum
    final = tmp_path / "lock"
    summary = DerivativesContextDatasetLocker(payloads.__getitem__).run(
        final, AUTHORIZATION_PHRASE
    )

    with pytest.raises(RuntimeError, match="manifest identity"):
        read_locked_derivatives_context_dataset(final, expected_manifest_sha256="0" * 64)
    target = next((final / "normalized").rglob("FUNDING_RATE.csv"))
    target.write_bytes(target.read_bytes() + b"tamper")
    with pytest.raises(RuntimeError, match="byte-count mismatch|hash mismatch"):
        read_locked_derivatives_context_dataset(
            final, expected_manifest_sha256=summary["manifest_sha256"], verify_raw=False
        )


def test_failed_acquisition_preserves_staging_and_never_creates_final(
    tmp_path, monkeypatch
):
    spec = _spec("FUNDING_RATE")
    monkeypatch.setattr(dataset, "expected_object_registry", lambda: [spec])

    def fail(_url):
        raise OSError("transport stopped")

    final = tmp_path / "failed"
    with pytest.raises(OSError, match="transport stopped"):
        DerivativesContextDatasetLocker(fail).run(final, AUTHORIZATION_PHRASE)
    assert not final.exists()
    assert (tmp_path / ".failed.staging").is_dir()


def test_protocol_freezes_no_fallback_no_fill_and_no_learning():
    protocol = (
        Path(__file__).resolve().parents[1]
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    assert "exactly one safe CSV member" in protocol
    assert "No REST fallback" in protocol
    assert "No duplicate, ordering inversion" in protocol
    assert "does not execute acquisition" in protocol
    assert "Calibration, Evaluation" in protocol
