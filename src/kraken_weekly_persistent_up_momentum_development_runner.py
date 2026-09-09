"""Hash-bound weekly Development runner; inert until exact authorization."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import zipfile

try:
    from kraken_weekly_persistent_up_momentum_development_runner_design import (
        ARCHIVE_SPEC as DESIGN_ARCHIVE_SPEC,
        ASSET_ORDER,
        CONTROL_ORDER,
        COST_PROFILE_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        DECISIONS_FILENAME,
        DEVELOPMENT_END_EXCLUSIVE,
        DEVELOPMENT_GATES,
        DEVELOPMENT_SLICES,
        DEVELOPMENT_START,
        ENGINE_FIELD_ORDER,
        EVIDENCE_FILE_ORDER,
        EXPECTED_DEVELOPMENT_CALENDAR_ROWS,
        EXPECTED_DEVELOPMENT_SOURCE,
        EXPECTED_INVALID_MARKET_WEEK_STARTS,
        FINAL_DIRECTORY_NAME,
        FUTURE_AUTHORIZATION_PHRASE,
        MEMBER_BASENAME_BY_ASSET,
        PRIMARY_RULE_ID,
        REPORT_FILENAME,
        RULE_ORDER,
        SOURCE_BINDING_SHA256 as DESIGN_SOURCE_BINDING_SHA256,
        SOURCE_FIELD_ORDER,
        STAGING_DIRECTORY_NAME,
        weekly_development_runner_design_declaration,
    )
    from kraken_weekly_persistent_up_momentum_synthetic import (
        SYNTHETIC_AUTHORIZATION_TOKEN,
        _aggregate_internal,
        _asset_momentum,
        _decimal_text,
        _iso,
        _market_four_week_return,
        _rule_actions,
        _state,
        _synthetic_outcome,
        _validated_daily_rows,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_weekly_persistent_up_momentum_development_runner_design import (
        ARCHIVE_SPEC as DESIGN_ARCHIVE_SPEC,
        ASSET_ORDER,
        CONTROL_ORDER,
        COST_PROFILE_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        DECISIONS_FILENAME,
        DEVELOPMENT_END_EXCLUSIVE,
        DEVELOPMENT_GATES,
        DEVELOPMENT_SLICES,
        DEVELOPMENT_START,
        ENGINE_FIELD_ORDER,
        EVIDENCE_FILE_ORDER,
        EXPECTED_DEVELOPMENT_CALENDAR_ROWS,
        EXPECTED_DEVELOPMENT_SOURCE,
        EXPECTED_INVALID_MARKET_WEEK_STARTS,
        FINAL_DIRECTORY_NAME,
        FUTURE_AUTHORIZATION_PHRASE,
        MEMBER_BASENAME_BY_ASSET,
        PRIMARY_RULE_ID,
        REPORT_FILENAME,
        RULE_ORDER,
        SOURCE_BINDING_SHA256 as DESIGN_SOURCE_BINDING_SHA256,
        SOURCE_FIELD_ORDER,
        STAGING_DIRECTORY_NAME,
        weekly_development_runner_design_declaration,
    )
    from .kraken_weekly_persistent_up_momentum_synthetic import (
        SYNTHETIC_AUTHORIZATION_TOKEN,
        _aggregate_internal,
        _asset_momentum,
        _decimal_text,
        _iso,
        _market_four_week_return,
        _rule_actions,
        _state,
        _synthetic_outcome,
        _validated_daily_rows,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-weekly-persistent-up-momentum-"
    "development-runner-implementation-v1"
)
COMPONENT_ID = "kraken-weekly-persistent-up-momentum-development-runner-v1"
RUN_ID = "kraken-weekly-persistent-up-momentum-development-v1"
PARENT_COMMIT = "0b51b8455f218793605cc6da086862e96776e50d"
AUTHORIZATION_PHRASE = FUTURE_AUTHORIZATION_PHRASE
RUNNER_SYNTHETIC_TEST_TOKEN = (
    "KRAKEN_WEEKLY_PERSISTENT_UP_RUNNER_SYNTHETIC_FIXTURE_V1"
)
INPUT_MODE = "HASH_BOUND_REAL_DEVELOPMENT"
FROZEN_ARCHIVE_SPEC = dict(DESIGN_ARCHIVE_SPEC)

SOURCE_BINDING_SHA256 = {
    **DESIGN_SOURCE_BINDING_SHA256,
    "runner_design_protocol": (
        "8aaf29337e124a27ff303db1158d565d790bdd1bd7c59f05db5b017ae7ee8163"
    ),
    "runner_design_component": (
        "89bd2bc3e13827f729e7af3f9e69280cb5134748ae3d9b62f5d3ba0f2089e97d"
    ),
    "runner_design_review": (
        "57f3ef695db23917a5668b470859387e64aac09eddcceb02c73657e0031c2eaa"
    ),
}

REPORT_SHA256_FILENAME = REPORT_FILENAME + ".sha256"
DECISIONS_SHA256_FILENAME = DECISIONS_FILENAME + ".sha256"
PASS_STATUS = (
    "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_"
    "INTEREST_REVIEW_REQUIRED"
)
FAILURE_STATUS = (
    "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_NO_VIABLE_HYPOTHESIS_HOLD_CASH"
)
RUN_COMPLETED_STATUS = (
    "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_COMPLETED_REVIEW_REQUIRED"
)
READER_PASS_STATUS = (
    "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_EVIDENCE_READER_PASS"
)

IMPLEMENTATION_TRUE_FLAGS = (
    "filesystem_reader_implemented",
    "exact_archive_hash_gate_implemented",
    "unique_member_gate_implemented",
    "development_only_value_parser_implemented",
    "opaque_nondevelopment_values_implemented",
    "full_grid_gap_identity_gate_implemented",
    "trusted_real_adapter_implemented",
    "synthetic_token_separation_implemented",
    "synthetic_adapter_parity_tests_implemented",
    "development_gate_evaluator_implemented",
    "canonical_binary_lf_sidecars_implemented",
    "one_shot_atomic_evidence_implemented",
    "independent_evidence_reader_implemented",
    "independent_gate_recomputation_implemented",
)
DECLARATION_FALSE_FLAGS = (
    "network_reader_implemented",
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

_TRUSTED_ADAPTER_CAPABILITY = object()


@dataclass(frozen=True)
class RecordedWeeklyDevelopmentEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    learning_status: str
    action: str
    valid_primary_event_count: int


def canonical_json_bytes(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256_path(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_utc(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def _timestamp_iso(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _parse_source_decimal(raw_value, label):
    try:
        text = raw_value.decode("ascii")
        value = Decimal(text)
    except (UnicodeDecodeError, InvalidOperation, ValueError) as exc:
        raise RuntimeError(f"Invalid exact decimal {label}.") from exc
    if not value.is_finite():
        raise RuntimeError(f"Non-finite exact decimal {label}.")
    return text, value


def _parse_trade_count(raw_value, label):
    text, value = _parse_source_decimal(raw_value, label)
    if value <= 0 or value != value.to_integral_value():
        raise RuntimeError(f"Trades must be a positive integer {label}.")
    return text


def _source_row(fields, member_name, row_number, timestamp):
    label = f"in Development row {member_name}:{row_number}"
    open_text, open_value = _parse_source_decimal(fields[1], f"Open {label}")
    high_text, high_value = _parse_source_decimal(fields[2], f"High {label}")
    low_text, low_value = _parse_source_decimal(fields[3], f"Low {label}")
    close_text, close_value = _parse_source_decimal(fields[4], f"Close {label}")
    volume_text, volume_value = _parse_source_decimal(fields[5], f"Volume {label}")
    trades_text = _parse_trade_count(fields[6], f"{label}")
    if min(open_value, high_value, low_value, close_value) <= 0:
        raise RuntimeError(f"OHLC values must be positive {label}.")
    if (
        high_value < max(open_value, close_value)
        or low_value > min(open_value, close_value)
        or high_value < low_value
    ):
        raise RuntimeError(f"OHLC geometry is invalid {label}.")
    if volume_value < 0:
        raise RuntimeError(f"Volume must be nonnegative {label}.")
    return {
        "timestamp": _timestamp_iso(timestamp),
        "open": open_text,
        "high": high_text,
        "low": low_text,
        "close": close_text,
        "volume": volume_text,
        "trades": trades_text,
    }


def _normalize_outcome(outcome):
    result = deepcopy(outcome)
    if result.get("status") == "VALID_SYNTHETIC_OUTCOME":
        result["status"] = "VALID_DEVELOPMENT_OUTCOME"
    return result


def _evaluate_trusted_development_rows(daily_rows_by_asset, *, capability):
    if capability is not _TRUSTED_ADAPTER_CAPABILITY:
        raise PermissionError("Trusted weekly Development adapter capability required.")
    validated = _validated_daily_rows(daily_rows_by_asset)
    week_starts, weekly_maps, aggregation = _aggregate_internal(validated)
    aggregation = deepcopy(aggregation)
    aggregation["status"] = "COMPLETE_WEEK_AGGREGATION_PASS"
    aggregation["input_mode"] = INPUT_MODE

    decisions = []
    valid_outcomes = {rule: 0 for rule in RULE_ORDER}
    invalid_outcomes = {rule: 0 for rule in RULE_ORDER}
    long_decisions = {rule: 0 for rule in RULE_ORDER}
    segment = []

    for week_start in week_starts:
        market_complete = all(
            weekly_maps[asset][week_start] is not None for asset in ASSET_ORDER
        )
        if market_complete:
            segment.append(week_start)
        else:
            segment = []

        current_market_return = None
        previous_market_return = None
        if len(segment) >= 5:
            current_market_return = _market_four_week_return(segment, weekly_maps)
        if len(segment) >= 6:
            previous_market_return = _market_four_week_return(
                segment[:-1], weekly_maps
            )
        current_state = _state(current_market_return)
        previous_state = _state(previous_market_return)

        for asset in ASSET_ORDER:
            momentum = None
            if len(segment) >= 5:
                momentum = _asset_momentum(segment, weekly_maps, asset)
            actions = _rule_actions(
                market_complete, current_state, previous_state, momentum
            )
            for rule in RULE_ORDER:
                if actions[rule]["action"] == "LONG":
                    long_decisions[rule] += 1
                    outcome = _normalize_outcome(
                        _synthetic_outcome(asset, week_start, weekly_maps)
                    )
                    if outcome["status"] == "VALID_DEVELOPMENT_OUTCOME":
                        valid_outcomes[rule] += 1
                    else:
                        invalid_outcomes[rule] += 1
                else:
                    outcome = {"status": "NOT_APPLICABLE_HOLD_CASH"}
                actions[rule]["outcome"] = outcome

            decisions.append(
                {
                    "asset": asset,
                    "decision_week_start": _iso(week_start),
                    "market_week_complete": market_complete,
                    "asset_week_complete": weekly_maps[asset][week_start] is not None,
                    "consecutive_complete_market_weeks": len(segment),
                    "market_four_week_return": (
                        None
                        if current_market_return is None
                        else _decimal_text(current_market_return)
                    ),
                    "previous_market_four_week_return": (
                        None
                        if previous_market_return is None
                        else _decimal_text(previous_market_return)
                    ),
                    "market_state_current": current_state,
                    "market_state_previous": previous_state,
                    "asset_four_week_momentum": (
                        None if momentum is None else _decimal_text(momentum)
                    ),
                    "rule_actions": actions,
                }
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "input_mode": INPUT_MODE,
        "asset_order": list(ASSET_ORDER),
        "rule_order": list(RULE_ORDER),
        "aggregation": aggregation,
        "decisions": decisions,
        "decision_count": len(decisions),
        "long_decision_count_by_rule": long_decisions,
        "valid_outcome_count_by_rule": valid_outcomes,
        "invalid_outcome_count_by_rule": invalid_outcomes,
        "status": "TRUSTED_WEEKLY_DEVELOPMENT_ADAPTER_PASS",
    }


def evaluate_runner_adapter_synthetic_fixture(
    daily_rows_by_asset, *, authorization_token
):
    if authorization_token != RUNNER_SYNTHETIC_TEST_TOKEN:
        raise PermissionError("Exact runner synthetic-fixture token is required.")
    if authorization_token == SYNTHETIC_AUTHORIZATION_TOKEN:
        raise PermissionError("Synthetic engine token reuse is prohibited.")
    result = _evaluate_trusted_development_rows(
        daily_rows_by_asset, capability=_TRUSTED_ADAPTER_CAPABILITY
    )
    result["input_mode"] = "RUNNER_SYNTHETIC_TEST_ONLY"
    result["aggregation"]["input_mode"] = "RUNNER_SYNTHETIC_TEST_ONLY"
    result["source_values_opened"] = False
    result["kraken_archive_opened"] = False
    result["development_run_executed"] = False
    return result


def _slice_id(timestamp):
    value = _parse_utc(timestamp)
    for slice_id, start, end in DEVELOPMENT_SLICES:
        if _parse_utc(start) <= value < _parse_utc(end):
            return slice_id
    return None


def _mean(values):
    if not values:
        return None
    with localcontext() as context:
        context.prec = 50
        return sum(values, Decimal(0)) / Decimal(len(values))


def _net_return(action, profile):
    try:
        value = Decimal(action["outcome"]["cost_profiles"][profile]["net_return"])
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise RuntimeError("Weekly Development outcome schema mismatch.") from exc
    if not value.is_finite():
        raise RuntimeError("Weekly Development outcome contains non-finite return.")
    return value


def _rule_asset_summary(decisions, asset, rule):
    valid = []
    invalid_count = 0
    for decision in decisions:
        if decision.get("asset") != asset:
            continue
        slice_id = _slice_id(decision.get("decision_week_start"))
        if slice_id is None:
            continue
        try:
            action = decision["rule_actions"][rule]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("Weekly Development decision schema mismatch.") from exc
        if action.get("action") != "LONG":
            continue
        status = action.get("outcome", {}).get("status")
        if status == "VALID_DEVELOPMENT_OUTCOME":
            valid.append((slice_id, action))
        elif status == "INVALID_MISSING_FUTURE_BOUNDARY":
            invalid_count += 1
        else:
            raise RuntimeError("Weekly Development LONG outcome status mismatch.")

    overall_means = {}
    for profile in COST_PROFILE_ORDER:
        mean = _mean([_net_return(action, profile) for _, action in valid])
        overall_means[profile] = None if mean is None else _decimal_text(mean)

    slices = []
    for slice_id, _, _ in DEVELOPMENT_SLICES:
        selected = [action for observed, action in valid if observed == slice_id]
        means = {}
        for profile in COST_PROFILE_ORDER:
            mean = _mean([_net_return(action, profile) for action in selected])
            means[profile] = None if mean is None else _decimal_text(mean)
        slices.append(
            {"slice_id": slice_id, "valid_event_count": len(selected), "mean_net_return": means}
        )

    return {
        "asset": asset,
        "rule_id": rule,
        "valid_event_count": len(valid),
        "invalid_future_boundary_count": invalid_count,
        "overall_mean_net_return": overall_means,
        "slice_summaries": slices,
        "positive_baseline_returns": [
            _net_return(action, COST_PROFILE_ORDER[0])
            for _, action in valid
            if _net_return(action, COST_PROFILE_ORDER[0]) > 0
        ],
    }


def _decimal_or_none(value):
    return None if value is None else Decimal(value)


def _primary_asset_review(summary):
    baseline = _decimal_or_none(
        summary["overall_mean_net_return"][COST_PROFILE_ORDER[0]]
    )
    stress = _decimal_or_none(
        summary["overall_mean_net_return"][COST_PROFILE_ORDER[1]]
    )
    baseline_slice_means = [
        _decimal_or_none(item["mean_net_return"][COST_PROFILE_ORDER[0]])
        for item in summary["slice_summaries"]
    ]
    stress_slice_means = [
        _decimal_or_none(item["mean_net_return"][COST_PROFILE_ORDER[1]])
        for item in summary["slice_summaries"]
    ]
    positives = summary.pop("positive_baseline_returns")
    concentration = None
    if positives:
        with localcontext() as context:
            context.prec = 50
            concentration = max(positives) / sum(positives, Decimal(0))

    gates = {
        "minimum_valid_primary_events": (
            summary["valid_event_count"]
            >= DEVELOPMENT_GATES["minimum_valid_primary_events_per_asset"]
        ),
        "slice_support": (
            sum(
                item["valid_event_count"]
                >= DEVELOPMENT_GATES["minimum_events_per_counted_slice"]
                for item in summary["slice_summaries"]
            )
            >= DEVELOPMENT_GATES["minimum_counted_slices"]
        ),
        "overall_baseline_mean_positive": baseline is not None and baseline > 0,
        "overall_stress_mean_nonnegative": stress is not None and stress >= 0,
        "baseline_slice_stability": (
            sum(value is not None and value >= 0 for value in baseline_slice_means)
            >= DEVELOPMENT_GATES["minimum_nonnegative_baseline_slices"]
        ),
        "stress_slice_stability": (
            sum(value is not None and value >= 0 for value in stress_slice_means)
            >= DEVELOPMENT_GATES["minimum_nonnegative_stress_slices"]
        ),
        "positive_profit_concentration": (
            concentration is not None
            and concentration
            <= Decimal(DEVELOPMENT_GATES["maximum_largest_positive_event_share"])
        ),
    }
    summary["largest_positive_baseline_event_share"] = (
        None if concentration is None else _decimal_text(concentration)
    )
    summary["gates"] = gates
    summary["failed_gates"] = [name for name, passed in gates.items() if not passed]
    summary["passes_all_asset_gates"] = all(gates.values())
    return summary


def _evaluate_development_gates(decisions):
    if not isinstance(decisions, list):
        raise TypeError("Weekly Development decisions must be a list.")
    summaries = {rule: {} for rule in RULE_ORDER}
    asset_reviews = {}
    comparison_wins = []
    for asset in ASSET_ORDER:
        for rule in RULE_ORDER:
            summaries[rule][asset] = _rule_asset_summary(decisions, asset, rule)
        asset_reviews[asset] = _primary_asset_review(
            deepcopy(summaries[PRIMARY_RULE_ID][asset])
        )
        primary_mean = _decimal_or_none(
            summaries[PRIMARY_RULE_ID][asset]["overall_mean_net_return"][
                COST_PROFILE_ORDER[0]
            ]
        )
        control_means = [
            _decimal_or_none(
                summaries[rule][asset]["overall_mean_net_return"][
                    COST_PROFILE_ORDER[0]
                ]
            )
            for rule in CONTROL_ORDER
        ]
        beats = (
            primary_mean is not None
            and all(value is not None and primary_mean > value for value in control_means)
        )
        asset_reviews[asset]["primary_strictly_beats_both_controls"] = beats
        if beats:
            comparison_wins.append(asset)

    for rule in RULE_ORDER:
        for asset in ASSET_ORDER:
            summaries[rule][asset].pop("positive_baseline_returns")
    passing_assets = [
        asset
        for asset in ASSET_ORDER
        if asset_reviews[asset]["passes_all_asset_gates"]
    ]
    cross_asset_gates = {
        "minimum_assets_passing_all_gates": (
            len(passing_assets)
            >= DEVELOPMENT_GATES["minimum_assets_passing_every_asset_gate"]
        ),
        "primary_beats_both_controls_on_minimum_assets": (
            len(comparison_wins)
            >= DEVELOPMENT_GATES[
                "minimum_assets_primary_strictly_beats_both_controls"
            ]
        ),
    }
    viable = all(cross_asset_gates.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "primary_rule_id": PRIMARY_RULE_ID,
        "control_order": list(CONTROL_ORDER),
        "rule_summaries": summaries,
        "primary_asset_reviews": asset_reviews,
        "passing_asset_order": passing_assets,
        "control_comparison_win_asset_order": comparison_wins,
        "cross_asset_gates": cross_asset_gates,
        "development_viable": viable,
        "learning_status": PASS_STATUS if viable else FAILURE_STATUS,
        "action": "HOLD_CASH",
        "candidate_v2_authorized": False,
    }


def evaluate_development_gates_synthetic_fixture(
    decisions, *, authorization_token
):
    if authorization_token != RUNNER_SYNTHETIC_TEST_TOKEN:
        raise PermissionError("Exact runner synthetic-fixture token is required.")
    result = _evaluate_development_gates(deepcopy(decisions))
    result["input_mode"] = "RUNNER_SYNTHETIC_TEST_ONLY"
    result["development_gates_executed_on_real_data"] = False
    return result


def _validate_recorded_aggregation(aggregation):
    if not isinstance(aggregation, dict):
        raise RuntimeError("Weekly Development aggregation evidence missing.")
    expected = {
        "status": "COMPLETE_WEEK_AGGREGATION_PASS",
        "input_mode": INPUT_MODE,
        "fill_or_interpolation_used": False,
    }
    if any(aggregation.get(name) != value for name, value in expected.items()):
        raise RuntimeError("Weekly Development aggregation identity mismatch.")
    invalid_by_asset = aggregation.get("invalid_weeks_by_asset")
    if not isinstance(invalid_by_asset, dict) or tuple(invalid_by_asset) != ASSET_ORDER:
        raise RuntimeError("Weekly Development invalid-week registry mismatch.")
    observed = set()
    for asset in ASSET_ORDER:
        entries = invalid_by_asset[asset]
        if not isinstance(entries, list):
            raise RuntimeError("Weekly Development invalid-week evidence mismatch.")
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(
                entry.get("week_start"), str
            ):
                raise RuntimeError("Weekly Development invalid-week evidence mismatch.")
            observed.add(entry["week_start"])
    if tuple(sorted(observed)) != tuple(EXPECTED_INVALID_MARKET_WEEK_STARTS):
        raise RuntimeError("Weekly Development invalid market weeks mismatch.")


def _verify_file_and_sidecar(root, filename):
    path = root / filename
    sidecar = root / f"{filename}.sha256"
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected_sidecar = f"{digest}  {filename}\n".encode("ascii")
    if sidecar.read_bytes() != expected_sidecar:
        raise RuntimeError(f"Weekly Development sidecar mismatch: {filename}.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Weekly Development JSON invalid: {filename}.") from exc
    if canonical_json_bytes(payload) != raw:
        raise RuntimeError(f"Weekly Development JSON is not canonical: {filename}.")
    return payload, digest, len(raw)


def _validate_recorded_member_evidence(items):
    if not isinstance(items, list) or len(items) != len(ASSET_ORDER):
        raise RuntimeError("Weekly Development member evidence registry mismatch.")
    for asset, item in zip(ASSET_ORDER, items, strict=True):
        expected = EXPECTED_DEVELOPMENT_SOURCE[asset]
        if not isinstance(item, dict) or item.get("asset") != asset:
            raise RuntimeError("Weekly Development member asset order mismatch.")
        if item.get("member_basename") != MEMBER_BASENAME_BY_ASSET[asset]:
            raise RuntimeError(f"Weekly Development member basename mismatch: {asset}.")
        member_name = item.get("member_name", "")
        if not isinstance(member_name, str) or PurePosixPath(member_name).name != item[
            "member_basename"
        ]:
            raise RuntimeError(f"Weekly Development member name mismatch: {asset}.")
        for size_name in ("compressed_bytes", "uncompressed_bytes"):
            if not isinstance(item.get(size_name), int) or item[size_name] < 0:
                raise RuntimeError(
                    f"Weekly Development member size invalid: {asset}."
                )
        crc32 = item.get("crc32", "")
        if len(crc32) != 8 or set(crc32) - set("0123456789abcdef"):
            raise RuntimeError(f"Weekly Development member CRC invalid: {asset}.")
        if item.get("development_rows") != expected["observed_rows"]:
            raise RuntimeError(f"Weekly Development member row count mismatch: {asset}.")
        if item.get("expected_calendar_rows") != EXPECTED_DEVELOPMENT_CALENDAR_ROWS:
            raise RuntimeError(f"Weekly Development calendar count mismatch: {asset}.")
        if tuple(item.get("missing_development_timestamps", ())) != tuple(
            expected["missing_timestamps"]
        ):
            raise RuntimeError(f"Weekly Development member gap mismatch: {asset}.")
        if item.get("first_development_timestamp") != expected["first_timestamp"]:
            raise RuntimeError(f"Weekly Development member first timestamp mismatch: {asset}.")
        if item.get("last_development_timestamp") != expected["last_timestamp"]:
            raise RuntimeError(f"Weekly Development member last timestamp mismatch: {asset}.")
        digest = item.get("member_uncompressed_sha256", "")
        if len(digest) != 64 or set(digest) - set("0123456789abcdef"):
            raise RuntimeError(f"Weekly Development member hash invalid: {asset}.")
        if item.get("nondevelopment_timestamp_tokens_read") is not True:
            raise RuntimeError(
                f"Weekly Development timestamp-token evidence mismatch: {asset}."
            )
        if item.get("nondevelopment_market_values_parsed") is not False:
            raise RuntimeError(f"Weekly Development non-Development values opened: {asset}.")


def _validate_decision_payload_counts(payload):
    expected_identity = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "run_id": RUN_ID,
    }
    if any(payload.get(name) != value for name, value in expected_identity.items()):
        raise RuntimeError("Weekly Development decisions identity mismatch.")
    if payload.get("asset_order") != list(ASSET_ORDER):
        raise RuntimeError("Weekly Development decisions asset order mismatch.")
    if payload.get("rule_order") != list(RULE_ORDER):
        raise RuntimeError("Weekly Development decisions rule order mismatch.")
    _validate_recorded_aggregation(payload.get("aggregation"))
    decisions = payload.get("decisions")
    if not isinstance(decisions, list) or payload.get("decision_count") != len(decisions):
        raise RuntimeError("Weekly Development decision count mismatch.")
    long_counts = {rule: 0 for rule in RULE_ORDER}
    valid_counts = {rule: 0 for rule in RULE_ORDER}
    invalid_counts = {rule: 0 for rule in RULE_ORDER}
    for decision in decisions:
        if decision.get("asset") not in ASSET_ORDER:
            raise RuntimeError("Weekly Development decision asset mismatch.")
        actions = decision.get("rule_actions")
        if not isinstance(actions, dict) or set(actions) != set(RULE_ORDER):
            raise RuntimeError("Weekly Development decision rule registry mismatch.")
        for rule in RULE_ORDER:
            action = actions[rule]
            if action.get("action") == "LONG":
                long_counts[rule] += 1
                status = action.get("outcome", {}).get("status")
                if status == "VALID_DEVELOPMENT_OUTCOME":
                    valid_counts[rule] += 1
                elif status == "INVALID_MISSING_FUTURE_BOUNDARY":
                    invalid_counts[rule] += 1
                else:
                    raise RuntimeError("Weekly Development LONG outcome status mismatch.")
            elif action.get("action") != "HOLD_CASH":
                raise RuntimeError("Weekly Development action mismatch.")
            elif action.get("outcome") != {"status": "NOT_APPLICABLE_HOLD_CASH"}:
                raise RuntimeError("Weekly Development HOLD_CASH outcome mismatch.")
    expected = {
        "long_decision_count_by_rule": long_counts,
        "valid_outcome_count_by_rule": valid_counts,
        "invalid_outcome_count_by_rule": invalid_counts,
    }
    if any(payload.get(name) != value for name, value in expected.items()):
        raise RuntimeError("Weekly Development recorded decision counts mismatch.")
    return decisions, valid_counts


def read_weekly_development_evidence(evidence_directory):
    root = Path(evidence_directory)
    if not root.is_dir() or root.name != FINAL_DIRECTORY_NAME:
        raise RuntimeError("Weekly Development evidence directory identity mismatch.")
    observed_files = {item.name for item in root.iterdir()}
    if observed_files != set(EVIDENCE_FILE_ORDER):
        raise RuntimeError("Weekly Development evidence file registry mismatch.")
    report, report_digest, _ = _verify_file_and_sidecar(root, REPORT_FILENAME)
    decisions_payload, decisions_digest, decisions_bytes = _verify_file_and_sidecar(
        root, DECISIONS_FILENAME
    )
    expected_identity = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "run_id": RUN_ID,
        "implementation_parent_commit": PARENT_COMMIT,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "partition": "DEVELOPMENT",
        "development_start_inclusive": DEVELOPMENT_START,
        "development_end_exclusive": DEVELOPMENT_END_EXCLUSIVE,
    }
    if any(report.get(name) != value for name, value in expected_identity.items()):
        raise RuntimeError("Weekly Development report identity mismatch.")
    if report.get("source_binding_sha256") != SOURCE_BINDING_SHA256:
        raise RuntimeError("Weekly Development report source binding mismatch.")
    design = weekly_development_runner_design_declaration()
    if report.get("runner_design_configuration_sha256") != design[
        "configuration_sha256"
    ]:
        raise RuntimeError("Weekly Development design configuration mismatch.")
    archive = report.get("source_archive", {})
    if archive != FROZEN_ARCHIVE_SPEC:
        raise RuntimeError("Weekly Development archive evidence mismatch.")
    _validate_recorded_member_evidence(report.get("source_member_evidence"))
    if report.get("expected_invalid_market_week_starts") != list(
        EXPECTED_INVALID_MARKET_WEEK_STARTS
    ):
        raise RuntimeError("Weekly Development invalid-week evidence mismatch.")
    artifact = report.get("decisions_artifact", {})
    if artifact != {
        "path": DECISIONS_FILENAME,
        "checksum_path": DECISIONS_SHA256_FILENAME,
        "bytes": decisions_bytes,
        "sha256": decisions_digest,
    }:
        raise RuntimeError("Weekly Development decisions artifact mismatch.")
    decisions, valid_counts = _validate_decision_payload_counts(decisions_payload)
    recomputed = _evaluate_development_gates(decisions)
    if report.get("gate_review") != recomputed:
        raise RuntimeError("Weekly Development gate recomputation mismatch.")
    if report.get("learning_status") != recomputed["learning_status"]:
        raise RuntimeError("Weekly Development learning status mismatch.")
    if report.get("action") != recomputed["action"]:
        raise RuntimeError("Weekly Development action evidence mismatch.")
    if report.get("status") != RUN_COMPLETED_STATUS:
        raise RuntimeError("Weekly Development technical status mismatch.")
    if report.get("real_outcomes_generated") is not (sum(valid_counts.values()) > 0):
        raise RuntimeError("Weekly Development outcome-generation state mismatch.")
    required_true = (
        "source_values_opened",
        "kraken_archive_opened",
        "real_weekly_aggregation_executed",
        "development_gates_executed",
        "development_run_authorized",
        "development_run_executed",
    )
    if any(report.get(name) is not True for name in required_true):
        raise RuntimeError("Weekly Development executed-state evidence mismatch.")
    required_false = (
        "model_training_executed",
        "model_training_authorized",
        "parameter_search_authorized",
        "parameter_search_executed",
        "threshold_search_authorized",
        "threshold_search_executed",
        "automatic_asset_selection_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    if any(report.get(name) is not False for name in required_false):
        raise RuntimeError("Weekly Development negative safety evidence mismatch.")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": READER_PASS_STATUS,
        "report_sha256": report_digest,
        "learning_status": recomputed["learning_status"],
        "action": recomputed["action"],
        "valid_primary_event_count": sum(
            recomputed["rule_summaries"][PRIMARY_RULE_ID][asset][
                "valid_event_count"
            ]
            for asset in ASSET_ORDER
        ),
        "source_archive_opened_by_reader": False,
        "evidence_files_written_by_reader": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "real_orders_submitted": False,
    }


class KrakenWeeklyPersistentUpMomentumDevelopmentRunner:
    @staticmethod
    def _external_paths(archive_path, evidence_root):
        project_root = Path(__file__).resolve().parents[1]
        archive = Path(archive_path).resolve()
        evidence = Path(evidence_root).resolve()
        for path in (archive, evidence):
            if path == project_root or path.is_relative_to(project_root):
                raise ValueError("Weekly Development archive/evidence must remain external.")
        if (
            archive == evidence
            or archive.is_relative_to(evidence)
            or evidence.is_relative_to(archive)
        ):
            raise ValueError("Weekly Development archive and evidence must be distinct.")
        return archive, evidence

    @staticmethod
    def _assert_one_shot(evidence_root):
        final = evidence_root / FINAL_DIRECTORY_NAME
        staging = evidence_root / STAGING_DIRECTORY_NAME
        if final.exists():
            raise FileExistsError("Weekly Development final evidence already exists.")
        if staging.exists():
            raise FileExistsError("Weekly Development staging evidence already exists.")
        return final, staging

    @staticmethod
    def _validate_archive(archive_path):
        if not archive_path.is_file():
            raise FileNotFoundError(f"Weekly source archive missing: {archive_path}")
        if archive_path.name != FROZEN_ARCHIVE_SPEC["filename"]:
            raise ValueError("Weekly source archive filename mismatch.")
        size = archive_path.stat().st_size
        if size != FROZEN_ARCHIVE_SPEC["bytes"]:
            raise RuntimeError("Weekly source archive byte-size mismatch.")
        digest = _sha256_path(archive_path)
        if digest != FROZEN_ARCHIVE_SPEC["sha256"]:
            raise RuntimeError("Weekly source archive SHA256 mismatch.")
        return {"filename": archive_path.name, "bytes": size, "sha256": digest}

    @classmethod
    def _read_member(cls, archive, info, asset):
        start = int(_parse_utc(DEVELOPMENT_START).timestamp())
        end = int(_parse_utc(DEVELOPMENT_END_EXCLUSIVE).timestamp())
        digest = hashlib.sha256()
        rows = []
        timestamps = []
        previous = None
        with archive.open(info) as source:
            for row_number, raw_line in enumerate(source, start=1):
                digest.update(raw_line)
                stripped = raw_line.rstrip(b"\r\n")
                if not stripped:
                    continue
                fields = stripped.split(b",")
                if len(fields) != len(SOURCE_FIELD_ORDER):
                    raise RuntimeError(
                        f"Weekly source row must contain seven columns: {info.filename}:{row_number}."
                    )
                try:
                    timestamp = int(fields[0])
                except ValueError as exc:
                    raise RuntimeError(
                        f"Invalid weekly source timestamp: {info.filename}:{row_number}."
                    ) from exc
                if previous is not None and timestamp <= previous:
                    raise RuntimeError(
                        f"Weekly source timestamps not strictly increasing: {info.filename}."
                    )
                previous = timestamp
                if not start <= timestamp < end:
                    continue
                if timestamp % 86400:
                    raise RuntimeError(
                        f"Misaligned Development timestamp: {info.filename}:{row_number}."
                    )
                timestamps.append(timestamp)
                rows.append(_source_row(fields, info.filename, row_number, timestamp))

        expected = EXPECTED_DEVELOPMENT_SOURCE[asset]
        if len(rows) != expected["observed_rows"]:
            raise RuntimeError(f"Unexpected Development row count for {asset}.")
        observed_timestamps = set(timestamps)
        missing = [
            _timestamp_iso(timestamp)
            for timestamp in range(start, end, 86400)
            if timestamp not in observed_timestamps
        ]
        if tuple(missing) != tuple(expected["missing_timestamps"]):
            raise RuntimeError(f"Unexpected Development missing timestamps for {asset}.")
        if not timestamps:
            raise RuntimeError(f"No Development rows for {asset}.")
        if _timestamp_iso(timestamps[0]) != expected["first_timestamp"]:
            raise RuntimeError(f"Unexpected first Development timestamp for {asset}.")
        if _timestamp_iso(timestamps[-1]) != expected["last_timestamp"]:
            raise RuntimeError(f"Unexpected last Development timestamp for {asset}.")
        return rows, {
            "asset": asset,
            "member_name": info.filename,
            "member_basename": PurePosixPath(info.filename).name,
            "compressed_bytes": int(info.compress_size),
            "uncompressed_bytes": int(info.file_size),
            "crc32": f"{info.CRC:08x}",
            "member_uncompressed_sha256": digest.hexdigest(),
            "development_rows": len(rows),
            "expected_calendar_rows": EXPECTED_DEVELOPMENT_CALENDAR_ROWS,
            "missing_development_timestamps": missing,
            "first_development_timestamp": _timestamp_iso(timestamps[0]),
            "last_development_timestamp": _timestamp_iso(timestamps[-1]),
            "nondevelopment_timestamp_tokens_read": True,
            "nondevelopment_market_values_parsed": False,
        }

    @classmethod
    def _load_development_rows(cls, archive_path):
        rows_by_asset = {}
        evidence = []
        try:
            with zipfile.ZipFile(archive_path) as archive:
                infos = archive.infolist()
                names = [item.filename for item in infos]
                if len(names) != len(set(names)):
                    raise RuntimeError("Weekly source archive has duplicate member names.")
                if any(item.flag_bits & 0x1 for item in infos):
                    raise RuntimeError("Encrypted weekly source members are prohibited.")
                for asset in ASSET_ORDER:
                    required = MEMBER_BASENAME_BY_ASSET[asset]
                    matching = [
                        item
                        for item in infos
                        if not item.is_dir()
                        and PurePosixPath(item.filename).name == required
                    ]
                    if len(matching) != 1:
                        raise RuntimeError(
                            f"Weekly source requires exactly one {required} member."
                        )
                    rows, member_evidence = cls._read_member(
                        archive, matching[0], asset
                    )
                    rows_by_asset[asset] = rows
                    evidence.append(member_evidence)
        except zipfile.BadZipFile as exc:
            raise RuntimeError("Weekly source archive is not a valid ZIP.") from exc
        return rows_by_asset, evidence

    def run(self, archive_path, evidence_root, authorization_phrase):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError("Exact one-shot weekly Development authorization required.")
        archive_path, evidence_root = self._external_paths(
            archive_path, evidence_root
        )
        final, staging = self._assert_one_shot(evidence_root)
        evidence_root.mkdir(parents=True, exist_ok=True)
        staging.mkdir(exist_ok=False)

        archive_evidence = self._validate_archive(archive_path)
        daily_rows, member_evidence = self._load_development_rows(archive_path)
        evaluation = _evaluate_trusted_development_rows(
            daily_rows, capability=_TRUSTED_ADAPTER_CAPABILITY
        )
        _validate_recorded_aggregation(evaluation["aggregation"])
        gate_review = _evaluate_development_gates(evaluation["decisions"])
        decisions_payload = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "component_id": COMPONENT_ID,
            "run_id": RUN_ID,
            "asset_order": list(ASSET_ORDER),
            "rule_order": list(RULE_ORDER),
            "aggregation": evaluation["aggregation"],
            "decision_count": evaluation["decision_count"],
            "long_decision_count_by_rule": evaluation[
                "long_decision_count_by_rule"
            ],
            "valid_outcome_count_by_rule": evaluation[
                "valid_outcome_count_by_rule"
            ],
            "invalid_outcome_count_by_rule": evaluation[
                "invalid_outcome_count_by_rule"
            ],
            "decisions": evaluation["decisions"],
        }
        decisions_bytes = canonical_json_bytes(decisions_payload)
        decisions_sha256 = hashlib.sha256(decisions_bytes).hexdigest()
        design = weekly_development_runner_design_declaration()
        report = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "component_id": COMPONENT_ID,
            "run_id": RUN_ID,
            "implementation_parent_commit": PARENT_COMMIT,
            "source_binding_sha256": dict(SOURCE_BINDING_SHA256),
            "runner_design_configuration_sha256": design["configuration_sha256"],
            "dataset_id": DATASET_ID,
            "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
            "partition": "DEVELOPMENT",
            "development_start_inclusive": DEVELOPMENT_START,
            "development_end_exclusive": DEVELOPMENT_END_EXCLUSIVE,
            "source_archive": archive_evidence,
            "source_member_evidence": member_evidence,
            "expected_invalid_market_week_starts": list(
                EXPECTED_INVALID_MARKET_WEEK_STARTS
            ),
            "decisions_artifact": {
                "path": DECISIONS_FILENAME,
                "checksum_path": DECISIONS_SHA256_FILENAME,
                "bytes": len(decisions_bytes),
                "sha256": decisions_sha256,
            },
            "gate_review": gate_review,
            "learning_status": gate_review["learning_status"],
            "action": gate_review["action"],
            "source_values_opened": True,
            "kraken_archive_opened": True,
            "real_weekly_aggregation_executed": True,
            "real_outcomes_generated": sum(
                evaluation["valid_outcome_count_by_rule"].values()
            )
            > 0,
            "development_gates_executed": True,
            "development_run_authorized": True,
            "development_run_executed": True,
            "model_training_authorized": False,
            "model_training_executed": False,
            "parameter_search_authorized": False,
            "parameter_search_executed": False,
            "threshold_search_authorized": False,
            "threshold_search_executed": False,
            "automatic_asset_selection_authorized": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
            "status": RUN_COMPLETED_STATUS,
            "next_stage": "RUN_INDEPENDENT_READ_ONLY_WEEKLY_EVIDENCE_REVIEW",
        }
        report_bytes = canonical_json_bytes(report)
        report_sha256 = hashlib.sha256(report_bytes).hexdigest()
        (staging / DECISIONS_FILENAME).write_bytes(decisions_bytes)
        (staging / DECISIONS_SHA256_FILENAME).write_bytes(
            f"{decisions_sha256}  {DECISIONS_FILENAME}\n".encode("ascii")
        )
        (staging / REPORT_FILENAME).write_bytes(report_bytes)
        (staging / REPORT_SHA256_FILENAME).write_bytes(
            f"{report_sha256}  {REPORT_FILENAME}\n".encode("ascii")
        )
        os.replace(staging, final)
        locked = read_weekly_development_evidence(final)
        return RecordedWeeklyDevelopmentEvidence(
            report_path=final / REPORT_FILENAME,
            checksum_path=final / REPORT_SHA256_FILENAME,
            report_sha256=locked["report_sha256"],
            learning_status=locked["learning_status"],
            action=locked["action"],
            valid_primary_event_count=locked["valid_primary_event_count"],
        )


def runner_declaration():
    design = weekly_development_runner_design_declaration()
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "run_id": RUN_ID,
        "parent_commit": PARENT_COMMIT,
        "authorization_phrase": AUTHORIZATION_PHRASE,
        "synthetic_test_token": RUNNER_SYNTHETIC_TEST_TOKEN,
        "synthetic_engine_token_reused": False,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "frozen_archive_spec": dict(FROZEN_ARCHIVE_SPEC),
        "asset_order": list(ASSET_ORDER),
        "rule_order": list(RULE_ORDER),
        "development_slices": [list(item) for item in DEVELOPMENT_SLICES],
        "development_gates": dict(DEVELOPMENT_GATES),
        "evidence_file_order": list(EVIDENCE_FILE_ORDER),
        "source_binding_sha256": dict(SOURCE_BINDING_SHA256),
        "runner_design_configuration_sha256": design["configuration_sha256"],
        "model_artifact_count": 0,
        "status": (
            "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_DEVELOPMENT_RUNNER_"
            "IMPLEMENTED_NO_RUN_AUTHORIZATION"
        ),
        "next_stage": "SEPARATE_READ_ONLY_DEVELOPMENT_PREFLIGHT_DECISION",
    }
    result.update({name: True for name in IMPLEMENTATION_TRUE_FLAGS})
    result.update({name: False for name in DECLARATION_FALSE_FLAGS})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Execute or review frozen weekly Persistent-UP Development."
    )
    parser.add_argument("--declaration-only", action="store_true")
    parser.add_argument("--archive")
    parser.add_argument("--evidence-root")
    parser.add_argument("--authorization-phrase")
    parser.add_argument("--review-evidence")
    args = parser.parse_args(argv)
    if args.declaration_only:
        result = runner_declaration()
    elif args.review_evidence:
        result = read_weekly_development_evidence(args.review_evidence)
    elif all((args.archive, args.evidence_root, args.authorization_phrase)):
        recorded = KrakenWeeklyPersistentUpMomentumDevelopmentRunner().run(
            args.archive, args.evidence_root, args.authorization_phrase
        )
        result = {
            "status": "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_EVIDENCE_RECORDED",
            "report_path": str(recorded.report_path),
            "checksum_path": str(recorded.checksum_path),
            "report_sha256": recorded.report_sha256,
            "learning_status": recorded.learning_status,
            "action": recorded.action,
            "valid_primary_event_count": recorded.valid_primary_event_count,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "candidate_v2_authorized": False,
            "real_orders_submitted": False,
        }
    else:
        parser.error(
            "Use --declaration-only, --review-evidence, or all execution arguments."
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
