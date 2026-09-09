import json
import os
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_weekly_persistent_up_momentum_development_runner_design import (
    ADAPTER_FIELD_MAP,
    ARCHIVE_SPEC,
    ASSET_ORDER,
    CONTROL_ORDER,
    DESIGN_FALSE_FLAGS,
    DESIGN_TRUE_FLAGS,
    DEVELOPMENT_GATES,
    EVIDENCE_FILE_ORDER,
    EXPECTED_DEVELOPMENT_CALENDAR_ROWS,
    EXPECTED_DEVELOPMENT_SOURCE,
    EXPECTED_INVALID_MARKET_WEEK_STARTS,
    FUTURE_AUTHORIZATION_PHRASE,
    HYPOTHESIS_PROTOCOL_ID,
    MEMBER_BASENAME_BY_ASSET,
    PARENT_COMMIT,
    PRIMARY_RULE_ID,
    PROTOCOL_ID,
    RULE_ORDER,
    SOURCE_BINDING_SHA256,
    SYNTHETIC_PROTOCOL_ID,
    main,
    validate_weekly_development_runner_design,
    weekly_development_runner_design_declaration,
)


def test_design_identity_and_parent_are_frozen():
    result = weekly_development_runner_design_declaration()

    assert result["protocol_id"] == PROTOCOL_ID
    assert result["parent_commit"] == PARENT_COMMIT
    assert PARENT_COMMIT == "615cc8544aeeddda7163b59a343f099c96d49789"
    assert result["run_id"] == "kraken-weekly-persistent-up-momentum-development-v1"
    assert result["hypothesis_protocol_id"] == HYPOTHESIS_PROTOCOL_ID
    assert result["synthetic_protocol_id"] == SYNTHETIC_PROTOCOL_ID
    assert result["status"].endswith("DESIGN_FROZEN_NO_DATA_OR_RUN")
    assert result["next_stage"] == (
        "SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_IMPLEMENTATION_DECISION"
    )


def test_exact_archive_and_dataset_identity_are_frozen():
    result = weekly_development_runner_design_declaration()

    assert result["archive_spec"] == ARCHIVE_SPEC
    assert ARCHIVE_SPEC == {
        "filename": "Kraken_OHLCVT.zip",
        "bytes": 7_885_068_519,
        "sha256": "e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d",
    }
    assert result["dataset_manifest_sha256"] == (
        "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
    )
    assert result["configuration"]["source"]["quarterly_archive_required"] is False
    assert result["configuration"]["source"]["network_fallback_permitted"] is False


def test_daily_member_and_field_adapter_are_exact():
    configuration = weekly_development_runner_design_declaration()["configuration"]

    assert tuple(configuration["source"]["asset_order"]) == ASSET_ORDER
    assert configuration["source"]["member_basename_by_asset"] == MEMBER_BASENAME_BY_ASSET
    assert MEMBER_BASENAME_BY_ASSET == {
        "BTC-USD": "XBTUSD_1440.csv",
        "ETH-USD": "ETHUSD_1440.csv",
        "XRP-USD": "XRPUSD_1440.csv",
    }
    assert configuration["adapter"]["field_map"] == [
        list(item) for item in ADAPTER_FIELD_MAP
    ]
    assert configuration["adapter"]["numeric_transport"] == (
        "EXACT_DECIMAL_TEXT_NO_BINARY_FLOAT"
    )


def test_reader_design_keeps_nondevelopment_values_opaque():
    source = weekly_development_runner_design_declaration()["configuration"][
        "source"
    ]
    partition = weekly_development_runner_design_declaration()["configuration"][
        "partition"
    ]

    assert source["whole_member_hash_required"] is True
    assert source["duplicate_member_names_permitted"] is False
    assert source["encrypted_members_permitted"] is False
    assert partition["start_inclusive"] == "2019-01-01T00:00:00Z"
    assert partition["end_exclusive"] == "2024-04-01T00:00:00Z"
    assert partition["nondevelopment_timestamp_token_read_permitted"] is True
    assert partition["nondevelopment_market_value_parse_permitted"] is False


def test_exact_development_rows_and_gaps_are_frozen():
    partition = weekly_development_runner_design_declaration()["configuration"][
        "partition"
    ]

    assert partition["expected_calendar_rows_per_asset"] == (
        EXPECTED_DEVELOPMENT_CALENDAR_ROWS
    )
    assert partition["expected_source_by_asset"] == EXPECTED_DEVELOPMENT_SOURCE
    assert [EXPECTED_DEVELOPMENT_SOURCE[asset]["observed_rows"] for asset in ASSET_ORDER] == [
        1916,
        1917,
        1915,
    ]
    assert EXPECTED_DEVELOPMENT_SOURCE["BTC-USD"]["missing_timestamps"] == (
        "2024-03-31T00:00:00Z",
    )
    assert EXPECTED_DEVELOPMENT_SOURCE["ETH-USD"]["missing_timestamps"] == ()
    assert EXPECTED_DEVELOPMENT_SOURCE["XRP-USD"]["missing_timestamps"] == (
        "2022-05-11T00:00:00Z",
        "2022-05-12T00:00:00Z",
    )


def test_invalid_market_weeks_and_gap_reset_parity_are_frozen():
    adapter = weekly_development_runner_design_declaration()["configuration"][
        "adapter"
    ]

    assert tuple(adapter["expected_invalid_market_week_starts"]) == (
        EXPECTED_INVALID_MARKET_WEEK_STARTS
    )
    assert EXPECTED_INVALID_MARKET_WEEK_STARTS == (
        "2018-12-31T00:00:00Z",
        "2022-05-09T00:00:00Z",
        "2024-03-25T00:00:00Z",
    )
    assert "GAP_RESET" in adapter["parity_scope"]
    assert adapter["synthetic_authorization_token_reuse_permitted"] is False
    assert adapter["trusted_real_entrypoint_public"] is False


def test_rule_order_controls_and_no_model_are_frozen():
    experiment = weekly_development_runner_design_declaration()["configuration"][
        "experiment"
    ]

    assert PRIMARY_RULE_ID == "PERSISTENT_UP_ASSET_MOMENTUM"
    assert RULE_ORDER == (PRIMARY_RULE_ID, *CONTROL_ORDER)
    assert tuple(experiment["rule_order"]) == RULE_ORDER
    assert tuple(experiment["control_order"]) == CONTROL_ORDER
    assert experiment["controls_candidate_eligible"] is False
    assert experiment["model_family"] == "NONE_RULE_BASED_SIGNAL_FEASIBILITY"
    assert experiment["model_fit_count"] == 0


def test_slices_event_identity_and_gate_semantics_are_frozen():
    experiment = weekly_development_runner_design_declaration()["configuration"][
        "experiment"
    ]

    assert experiment["slice_attribution_field"] == "decision_week_start"
    assert [item["slice_id"] for item in experiment["slices"]] == [
        "D1",
        "D2",
        "D3",
        "D4",
        "D5",
    ]
    assert experiment["invalid_future_boundary_counts_for_gates"] is False
    assert experiment["adjacent_events_retained"] is True
    assert experiment["empty_mean"] is None
    assert experiment["gates"] == DEVELOPMENT_GATES
    assert DEVELOPMENT_GATES["maximum_largest_positive_event_share"] == "0.40"


def test_result_is_review_only_or_terminal_hold_cash():
    result = weekly_development_runner_design_declaration()["configuration"][
        "result"
    ]

    assert result["pass_status"].endswith("INTEREST_REVIEW_REQUIRED")
    assert result["failure_status"].endswith("HYPOTHESIS_HOLD_CASH")
    assert result["pass_authorizes_candidate"] is False
    assert result["failure_closes_exact_hypothesis"] is True


def test_evidence_file_set_sidecars_and_atomicity_are_frozen():
    evidence = weekly_development_runner_design_declaration()["configuration"][
        "evidence"
    ]

    assert tuple(evidence["file_order"]) == EVIDENCE_FILE_ORDER
    assert len(EVIDENCE_FILE_ORDER) == 4
    assert evidence["binary_ascii_lf_sidecars"] is True
    assert evidence["sidecar_format"] == "SHA256_TWO_SPACES_FILENAME_LF"
    assert evidence["existing_final_or_staging_blocks_run"] is True
    assert evidence["failed_staging_preserved"] is True
    assert evidence["atomic_final_rename_required"] is True
    assert evidence["model_artifact_count"] == 0
    assert evidence["reader_opens_source_archive"] is False
    assert evidence["reader_writes_files"] is False


def test_future_authorization_is_named_but_inactive():
    result = weekly_development_runner_design_declaration()

    assert result["future_authorization_phrase"] == FUTURE_AUTHORIZATION_PHRASE
    assert result["authorization_phrase_active"] is False
    assert result["development_run_authorized"] is False
    assert result["development_run_executed"] is False


def test_all_design_and_safety_flags_are_exact():
    result = weekly_development_runner_design_declaration()

    assert all(result[name] is True for name in DESIGN_TRUE_FLAGS)
    assert all(result[name] is False for name in DESIGN_FALSE_FLAGS)
    assert result["filesystem_reader_implemented"] is False
    assert result["source_values_opened"] is False
    assert result["real_weekly_aggregation_executed"] is False
    assert result["real_outcomes_generated"] is False
    assert result["development_gates_executed"] is False
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False
    assert result["candidate_v2_authorized"] is False
    assert result["real_orders_submitted"] is False


def test_every_source_binding_is_a_sha256_digest():
    result = weekly_development_runner_design_declaration()

    assert result["source_binding_sha256"] == SOURCE_BINDING_SHA256
    assert len(SOURCE_BINDING_SHA256) == 13
    assert all(len(value) == 64 for value in SOURCE_BINDING_SHA256.values())
    assert all(set(value) <= set("0123456789abcdef") for value in SOURCE_BINDING_SHA256.values())


def test_declaration_is_deterministic_and_defensively_copied():
    first = weekly_development_runner_design_declaration()
    second = weekly_development_runner_design_declaration()

    assert first == second
    assert first["configuration_sha256"] == (
        "5af20c03ffbcffddd498b2b489910ca8eedabd6ee63bf56db66d5e4974fade90"
    )
    first["configuration"]["source"]["archive"]["bytes"] = 1
    first["source_binding_sha256"]["line_ending_policy"] = "0" * 64
    assert weekly_development_runner_design_declaration() == second


def test_validator_accepts_only_the_exact_frozen_design():
    declaration = weekly_development_runner_design_declaration()

    validated = validate_weekly_development_runner_design(declaration)

    assert validated == declaration
    assert validated is not declaration


@pytest.mark.parametrize("candidate", [None, [], (), "design"])
def test_validator_rejects_nondictionaries(candidate):
    with pytest.raises(TypeError, match="dictionary"):
        validate_weekly_development_runner_design(candidate)


def test_validator_rejects_unknown_missing_changed_and_open_fields():
    unknown = weekly_development_runner_design_declaration()
    unknown["surprise"] = True
    with pytest.raises(ValueError, match="Unknown"):
        validate_weekly_development_runner_design(unknown)

    missing = weekly_development_runner_design_declaration()
    missing.pop("run_id")
    with pytest.raises(ValueError, match="Missing"):
        validate_weekly_development_runner_design(missing)

    changed = weekly_development_runner_design_declaration()
    changed["configuration"]["experiment"]["model_fit_count"] = 1
    with pytest.raises(ValueError, match="differs"):
        validate_weekly_development_runner_design(changed)

    opened = weekly_development_runner_design_declaration()
    opened["source_values_opened"] = True
    with pytest.raises(ValueError, match="differs"):
        validate_weekly_development_runner_design(opened)


def test_main_prints_only_the_inert_design(capsys):
    assert main() == 0
    result = json.loads(capsys.readouterr().out)

    assert result["status"].endswith("DESIGN_FROZEN_NO_DATA_OR_RUN")
    assert result["source_values_opened"] is False
    assert result["development_run_executed"] is False
    assert result["real_orders_submitted"] is False
