import json
import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_development_review import (
    COMPONENT_BINDINGS,
    DEVELOPMENT_PROTOCOL_ID,
    DEVELOPMENT_PROTOCOL_NORMALIZED_SHA256,
    DEVELOPMENT_RUNNER_NORMALIZED_SHA256,
    load_development_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)
from kraken_ai_driven_v2_development_runner import (
    AUTHORIZATION_PHRASE,
    DEVELOPMENT_RUN_ID,
    INITIAL_CAPITAL,
)
from kraken_ai_driven_v2_partition import (
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    PARTITION_PROTOCOL_ID,
    REFERENCE_PARTITION_CONTRACT,
)


ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_PROTOCOL = (
    ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DEVELOPMENT_RUNNER_PROTOCOL_V1.md"
)
DEVELOPMENT_RUNNER = ROOT / "src" / "kraken_ai_driven_v2_development_runner.py"
ATTEMPT_1_INCIDENT = (
    ROOT / "KRAKEN_AI_DRIVEN_V2_DEVELOPMENT_ATTEMPT_1_INCIDENT.md"
)


def test_development_review_exactly_hash_binds_the_complete_v2_chain():
    _, protocol_digest = load_development_protocol(DEVELOPMENT_PROTOCOL)

    assert protocol_digest == DEVELOPMENT_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(DEVELOPMENT_RUNNER) == (
        DEVELOPMENT_RUNNER_NORMALIZED_SHA256
    )
    assert len(COMPONENT_BINDINGS) == 8
    for binding in COMPONENT_BINDINGS:
        assert normalized_text_sha256(ROOT / binding["path"]) == binding["sha256"]


@pytest.mark.parametrize("binding_index", range(8))
def test_changed_upstream_component_is_rejected(tmp_path, binding_index):
    changed_paths = [ROOT / item["path"] for item in COMPONENT_BINDINGS]
    source = changed_paths[binding_index]
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    changed_paths[binding_index] = changed

    with pytest.raises(RuntimeError, match="SHA256 mismatch"):
        review_declaration(
            *changed_paths,
            development_protocol_path=DEVELOPMENT_PROTOCOL,
            development_runner_path=DEVELOPMENT_RUNNER,
        )


@pytest.mark.parametrize(
    "source,keyword",
    [
        (DEVELOPMENT_PROTOCOL, "development protocol SHA256"),
        (DEVELOPMENT_RUNNER, "development runner SHA256"),
    ],
)
def test_changed_development_artifact_is_rejected(tmp_path, source, keyword):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    kwargs = {
        "development_protocol_path": DEVELOPMENT_PROTOCOL,
        "development_runner_path": DEVELOPMENT_RUNNER,
    }
    if source == DEVELOPMENT_PROTOCOL:
        kwargs["development_protocol_path"] = changed
    else:
        kwargs["development_runner_path"] = changed

    with pytest.raises(RuntimeError, match=keyword):
        review_declaration(**kwargs)


def test_development_review_is_nonexecuting_and_authorization_blocked():
    declaration = review_declaration()

    assert declaration["status"] == (
        "KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_"
        "CLOSED_NO_FURTHER_EXECUTION_AUTHORIZATION"
    )
    assert declaration["recorded_development_report_sha256"] == (
        "f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594"
    )
    assert declaration["reference_a_closed"] is True
    assert declaration["reference_a_rerun_authorized"] is False
    assert declaration["recorded_development_run_executed"] is True
    assert declaration["development_protocol_id"] == DEVELOPMENT_PROTOCOL_ID
    assert declaration["development_run_id"] == DEVELOPMENT_RUN_ID
    assert declaration["partition_protocol_id"] == PARTITION_PROTOCOL_ID
    assert declaration["partition_plan_sha256"] == (
        REFERENCE_PARTITION_CONTRACT.plan_sha256()
    )
    assert declaration["dataset_id"] == DATASET_ID
    assert declaration["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert declaration["initial_capital"] == INITIAL_CAPITAL
    assert declaration["authorization_phrase"] == AUTHORIZATION_PHRASE
    assert declaration["development_only_reader_implemented"] is True
    assert declaration["full_asset_files_hashed_as_opaque_bytes"] is True
    assert declaration["nondevelopment_ohlcv_parsing_permitted"] is False
    assert declaration["independent_evidence_lock_implemented"] is True
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["development_run_authorized"] is False
    assert declaration["development_run_executed"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["parameter_sweep_executed"] is False
    assert declaration["optimization_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["cloud_execution_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_development_review_cli_prints_only_declaration(capsys):
    result = main([])
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["reference_a_closed"] is True
    assert payload["reference_a_rerun_authorized"] is False
    assert payload["development_data_opened"] is False
    assert payload["calibration_data_opened"] is False
    assert payload["evaluation_data_opened"] is False


def test_project_documents_name_development_runner_and_authorization_boundary():
    texts = {
        name: (ROOT / name).read_text(encoding="utf-8")
        for name in (
            "VISION.md",
            "ARCHITECTURE.md",
            "ROADMAP.md",
            "CURRENT_MISSION.md",
            "LOG.md",
        )
    }

    assert "Development-Only Evidence Runner" in texts["ARCHITECTURE.md"]
    assert "DEVELOPMENT RUNNER IMPLEMENTED" in texts["CURRENT_MISSION.md"]
    assert "AI-Driven v2 Development Runner" in texts["ROADMAP.md"]
    assert "opaque byte hashing" in texts["VISION.md"]
    assert "AI-Driven v2 Development Runner" in texts["LOG.md"]
    for text in texts.values():
        assert DEVELOPMENT_PROTOCOL_ID in text
        assert "2024-04-01T00:00:00Z" in text
        assert "Candidate v2" in text
        assert "live" in text.lower()


def test_attempt_1_incident_is_technical_and_requires_new_authorization():
    text = ATTEMPT_1_INCIDENT.read_text(encoding="utf-8")

    assert "TECHNICAL_NUMERIC_TYPE_INTEGRATION_FAILURE" in text
    assert "Signal close must be numeric" in text
    assert "float64" in text
    assert "not a completed development" in text
    assert "authorization is consumed" in text
    assert "calibration and evaluation OHLCV values were not parsed" in text
