import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from daily_crypto_replay_protocol import (
    BTC_ETH_1D_MANIFEST_SHA256,
    DAILY_CRYPTO_ASSET_ORDER,
    DAILY_CRYPTO_REPLAY_PROTOCOL_ID,
    MANDATE_NORMALIZED_SHA256,
    DailyCryptoReplayProtocol,
    load_btc_eth_daily_manifest,
    load_selective_swing_mandate,
    main,
    normalized_text_sha256,
    protocol_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
MANDATE = ROOT / "SELECTIVE_SWING_TRADING_RESEARCH_MANDATE_V1.md"
MANIFEST = ROOT / "data/research/timeframe_sensitivity_v1/1d/manifest.json"


def test_protocol_declaration_is_exact_safe_and_provider_neutral_for_xrp():
    declaration = protocol_declaration()

    assert declaration["schema_version"] == 1
    assert declaration["protocol_id"] == DAILY_CRYPTO_REPLAY_PROTOCOL_ID
    assert declaration["assets"] == list(DAILY_CRYPTO_ASSET_ORDER)
    assert declaration["timeframe"] == "1d"
    assert declaration["granularity_seconds"] == 86400
    assert declaration["decision_context_bars"] == 30
    assert declaration["cash_is_default"] is True
    assert declaration["btc_eth_recorded_manifest_sha256"] == (
        BTC_ETH_1D_MANIFEST_SHA256
    )
    assert declaration["xrp_provider_status"] == "PROVIDER_AUDIT_REQUIRED"
    assert declaration["xrp_provider"] is None
    assert declaration["data_acquisition_executed"] is False
    assert declaration["real_chart_replay_executed"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["cloud_execution_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_data_contract_prohibits_synthetic_fill_and_cross_provider_raw_volume():
    contract = protocol_declaration()["data_contract"]

    assert contract["candle_fill_policy"] == "NO_SYNTHETIC_CANDLE_FILL"
    assert contract["missing_interval_policy"] == "EXPLICIT_UNAVAILABLE_INTERVALS"
    assert contract["volume_semantics"] == "PROVIDER_VENUE_NATIVE_BASE_VOLUME"
    assert contract["cross_provider_raw_volume_comparison"] == "PROHIBITED"
    assert contract["relative_volume_normalization"] == "PER_ASSET_CAUSAL_TRAILING"
    assert contract["availability_segments"] == "REPLAY_SEPARATELY"


def test_mandate_hash_is_line_ending_stable(tmp_path):
    original = MANDATE.read_text(encoding="utf-8")
    crlf = tmp_path / "mandate.md"
    crlf.write_bytes(original.replace("\n", "\r\n").encode("utf-8"))

    assert normalized_text_sha256(MANDATE) == MANDATE_NORMALIZED_SHA256
    assert normalized_text_sha256(crlf) == MANDATE_NORMALIZED_SHA256
    text, digest = load_selective_swing_mandate(crlf)
    assert "Crypto Capitulation-Volume Reversal v1" in text
    assert digest == MANDATE_NORMALIZED_SHA256


def test_tampered_or_wrong_mandate_is_rejected(tmp_path):
    changed = tmp_path / "mandate.md"
    changed.write_text(MANDATE.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="mandate SHA256"):
        load_selective_swing_mandate(changed)


def copy_manifest_bundle(tmp_path, mutator=None):
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if mutator:
        mutator(payload)
    manifest = tmp_path / "manifest.json"
    raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    manifest.with_name("manifest.sha256").write_text(
        f"{digest}  manifest.json\n", encoding="ascii", newline="\n"
    )
    return manifest


def test_recorded_btc_eth_manifest_is_exact_and_verified():
    payload, digest = load_btc_eth_daily_manifest(MANIFEST)

    assert digest == BTC_ETH_1D_MANIFEST_SHA256
    assert payload["contract"]["products"] == ["BTC-USD", "ETH-USD"]
    assert payload["contract"]["timeframe"] == "1d"
    assert payload["contract"]["granularity_seconds"] == 86400
    assert payload["assets"]["BTC-USD"]["rows"] == 2769
    assert payload["assets"]["ETH-USD"]["rows"] == 2769


@pytest.mark.parametrize(
    "mutator, error",
    [
        (lambda payload: payload["contract"].update(timeframe="6h"), "contract"),
        (lambda payload: payload["contract"].update(granularity_seconds=21600), "contract"),
        (lambda payload: payload["contract"].update(products=["BTC-USD"]), "contract"),
        (lambda payload: payload["assets"].pop("ETH-USD"), "assets"),
        (lambda payload: payload["source"].update(provider="unknown"), "source"),
    ],
)
def test_manifest_contract_drift_is_rejected_after_valid_resigning(
    tmp_path, mutator, error
):
    manifest = copy_manifest_bundle(tmp_path, mutator)

    with pytest.raises(RuntimeError, match=error):
        load_btc_eth_daily_manifest(
            manifest,
            expected_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        )


def test_manifest_sidecar_mismatch_is_rejected(tmp_path):
    manifest = copy_manifest_bundle(tmp_path)
    manifest.with_name("manifest.sha256").write_text(
        f"{'0' * 64}  manifest.json\n", encoding="ascii"
    )

    with pytest.raises(RuntimeError, match="sidecar"):
        load_btc_eth_daily_manifest(
            manifest,
            expected_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        )


def test_protocol_review_binds_existing_assets_but_blocks_real_replay_for_xrp():
    review = DailyCryptoReplayProtocol().review(MANDATE, MANIFEST)

    assert review["status"] == (
        "DAILY_CRYPTO_REPLAY_PROTOCOL_REVIEWED_PROVIDER_AUDIT_REQUIRED"
    )
    assert review["mandate_sha256_match"] is True
    assert review["btc_eth_manifest_sha256_match"] is True
    assert review["replay_component_reviewed"] is True
    assert review["xrp_provider_audit_completed"] is False
    assert review["all_asset_data_locked"] is False
    assert review["real_replay_authorized"] is False
    assert review["prerequisites_satisfied"] is False
    assert review["performance_evaluation_executed"] is False
    assert review["candidate_v2_authorized"] is False
    assert review["bounded_forward_paper_authorized"] is False
    assert review["cloud_execution_authorized"] is False
    assert review["live_execution_authorized"] is False


def test_cli_emits_declaration_without_running_replay(capsys):
    exit_code = main(
        ["--mandate", str(MANDATE), "--btc-eth-manifest", str(MANIFEST)]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"].endswith("PROVIDER_AUDIT_REQUIRED")
    assert payload["real_replay_authorized"] is False
    assert payload["performance_evaluation_executed"] is False
