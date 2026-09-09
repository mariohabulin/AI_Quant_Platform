"""Declarative hash-bound weekly Development runner design; no data access."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-weekly-persistent-up-momentum-"
    "development-runner-design-v1"
)
COMPONENT_ID = (
    "kraken-weekly-persistent-up-momentum-development-runner-design-v1"
)
RUN_ID = "kraken-weekly-persistent-up-momentum-development-v1"
PARENT_COMMIT = "615cc8544aeeddda7163b59a343f099c96d49789"
HYPOTHESIS_PROTOCOL_ID = (
    "kraken-btc-eth-xrp-weekly-persistent-up-momentum-hypothesis-v1"
)
SYNTHETIC_PROTOCOL_ID = (
    "kraken-btc-eth-xrp-weekly-persistent-up-momentum-"
    "synthetic-implementation-v1"
)
FUTURE_AUTHORIZATION_PHRASE = (
    "EXECUTE_KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_ONCE"
)

DATASET_ID = (
    "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
)
DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
ARCHIVE_SPEC = {
    "filename": "Kraken_OHLCVT.zip",
    "bytes": 7_885_068_519,
    "sha256": "e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d",
}

ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
MEMBER_BASENAME_BY_ASSET = {
    "BTC-USD": "XBTUSD_1440.csv",
    "ETH-USD": "ETHUSD_1440.csv",
    "XRP-USD": "XRPUSD_1440.csv",
}
SOURCE_FIELD_ORDER = (
    "Unix time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Trades",
)
ENGINE_FIELD_ORDER = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "trades",
)
ADAPTER_FIELD_MAP = tuple(zip(SOURCE_FIELD_ORDER, ENGINE_FIELD_ORDER, strict=True))

DEVELOPMENT_START = "2019-01-01T00:00:00Z"
DEVELOPMENT_END_EXCLUSIVE = "2024-04-01T00:00:00Z"
EXPECTED_DEVELOPMENT_CALENDAR_ROWS = 1917
EXPECTED_DEVELOPMENT_SOURCE = {
    "BTC-USD": {
        "observed_rows": 1916,
        "first_timestamp": "2019-01-01T00:00:00Z",
        "last_timestamp": "2024-03-30T00:00:00Z",
        "missing_timestamps": ("2024-03-31T00:00:00Z",),
    },
    "ETH-USD": {
        "observed_rows": 1917,
        "first_timestamp": "2019-01-01T00:00:00Z",
        "last_timestamp": "2024-03-31T00:00:00Z",
        "missing_timestamps": (),
    },
    "XRP-USD": {
        "observed_rows": 1915,
        "first_timestamp": "2019-01-01T00:00:00Z",
        "last_timestamp": "2024-03-31T00:00:00Z",
        "missing_timestamps": (
            "2022-05-11T00:00:00Z",
            "2022-05-12T00:00:00Z",
        ),
    },
}
EXPECTED_INVALID_MARKET_WEEK_STARTS = (
    "2018-12-31T00:00:00Z",
    "2022-05-09T00:00:00Z",
    "2024-03-25T00:00:00Z",
)

PRIMARY_RULE_ID = "PERSISTENT_UP_ASSET_MOMENTUM"
CONTROL_ORDER = (
    "CURRENT_UP_ONLY_ASSET_MOMENTUM_CONTROL",
    "PERSISTENT_UP_MARKET_ONLY_CONTROL",
)
RULE_ORDER = (PRIMARY_RULE_ID, *CONTROL_ORDER)
COST_PROFILE_ORDER = ("KRAKEN_BASELINE_ADVERSE", "KRAKEN_STRESS_ADVERSE")
DEVELOPMENT_SLICES = (
    ("D1", "2019-02-04T00:00:00Z", "2020-01-06T00:00:00Z"),
    ("D2", "2020-01-06T00:00:00Z", "2021-01-04T00:00:00Z"),
    ("D3", "2021-01-04T00:00:00Z", "2022-01-03T00:00:00Z"),
    ("D4", "2022-01-03T00:00:00Z", "2023-01-02T00:00:00Z"),
    ("D5", "2023-01-02T00:00:00Z", "2024-04-01T00:00:00Z"),
)
DEVELOPMENT_GATES = {
    "minimum_valid_primary_events_per_asset": 30,
    "minimum_events_per_counted_slice": 4,
    "minimum_counted_slices": 4,
    "overall_baseline_mean_strictly_positive": True,
    "overall_stress_mean_nonnegative": True,
    "minimum_nonnegative_baseline_slices": 4,
    "minimum_nonnegative_stress_slices": 3,
    "maximum_largest_positive_event_share": "0.40",
    "minimum_assets_passing_every_asset_gate": 2,
    "minimum_assets_primary_strictly_beats_both_controls": 2,
}

SOURCE_BINDING_SHA256 = {
    "line_ending_policy": (
        "0cc450c4a2fe9a9fdf974fba4a75e7cd5d63b5897469b4f28e888d7c1bc1185e"
    ),
    "daily_dataset_protocol": (
        "814cd561e1869023832315050683665c142f3b216ae354d45019a28edcc6a05a"
    ),
    "daily_dataset_evidence": (
        "cd83822005525381024f0cd90130f34246ec609a90436c714b79633daed82184"
    ),
    "daily_dataset_component": (
        "82692459a4267f9f9e67f163a59e67c7a085fa3b7cc1cd81d3da8b147b3a4965"
    ),
    "partition_protocol": (
        "091d64ca9b7f80f8f3ebae2f3038b78cc305f49b19042a159a8e9050db5476ac"
    ),
    "partition_component": (
        "337d44259a05d1d7b10a3b81f636f776f0752411eab0bb239e8cf7f485da5a37"
    ),
    "partition_review": (
        "b24c5249765191e965661b280ef4af1b47ee1d68d9d85b13e014a7071b5b02e9"
    ),
    "hypothesis_protocol": (
        "06c2e0f25a6a237b8b490d12865973c6c4d9118bd378e42c2113e41f907658f1"
    ),
    "hypothesis_component": (
        "a8c22d3f2e4d1dc4584b1926fe537afec0962b33f0693e891b1ca657bc9a1772"
    ),
    "hypothesis_review": (
        "b362a2f8b70f44ae07357e34dcadc97141a96695e1327d0694193035add6fc92"
    ),
    "synthetic_protocol": (
        "297bccf162d780748cdc6dbd120989f73c76489fba97d445c4baf8f5413604c3"
    ),
    "synthetic_component": (
        "cae67fe56a008f1c9639f570d443c167ede4c5cb93ece291b4d1a29a0e7c0bc8"
    ),
    "synthetic_review": (
        "5bb8642005991643668c7f5542f753a8fee64bc3e1915c8480654d50045977f9"
    ),
}

FINAL_DIRECTORY_NAME = "kraken_weekly_persistent_up_momentum_development_v1"
STAGING_DIRECTORY_NAME = "." + FINAL_DIRECTORY_NAME + ".staging"
REPORT_FILENAME = (
    "kraken_weekly_persistent_up_momentum_development_report.json"
)
DECISIONS_FILENAME = (
    "kraken_weekly_persistent_up_momentum_decisions.json"
)
EVIDENCE_FILE_ORDER = (
    REPORT_FILENAME,
    REPORT_FILENAME + ".sha256",
    DECISIONS_FILENAME,
    DECISIONS_FILENAME + ".sha256",
)

DESIGN_TRUE_FLAGS = (
    "runner_design_frozen",
    "exact_archive_identity_designed",
    "unique_member_identity_designed",
    "development_only_value_reader_designed",
    "opaque_nondevelopment_values_designed",
    "full_grid_gap_identity_designed",
    "decimal_text_adapter_designed",
    "synthetic_parity_tests_required",
    "exact_gate_evaluator_designed",
    "canonical_binary_lf_sidecars_designed",
    "one_shot_atomic_evidence_designed",
    "independent_evidence_recomputation_designed",
)
DESIGN_FALSE_FLAGS = (
    "filesystem_reader_implemented",
    "network_reader_implemented",
    "trusted_real_adapter_implemented",
    "development_gate_evaluator_implemented",
    "evidence_writer_implemented",
    "independent_evidence_reader_implemented",
    "authorization_phrase_active",
    "source_values_opened",
    "kraken_archive_opened",
    "real_weekly_aggregation_executed",
    "real_outcomes_generated",
    "development_gates_executed",
    "development_run_authorized",
    "development_run_executed",
    "model_training_authorized",
    "model_training_executed",
    "parameter_search_authorized",
    "threshold_search_authorized",
    "automatic_asset_selection_authorized",
    "calibration_data_opened",
    "evaluation_data_opened",
    "candidate_v2_authorized",
    "bounded_forward_paper_authorized",
    "cloud_execution_authorized",
    "real_orders_submitted",
    "live_execution_authorized",
)


def _canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _configuration():
    return {
        "source": {
            "dataset_id": DATASET_ID,
            "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
            "archive": dict(ARCHIVE_SPEC),
            "asset_order": list(ASSET_ORDER),
            "member_basename_by_asset": dict(MEMBER_BASENAME_BY_ASSET),
            "source_field_order": list(SOURCE_FIELD_ORDER),
            "whole_member_hash_required": True,
            "duplicate_member_names_permitted": False,
            "encrypted_members_permitted": False,
            "network_fallback_permitted": False,
            "quarterly_archive_required": False,
        },
        "partition": {
            "name": "DEVELOPMENT",
            "start_inclusive": DEVELOPMENT_START,
            "end_exclusive": DEVELOPMENT_END_EXCLUSIVE,
            "expected_calendar_rows_per_asset": EXPECTED_DEVELOPMENT_CALENDAR_ROWS,
            "expected_source_by_asset": deepcopy(EXPECTED_DEVELOPMENT_SOURCE),
            "nondevelopment_timestamp_token_read_permitted": True,
            "nondevelopment_market_value_parse_permitted": False,
            "missing_timestamp_policy": "FULL_GRID_EXACT_EQUALITY_NO_FILL",
        },
        "adapter": {
            "field_map": [list(item) for item in ADAPTER_FIELD_MAP],
            "timestamp_output": "CANONICAL_UTC_MIDNIGHT",
            "numeric_transport": "EXACT_DECIMAL_TEXT_NO_BINARY_FLOAT",
            "synthetic_authorization_token_reuse_permitted": False,
            "trusted_real_entrypoint_public": False,
            "parity_scope": [
                "COMPLETE_WEEK_VALIDATION",
                "GAP_RESET",
                "RULE_ACTIONS",
                "DECIMAL_COST_ARITHMETIC",
            ],
            "expected_invalid_market_week_starts": list(
                EXPECTED_INVALID_MARKET_WEEK_STARTS
            ),
        },
        "experiment": {
            "rule_order": list(RULE_ORDER),
            "primary_rule_id": PRIMARY_RULE_ID,
            "control_order": list(CONTROL_ORDER),
            "cost_profile_order": list(COST_PROFILE_ORDER),
            "slice_attribution_field": "decision_week_start",
            "slices": [
                {
                    "slice_id": item[0],
                    "start_inclusive": item[1],
                    "end_exclusive": item[2],
                }
                for item in DEVELOPMENT_SLICES
            ],
            "valid_event": (
                "ELIGIBLE_ASSET_DECISION_RULE_WITH_T_PLUS_1_AND_T_PLUS_2_"
                "OPENS_INSIDE_DEVELOPMENT"
            ),
            "invalid_future_boundary_counts_for_gates": False,
            "adjacent_events_retained": True,
            "gate_means": "UNWEIGHTED_ARITHMETIC_VALID_EVENTS_ONLY",
            "empty_mean": None,
            "gates": deepcopy(DEVELOPMENT_GATES),
            "controls_candidate_eligible": False,
            "model_family": "NONE_RULE_BASED_SIGNAL_FEASIBILITY",
            "model_fit_count": 0,
            "parameter_or_threshold_rescue_permitted": False,
        },
        "result": {
            "pass_status": (
                "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_"
                "INTEREST_REVIEW_REQUIRED"
            ),
            "failure_status": (
                "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_NO_VIABLE_"
                "HYPOTHESIS_HOLD_CASH"
            ),
            "pass_authorizes_candidate": False,
            "failure_closes_exact_hypothesis": True,
        },
        "evidence": {
            "external_to_git_and_archive_required": True,
            "final_directory_name": FINAL_DIRECTORY_NAME,
            "staging_directory_name": STAGING_DIRECTORY_NAME,
            "file_order": list(EVIDENCE_FILE_ORDER),
            "canonical_json_utf8_lf": True,
            "binary_ascii_lf_sidecars": True,
            "sidecar_format": "SHA256_TWO_SPACES_FILENAME_LF",
            "existing_final_or_staging_blocks_run": True,
            "failed_staging_preserved": True,
            "atomic_final_rename_required": True,
            "model_artifact_count": 0,
            "reader_recomputes_all_summaries_and_gates": True,
            "reader_opens_source_archive": False,
            "reader_writes_files": False,
        },
    }


def weekly_development_runner_design_declaration():
    configuration = _configuration()
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "run_id": RUN_ID,
        "parent_commit": PARENT_COMMIT,
        "hypothesis_protocol_id": HYPOTHESIS_PROTOCOL_ID,
        "synthetic_protocol_id": SYNTHETIC_PROTOCOL_ID,
        "future_authorization_phrase": FUTURE_AUTHORIZATION_PHRASE,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "archive_spec": dict(ARCHIVE_SPEC),
        "source_binding_sha256": dict(SOURCE_BINDING_SHA256),
        "configuration": configuration,
        "configuration_sha256": hashlib.sha256(
            _canonical_json(configuration)
        ).hexdigest(),
        "status": (
            "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_RUNNER_"
            "DESIGN_FROZEN_NO_DATA_OR_RUN"
        ),
        "next_stage": (
            "SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_IMPLEMENTATION_DECISION"
        ),
    }
    result.update({name: True for name in DESIGN_TRUE_FLAGS})
    result.update({name: False for name in DESIGN_FALSE_FLAGS})
    return result


def validate_weekly_development_runner_design(candidate):
    if not isinstance(candidate, dict):
        raise TypeError("Weekly Development runner design must be a dictionary.")
    expected = weekly_development_runner_design_declaration()
    unknown = set(candidate) - set(expected)
    missing = set(expected) - set(candidate)
    if unknown:
        raise ValueError(f"Unknown weekly runner design fields: {sorted(unknown)}.")
    if missing:
        raise ValueError(f"Missing weekly runner design fields: {sorted(missing)}.")
    if candidate != expected:
        raise ValueError("Weekly Development runner design differs from the freeze.")
    if any(candidate[name] is not True for name in DESIGN_TRUE_FLAGS):
        raise ValueError("Weekly Development runner design contract is incomplete.")
    if any(candidate[name] is not False for name in DESIGN_FALSE_FLAGS):
        raise ValueError("Weekly Development runner design safety boundary is open.")
    return deepcopy(candidate)


def main():
    print(
        json.dumps(
            weekly_development_runner_design_declaration(),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
