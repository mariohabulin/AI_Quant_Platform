import json
import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_partition import (
    DATASET_ID,
    DATASET_MANIFEST_SHA256,
    PARTITION_PROTOCOL_ID,
    REFERENCE_PARTITION_CONTRACT,
)
from kraken_ai_driven_v2_partition_review import (
    PARTITION_COMPONENT_NORMALIZED_SHA256,
    PARTITION_PROTOCOL_NORMALIZED_SHA256,
    RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256,
    RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256,
    V1_BTC_EPISODE_EVIDENCE_SHA256,
    load_partition_protocol,
    load_risk_execution_protocol,
    main,
    normalized_text_sha256,
    review_declaration,
)


ROOT = Path(__file__).resolve().parents[1]
RISK_PROTOCOL = (
    ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_RISK_EXECUTION_PROTOCOL_V1.md"
)
RISK_COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_risk_execution.py"
PARTITION_PROTOCOL = (
    ROOT / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_PARTITION_PROTOCOL_V1.md"
)
PARTITION_COMPONENT = ROOT / "src" / "kraken_ai_driven_v2_partition.py"


def test_partition_review_inputs_are_exact_hash_bound():
    _, risk_digest = load_risk_execution_protocol(RISK_PROTOCOL)
    _, partition_digest = load_partition_protocol(PARTITION_PROTOCOL)

    assert risk_digest == RISK_EXECUTION_PROTOCOL_NORMALIZED_SHA256
    assert partition_digest == PARTITION_PROTOCOL_NORMALIZED_SHA256
    assert normalized_text_sha256(RISK_COMPONENT) == (
        RISK_EXECUTION_COMPONENT_NORMALIZED_SHA256
    )
    assert normalized_text_sha256(PARTITION_COMPONENT) == (
        PARTITION_COMPONENT_NORMALIZED_SHA256
    )


@pytest.mark.parametrize(
    "source,position,error",
    [
        (RISK_PROTOCOL, 0, "risk/execution protocol SHA256"),
        (RISK_COMPONENT, 1, "risk/execution component SHA256"),
        (PARTITION_PROTOCOL, 2, "partition protocol SHA256"),
        (PARTITION_COMPONENT, 3, "partition component SHA256"),
    ],
)
def test_changed_partition_review_input_is_rejected(
    tmp_path, source, position, error
):
    changed = tmp_path / source.name
    changed.write_text(
        source.read_text(encoding="utf-8") + "changed\n", encoding="utf-8"
    )
    paths = [RISK_PROTOCOL, RISK_COMPONENT, PARTITION_PROTOCOL, PARTITION_COMPONENT]
    paths[position] = changed

    with pytest.raises(RuntimeError, match=error):
        review_declaration(*paths)


def test_partition_review_declaration_is_nonexecuting_and_runner_blocked():
    declaration = review_declaration(
        RISK_PROTOCOL,
        RISK_COMPONENT,
        PARTITION_PROTOCOL,
        PARTITION_COMPONENT,
    )

    assert declaration["status"].endswith("DEVELOPMENT_RUNNER_REQUIRED")
    assert declaration["partition_protocol_id"] == PARTITION_PROTOCOL_ID
    assert declaration["partition_plan_sha256"] == (
        REFERENCE_PARTITION_CONTRACT.plan_sha256()
    )
    assert declaration["dataset_id"] == DATASET_ID
    assert declaration["dataset_manifest_sha256"] == DATASET_MANIFEST_SHA256
    assert declaration["asset_order"] == ["BTC-USD", "ETH-USD", "XRP-USD"]
    assert declaration["partition_order"] == [
        "DEVELOPMENT",
        "CALIBRATION",
        "EVALUATION",
    ]
    assert declaration["development_start_utc"] == "2019-01-01T00:00:00Z"
    assert declaration["development_end_exclusive_utc"] == (
        "2024-04-01T00:00:00Z"
    )
    assert declaration["calibration_start_utc"] == "2024-04-01T00:00:00Z"
    assert declaration["calibration_end_exclusive_utc"] == (
        "2025-04-01T00:00:00Z"
    )
    assert declaration["evaluation_start_utc"] == "2025-04-01T00:00:00Z"
    assert declaration["evaluation_end_exclusive_utc"] == (
        "2026-04-01T00:00:00Z"
    )
    assert declaration["expected_calendar_buckets"] == {
        "DEVELOPMENT": 1917,
        "CALIBRATION": 365,
        "EVALUATION": 365,
    }
    assert declaration["expected_observed_rows"] == {
        "BTC-USD": {"DEVELOPMENT": 1916, "CALIBRATION": 365, "EVALUATION": 365},
        "ETH-USD": {"DEVELOPMENT": 1917, "CALIBRATION": 365, "EVALUATION": 365},
        "XRP-USD": {"DEVELOPMENT": 1915, "CALIBRATION": 365, "EVALUATION": 365},
    }
    assert declaration["v1_btc_episode_evidence_sha256"] == (
        V1_BTC_EPISODE_EVIDENCE_SHA256
    )
    assert declaration["v1_btc_episode_partition"] == "CALIBRATION"
    assert declaration["v1_btc_episode_is_unseen"] is False
    assert declaration["evaluation_is_genuinely_untouched"] is True
    assert declaration["partition_boundaries_selected_from_performance"] is False
    assert declaration["state_carry_across_partitions"] is False
    assert declaration["state_carry_across_gaps"] is False
    assert declaration["dataset_opened"] is False
    assert declaration["partitions_materialized_from_dataset"] is False
    assert declaration["development_data_opened"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["development_runner_executed"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["optimization_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["cloud_execution_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_partition_review_cli_prints_only_declaration(capsys):
    result = main(
        [
            "--risk-execution-protocol",
            str(RISK_PROTOCOL),
            "--risk-execution-component",
            str(RISK_COMPONENT),
            "--partition-protocol",
            str(PARTITION_PROTOCOL),
            "--partition-component",
            str(PARTITION_COMPONENT),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload == result
    assert payload["dataset_opened"] is False
    assert payload["evaluation_data_opened"] is False
    assert payload["performance_evaluation_executed"] is False


def test_project_documents_name_partition_boundary_and_next_runner():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    mission = (ROOT / "CURRENT_MISSION.md").read_text(encoding="utf-8")
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    vision = (ROOT / "VISION.md").read_text(encoding="utf-8")
    log = (ROOT / "LOG.md").read_text(encoding="utf-8")

    assert "AI-Driven v2 Development/Evaluation Partition" in roadmap
    assert "PARTITION PROTOCOL FROZEN" in mission
    assert "AI-Driven v2 Partition Boundary" in architecture
    assert "sealed one-time evaluation" in vision
    assert "AI-Driven v2 Partition Protocol" in log
    for text in (roadmap, mission, architecture, vision, log):
        assert PARTITION_PROTOCOL_ID in text
        assert V1_BTC_EPISODE_EVIDENCE_SHA256 in text
        assert "2025-04-01T00:00:00Z" in text
        assert "Candidate v2" in text
        assert "live" in text.lower()
