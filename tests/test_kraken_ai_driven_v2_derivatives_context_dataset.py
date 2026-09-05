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
    ATTEMPT_3_RESUME_OBJECT_COUNT,
    AUTHORIZATION_PHRASE,
    COMMON_END_EXCLUSIVE_UTC,
    COMMON_START_UTC,
    DATASET_ID,
    DerivativesContextDatasetLocker,
    FUNDING_HEADER,
    KLINE_HEADER,
    KLINE_DOCUMENTED_HEADER,
    MAXIMUM_TRANSPORT_ATTEMPTS,
    METRICS_HEADER,
    OPEN_INTEREST_ZERO_SENTINEL_LITERAL,
    OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMPS,
    OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256,
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


def _metrics_payload(
    spec,
    *,
    symbol=None,
    open_interest="10000.50",
    open_interest_value="1000000",
    timestamp=None,
):
    symbol = spec["symbol"] if symbol is None else symbol
    timestamp = (
        pd.Timestamp(spec["period"], tz="UTC").strftime("%Y-%m-%d %H:%M:%S")
        if timestamp is None
        else timestamp
    )
    row = [
        timestamp,
        symbol,
        open_interest,
        open_interest_value,
        "1",
        "1",
        "1",
        "1",
    ]
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


def _prior_staging(tmp_path, attempt):
    prior = tmp_path / f".context_lock_attempt_{attempt}.staging"
    prior.mkdir()
    (prior / "preserved.bin").write_bytes(f"attempt-{attempt}-preserved".encode())
    return prior


def _attempt_3_resume_staging(tmp_path, monkeypatch, registry, payloads, count):
    prior = tmp_path / ".context_lock_attempt_3.staging"
    for spec in registry[:count]:
        raw = prior / dataset._safe_raw_relative(spec)
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(payloads[spec["url"]])
        Path(str(raw) + ".CHECKSUM").write_bytes(payloads[spec["checksum_url"]])
    inventory = dataset._directory_inventory(prior)
    monkeypatch.setattr(dataset, "ATTEMPT_3_RESUME_OBJECT_COUNT", count)
    monkeypatch.setattr(dataset, "ATTEMPT_3_STAGING_FILE_COUNT", inventory["file_count"])
    monkeypatch.setattr(dataset, "ATTEMPT_3_STAGING_TOTAL_BYTES", inventory["total_bytes"])
    monkeypatch.setattr(
        dataset,
        "ATTEMPT_3_STAGING_INVENTORY_SHA256",
        inventory["inventory_sha256"],
    )
    return prior, inventory


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
    assert declaration["recovery_parent_commit"] == "25d55b6"
    assert declaration["attempt_1_authorization_consumed"] is True
    assert declaration["attempt_1_final_dataset_exists"] is False
    assert declaration["attempt_1_staging_required"] is True
    assert declaration["attempt_2_authorization_consumed"] is True
    assert declaration["attempt_2_final_dataset_exists"] is False
    assert declaration["attempt_2_staging_required"] is True
    assert declaration["attempt_3_authorization_consumed"] is True
    assert declaration["attempt_3_final_dataset_exists"] is False
    assert declaration["attempt_3_staging_required"] is True
    assert declaration["verified_resume_object_count"] == ATTEMPT_3_RESUME_OBJECT_COUNT
    assert declaration["public_download_object_count"] == 2113
    assert declaration["maximum_transport_attempts_per_fetch"] == 12
    assert declaration["recovery_attempt"] == 4
    assert declaration["attempt_4_authorization_consumed"] is True
    assert declaration["attempt_4_final_dataset_recorded"] is True
    assert declaration["attempt_4_execution_commit"].startswith("40b5943")
    assert declaration["attempt_4_manifest_sha256"] == (
        "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
    )
    assert declaration["read_only_iso8601_timestamp_recovery_implemented"] is True
    assert declaration["open_interest_zero_sentinel_count"] == 399
    assert declaration["open_interest_zero_sentinel_count_per_asset"] == 133
    assert len(OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMPS) == 133
    assert (
        declaration["open_interest_zero_sentinel_timestamp_sha256"]
        == OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256
    )
    assert declaration["authorization_phrase_active"] is False
    assert declaration["source_objects_downloaded"] is False
    assert declaration["market_values_opened"] is False
    assert declaration["model_training_executed"] is False


def test_normalized_timestamp_parser_accepts_mixed_iso8601_precision():
    values = pd.Series(
        [
            "2021-12-01T00:00:00Z",
            "2021-12-01T16:00:00.001000Z",
            "2021-12-02T00:00:00.123456Z",
        ]
    )

    parsed = dataset._parse_normalized_utc(values, "funding")

    assert str(parsed.dt.tz) == "UTC"
    assert parsed.iloc[1] == pd.Timestamp("2021-12-01T16:00:00.001000Z")
    assert parsed.iloc[2] == pd.Timestamp("2021-12-02T00:00:00.123456Z")


def test_normalized_timestamp_parser_rejects_malformed_text():
    with pytest.raises(RuntimeError, match="timestamp format mismatch"):
        dataset._parse_normalized_utc(pd.Series(["not-a-timestamp"]), "funding")


def test_frozen_zero_sentinel_list_matches_its_canonical_hash():
    payload = dataset.canonical_json_bytes(
        list(OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMPS)
    )

    assert hashlib.sha256(payload).hexdigest() == (
        OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMP_SHA256
    )
    assert len(set(OPEN_INTEREST_ZERO_SENTINEL_TIMESTAMPS)) == 133


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


def test_open_interest_archive_requires_exact_symbol_and_usable_positive_value():
    spec = _spec("OPEN_INTEREST_METRICS", period="2021-12-01")
    payload, checksum = _metrics_payload(spec)
    result = validate_source_archive(spec, payload, checksum)
    assert result["row_count"] == 1
    assert b",10000.50\n" in result["normalized_bytes"]

    payload, checksum = _metrics_payload(spec, symbol="ETHUSDT")
    with pytest.raises(ValueError, match="symbol"):
        validate_source_archive(spec, payload, checksum)
    payload, checksum = _metrics_payload(spec, open_interest="0")
    with pytest.raises(ValueError, match="zero sentinel"):
        validate_source_archive(spec, payload, checksum)


def test_exact_frozen_paired_zero_sentinel_is_recorded_and_not_normalized():
    spec = _spec("OPEN_INTEREST_METRICS", period="2022-03-07")
    timestamp = "2022-03-07 15:30:00"
    payload, checksum = _metrics_payload(
        spec,
        open_interest=OPEN_INTEREST_ZERO_SENTINEL_LITERAL,
        open_interest_value=OPEN_INTEREST_ZERO_SENTINEL_LITERAL,
        timestamp=timestamp,
    )

    result = validate_source_archive(spec, payload, checksum)

    assert result["row_count"] == 1
    assert result["normalized_row_count"] == 0
    assert result["open_interest_zero_sentinel_timestamps"] == [
        "2022-03-07T15:30:00Z"
    ]
    assert result["normalized_bytes"] == b"source_timestamp,open_interest\n"


@pytest.mark.parametrize(
    ("open_interest", "open_interest_value", "timestamp"),
    [
        ("0", "0E-8", "2022-03-07 15:30:00"),
        ("0E-8", "1", "2022-03-07 15:30:00"),
        ("0E-8", "0E-8", "2022-03-07 15:25:00"),
    ],
)
def test_unfrozen_unpaired_or_alternative_zero_sentinel_fails_closed(
    open_interest, open_interest_value, timestamp
):
    spec = _spec("OPEN_INTEREST_METRICS", period="2022-03-07")
    payload, checksum = _metrics_payload(
        spec,
        open_interest=open_interest,
        open_interest_value=open_interest_value,
        timestamp=timestamp,
    )

    with pytest.raises(ValueError, match="zero sentinel"):
        validate_source_archive(spec, payload, checksum)


def test_open_interest_archive_records_exact_optional_blanks_without_fill():
    spec = _spec("OPEN_INTEREST_METRICS", period="2021-12-30")
    timestamp = "2021-12-30 14:35:00"
    row = [timestamp, spec["symbol"], "72516.05400000", "3437120278.45524000"]
    row.extend(["", "", "", ""])
    payload, checksum = _zip_payload(spec, _csv_bytes([METRICS_HEADER, row]))

    result = validate_source_archive(spec, payload, checksum)

    assert result["optional_blank_counts"] == {
        "count_toptrader_long_short_ratio": 1,
        "sum_toptrader_long_short_ratio": 1,
        "count_long_short_ratio": 1,
        "sum_taker_long_short_vol_ratio": 1,
    }
    assert b",72516.05400000\n" in result["normalized_bytes"]
    assert b"3437120278.45524000" not in result["normalized_bytes"]


def test_open_interest_archive_rejects_nonblank_optional_sentinel_and_required_blank():
    spec = _spec("OPEN_INTEREST_METRICS", period="2021-12-30")
    timestamp = "2021-12-30 14:35:00"
    row = [timestamp, spec["symbol"], "72516", "3437120278", "null", "", "", ""]
    payload, checksum = _zip_payload(spec, _csv_bytes([METRICS_HEADER, row]))
    with pytest.raises(ValueError, match="count_toptrader_long_short_ratio"):
        validate_source_archive(spec, payload, checksum)

    row[3] = ""
    row[4] = ""
    payload, checksum = _zip_payload(spec, _csv_bytes([METRICS_HEADER, row]))
    with pytest.raises(ValueError, match="sum_open_interest_value"):
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
    prior_1 = _prior_staging(tmp_path, 1)
    prior_2 = _prior_staging(tmp_path, 2)
    prior_3, prior_3_inventory = _attempt_3_resume_staging(
        tmp_path, monkeypatch, tiny_registry, payloads, 4
    )
    prior_1_payload = (prior_1 / "preserved.bin").read_bytes()
    prior_2_payload = (prior_2 / "preserved.bin").read_bytes()
    with pytest.raises(PermissionError):
        DerivativesContextDatasetLocker(fetch).run(final, "wrong")
    summary = DerivativesContextDatasetLocker(fetch).run(
        final, AUTHORIZATION_PHRASE, prior_1, prior_2, prior_3
    )

    assert summary["object_count"] == 12
    assert summary["normalized_file_count"] == 12
    assert summary["model_training_executed"] is False
    assert summary["recovery_attempt"] == 4
    assert summary["verified_resume_object_count"] == 4
    assert summary["public_download_object_count"] == 8
    assert summary["attempt_3_staging_inventory_sha256"] == (
        prior_3_inventory["inventory_sha256"]
    )
    assert summary["open_interest_zero_sentinel_count"] == 0
    assert len(calls) == 16
    assert final.is_dir()
    assert not (tmp_path / ".context_lock.staging").exists()
    assert (prior_1 / "preserved.bin").read_bytes() == prior_1_payload
    assert (prior_2 / "preserved.bin").read_bytes() == prior_2_payload
    assert dataset._directory_inventory(prior_3) == prior_3_inventory

    sources, manifest, digest = read_locked_derivatives_context_dataset(
        final, expected_manifest_sha256=summary["manifest_sha256"]
    )
    assert digest == summary["manifest_sha256"]
    assert manifest["dataset_id"] == DATASET_ID
    assert [record["acquisition_origin"] for record in manifest["objects"][:4]] == [
        "VERIFIED_ATTEMPT_3_STAGING"
    ] * 4
    assert [record["acquisition_origin"] for record in manifest["objects"][4:]] == [
        "PUBLIC_SOURCE_ATTEMPT_4"
    ] * 8
    assert manifest["optional_metrics_blank_counts"] == {
        "count_toptrader_long_short_ratio": 0,
        "sum_toptrader_long_short_ratio": 0,
        "count_long_short_ratio": 0,
        "sum_taker_long_short_vol_ratio": 0,
    }
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
        DerivativesContextDatasetLocker(fetch).run(
            final, AUTHORIZATION_PHRASE, prior_1, prior_2, prior_3
        )


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
    prior_1 = _prior_staging(tmp_path, 1)
    prior_2 = _prior_staging(tmp_path, 2)
    prior_3, _ = _attempt_3_resume_staging(
        tmp_path, monkeypatch, tiny_registry, payloads, 4
    )
    summary = DerivativesContextDatasetLocker(payloads.__getitem__).run(
        final, AUTHORIZATION_PHRASE, prior_1, prior_2, prior_3
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
    first = _spec("FUNDING_RATE")
    second = _spec("FUNDING_RATE", asset="ETH-USD")
    registry = [first, second]
    monkeypatch.setattr(dataset, "expected_object_registry", lambda: registry)
    payload, checksum = _payload_for_spec(first)
    payloads = {first["url"]: payload, first["checksum_url"]: checksum}

    def fail(_url):
        raise OSError("transport stopped")

    final = tmp_path / "failed"
    prior_1 = _prior_staging(tmp_path, 1)
    prior_2 = _prior_staging(tmp_path, 2)
    prior_3, _ = _attempt_3_resume_staging(
        tmp_path, monkeypatch, registry, payloads, 1
    )
    with pytest.raises(OSError, match="transport stopped"):
        DerivativesContextDatasetLocker(fail).run(
            final, AUTHORIZATION_PHRASE, prior_1, prior_2, prior_3
        )
    assert not final.exists()
    assert (tmp_path / ".failed.staging").is_dir()


def test_transport_retries_use_frozen_bounded_exponential_backoff(monkeypatch):
    attempts = []
    sleeps = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"verified"

    def open_after_three_failures(_request, timeout):
        assert timeout == 120
        attempts.append(1)
        if len(attempts) <= 3:
            raise OSError("temporary DNS failure")
        return Response()

    monkeypatch.setattr(dataset, "urlopen", open_after_three_failures)
    monkeypatch.setattr(dataset.time, "sleep", sleeps.append)

    assert dataset._default_fetch_bytes("https://example.test/object") == b"verified"
    assert len(attempts) == 4
    assert sleeps == [1, 2, 4]
    assert MAXIMUM_TRANSPORT_ATTEMPTS == 12


def test_attempt_3_resume_requires_exact_inventory_and_contiguous_file_set(
    tmp_path, monkeypatch
):
    registry = [_spec("FUNDING_RATE"), _spec("FUNDING_RATE", asset="ETH-USD")]
    monkeypatch.setattr(dataset, "expected_object_registry", lambda: registry)
    payloads = {}
    for spec in registry:
        payload, checksum = _payload_for_spec(spec)
        payloads[spec["url"]] = payload
        payloads[spec["checksum_url"]] = checksum
    prior_3, _ = _attempt_3_resume_staging(
        tmp_path, monkeypatch, registry, payloads, 1
    )
    extra = prior_3 / "unexpected.bin"
    extra.write_bytes(b"unexpected")

    with pytest.raises(RuntimeError, match="inventory mismatch"):
        DerivativesContextDatasetLocker(payloads.__getitem__).run(
            tmp_path / "lock",
            AUTHORIZATION_PHRASE,
            _prior_staging(tmp_path, 1),
            _prior_staging(tmp_path, 2),
            prior_3,
        )


def test_locker_rejects_an_incomplete_frozen_zero_sentinel_registry(
    tmp_path, monkeypatch
):
    spec = _spec("OPEN_INTEREST_METRICS", period="2022-03-07")
    monkeypatch.setattr(dataset, "expected_object_registry", lambda: [spec])
    payload, checksum = _metrics_payload(
        spec,
        open_interest=OPEN_INTEREST_ZERO_SENTINEL_LITERAL,
        open_interest_value=OPEN_INTEREST_ZERO_SENTINEL_LITERAL,
        timestamp="2022-03-07 15:30:00",
    )
    payloads = {spec["url"]: payload, spec["checksum_url"]: checksum}
    final = tmp_path / "incomplete_sentinel_lock"
    prior_3, _ = _attempt_3_resume_staging(
        tmp_path, monkeypatch, [spec], payloads, 1
    )

    with pytest.raises(RuntimeError, match="zero-sentinel registry"):
        DerivativesContextDatasetLocker(payloads.__getitem__).run(
            final,
            AUTHORIZATION_PHRASE,
            _prior_staging(tmp_path, 1),
            _prior_staging(tmp_path, 2),
            prior_3,
        )

    assert not final.exists()
    assert (tmp_path / ".incomplete_sentinel_lock.staging").is_dir()


def test_recovery_requires_three_distinct_nonempty_prior_staging_directories(tmp_path):
    final = tmp_path / "recovery"
    with pytest.raises(PermissionError, match="Attempt 1, Attempt 2 and Attempt 3"):
        DerivativesContextDatasetLocker().run(final, AUTHORIZATION_PHRASE)

    prior_1 = _prior_staging(tmp_path, 1)
    prior_2 = _prior_staging(tmp_path, 2)
    empty_2 = tmp_path / ".attempt_2.staging"
    empty_2.mkdir()
    with pytest.raises(RuntimeError, match="non-empty"):
        DerivativesContextDatasetLocker().run(
            final, AUTHORIZATION_PHRASE, prior_1, prior_2, empty_2
        )

    with pytest.raises(ValueError, match="distinct"):
        DerivativesContextDatasetLocker().run(
            final, AUTHORIZATION_PHRASE, prior_1, prior_2, prior_2
        )


def test_protocol_freezes_no_fallback_no_fill_and_no_learning():
    protocol = (
        Path(__file__).resolve().parents[1]
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DATASET_LOCK_READER_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    assert "exactly one safe CSV member" in protocol
    assert "No REST fallback" in protocol
    assert "No duplicate, ordering inversion" in protocol
    assert "exact blank" in protocol
    assert "Attempts 1, 2 and 3 staging" in protocol
    assert "695 verified-resume" in protocol
    assert "twelve attempts" in protocol
    assert "399" in protocol
    assert "0E-8" in protocol
    assert "does not execute acquisition" in protocol
    assert "Calibration, Evaluation" in protocol
