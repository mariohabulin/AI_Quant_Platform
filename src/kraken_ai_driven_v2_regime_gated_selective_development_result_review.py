"""Read-only terminal review for regime-gated selective Development Attempt 1."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

try:
    from kraken_ai_driven_v2_regime_gated_selective_development_runner import (
        MODEL_DIRECTORY_NAME,
        PREDICTIONS_FILENAME,
        PREDICTIONS_SHA256_FILENAME,
        REPORT_FILENAME,
        REPORT_SHA256_FILENAME,
        RUN_ID,
        STATUS_HOLD,
        canonical_json_bytes,
        read_regime_gated_selective_evidence,
    )
    from kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
        DIRECTION_ORDER,
        FOLD_PLAN,
        VARIANT_SPECS,
    )
    from kraken_ai_driven_v2_learning_core import ASSET_ORDER
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_regime_gated_selective_development_runner import (
        MODEL_DIRECTORY_NAME,
        PREDICTIONS_FILENAME,
        PREDICTIONS_SHA256_FILENAME,
        REPORT_FILENAME,
        REPORT_SHA256_FILENAME,
        RUN_ID,
        STATUS_HOLD,
        canonical_json_bytes,
        read_regime_gated_selective_evidence,
    )
    from .kraken_ai_driven_v2_regime_gated_selective_hypothesis import (
        DIRECTION_ORDER,
        FOLD_PLAN,
        VARIANT_SPECS,
    )
    from .kraken_ai_driven_v2_learning_core import ASSET_ORDER


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-v2-regime-gated-selective-development-result-review-v1"
)
COMPONENT_ID = "kraken-ai-v2-regime-gated-selective-development-result-review-v1"
EXECUTION_COMMIT = "40d98117613d3f4a74e809f76dcd371804b3fc31"
EXPECTED_REPORT_SHA256 = (
    "a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286"
)
EXPECTED_PREDICTION_SHA256 = (
    "728b60750ed9de5070281d8d3cebecddbef701f2f6ea604dbeec7c2ea7015400"
)
EXPECTED_CONTEXT_MANIFEST_SHA256 = (
    "db4dde045d9fce22bee1389fe8c7ad13d3e3ccc5e5c4ace7c433f5461ba11916"
)
EXPECTED_ARCHIVE_SHA256 = (
    "e6ab4a3d2fe3be99167607fa28f230a84a038ad3ea3348ef81dc4bffcabb758d"
)
ATTEMPT_1_RESULT_DOCUMENT_SHA256 = (
    "d9f1ac12d56571752dc78f13dc0157df3df7023be37e07448e75e0f700c87794"
)
RUNNER_PROTOCOL_SHA256 = (
    "dd1df5ebef5d4e2d73bc4e358307164f270ab83045b18a7aa6264e90289396df"
)
RUNNER_COMPONENT_SHA256 = (
    "d60506b7d753fbc7efc329c77db0327c655ff4002ecefb9f2798ad4bb2c6f732"
)
RUNNER_REVIEW_SHA256 = (
    "d35b55367e8687b6b54eef46e8e45fedcf05d70c2f4e3ceb9a045cbd9b5d6da5"
)
EXPECTED_LABELED_DECISION_COUNT = 3793
EXPECTED_PREDICTION_COUNT = 291
EXPECTED_BASE_MODEL_COUNT = 2
EXPECTED_CALIBRATOR_COUNT = 2
EXPECTED_SUPPORTED_CELLS = (
    "SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL|FOLD_1|SHORT",
    "SPOT_REGIME_CALIBRATED_LOGISTIC_CONTROL|FOLD_2|SHORT",
)
EXPECTED_SUPPORTED_CELL_RESULTS = {
    EXPECTED_SUPPORTED_CELLS[0]: {
        "row_count": 134,
        "positive_count": 11,
        "calibrated_brier_score": 0.07926634506436285,
        "prevalence_brier_score": 0.1067632773354219,
        "required_probability": 0.31250945260407764,
        "maximum_probability": 0.16413038189020743,
    },
    EXPECTED_SUPPORTED_CELLS[1]: {
        "row_count": 157,
        "positive_count": 1,
        "calibrated_brier_score": 0.013519253157928663,
        "prevalence_brier_score": 0.04636816078053185,
        "required_probability": 0.32803316317218534,
        "maximum_probability": 0.2116228886276886,
    },
}
STATUS = "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_TERMINAL_RESULT_REVIEW_PASS"
STATIC_STATUS = (
    "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_TERMINAL_RESULT_REVIEW_"
    "REVIEWED_EXTERNAL_EVIDENCE_REQUIRED"
)

PREDICTION_COLUMNS = {
    "action",
    "asset",
    "context_confirmed",
    "decision_timestamp",
    "direction",
    "entry_timestamp",
    "event_end_timestamp",
    "fold_id",
    "label",
    "outcome_net_r",
    "positive_outcome",
    "positive_probability",
    "regime",
    "required_probability",
    "variant_id",
}
IDENTITY_COLUMNS = (
    "fold_id",
    "asset",
    "decision_timestamp",
    "entry_timestamp",
    "event_end_timestamp",
    "direction",
    "label",
    "outcome_net_r",
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _finite_float(value, name):
    if isinstance(value, bool):
        raise RuntimeError(f"{name} must be a finite number.")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise RuntimeError(f"{name} must be a finite number.")
    return parsed


def _utc(value, name):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise RuntimeError(f"{name} is not ISO-8601.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"{name} must be timezone-aware.")
    return parsed


def _assert_empty_selection(summary, name):
    if (
        summary.get("count") != 0
        or _finite_float(summary.get("cumulative_net_r"), name) != 0.0
        or summary.get("mean_net_r") is not None
        or summary.get("median_net_r") is not None
        or summary.get("positive_outcome_count") != 0
        or summary.get("direction_counts")
        != {direction: 0 for direction in DIRECTION_ORDER}
    ):
        raise RuntimeError(f"{name} must remain an empty HOLD_CASH selection.")


def _validate_terminal_report(report):
    required = {
        "protocol_id": (
            "kraken-btc-eth-xrp-ai-v2-regime-gated-selective-development-runner-v1"
        ),
        "run_id": RUN_ID,
        "learning_status": STATUS_HOLD,
        "terminal_failure_status": STATUS_HOLD,
        "action": "HOLD_CASH",
        "partition": "DEVELOPMENT",
        "resolution": "12h",
        "common_start_utc": "2021-12-01T00:00:00Z",
        "common_end_exclusive_utc": "2024-04-01T00:00:00Z",
        "labeled_decision_count": EXPECTED_LABELED_DECISION_COUNT,
        "trained_base_model_count": EXPECTED_BASE_MODEL_COUNT,
        "trained_calibrator_count": EXPECTED_CALIBRATOR_COUNT,
        "trained_artifact_count": (
            EXPECTED_BASE_MODEL_COUNT + EXPECTED_CALIBRATOR_COUNT
        ),
        "out_of_fold_prediction_count": EXPECTED_PREDICTION_COUNT,
    }
    for field, expected in required.items():
        if report.get(field) != expected:
            raise RuntimeError(f"Terminal report mismatch: {field}.")
    if report.get("passing_development_hypotheses") != []:
        raise RuntimeError("Terminal report cannot contain a passing hypothesis.")
    if report.get("variant_order") != list(VARIANT_SPECS):
        raise RuntimeError("Terminal report variant order mismatch.")
    if report.get("direction_order") != list(DIRECTION_ORDER):
        raise RuntimeError("Terminal report direction order mismatch.")
    if report.get("source_archive") != {
        "filename": "Kraken_OHLCVT.zip",
        "bytes": 7885068519,
        "sha256": EXPECTED_ARCHIVE_SHA256,
    }:
        raise RuntimeError("Terminal report archive binding mismatch.")
    if (
        report.get("context_dataset_manifest_sha256")
        != EXPECTED_CONTEXT_MANIFEST_SHA256
        or report.get("context_dataset_object_count") != 2808
        or report.get("context_dataset_recovery_attempt") != 4
    ):
        raise RuntimeError("Terminal report context-lock binding mismatch.")

    diagnostics = report.get("label_diagnostics", {})
    if diagnostics.get("regime_counts") != {
        "LONG_REGIME": 933,
        "NEUTRAL": 1660,
        "SHORT_REGIME": 1200,
    } or diagnostics.get("context_confirmed_counts") != {"LONG": 201, "SHORT": 237}:
        raise RuntimeError("Terminal report regime diagnostics mismatch.")

    required_true = (
        "source_archive_opened",
        "context_dataset_opened",
        "development_data_opened",
        "labels_generated",
        "model_training_authorized",
        "model_training_executed",
    )
    if any(report.get(field) is not True for field in required_true):
        raise RuntimeError("Terminal report execution boundary mismatch.")
    required_false = (
        "feature_search_executed",
        "hyperparameter_sweep_executed",
        "threshold_sweep_executed",
        "automatic_model_selection",
        "automatic_successor_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    if any(report.get(field) is not False for field in required_false):
        raise RuntimeError("Terminal report safety boundary mismatch.")

    reviews = report.get("variant_reviews", [])
    if [item.get("variant_id") for item in reviews] != list(VARIANT_SPECS):
        raise RuntimeError("Terminal variant-review registry mismatch.")
    supported_cells = []
    unsupported_count = 0
    review_by_variant = {}
    for review in reviews:
        variant_id = review["variant_id"]
        review_by_variant[variant_id] = review
        gates = review.get("absolute_gates", {})
        expected_false_gates = (
            "all_fold_raw_support_pass",
            "all_fold_nonoverlap_support_pass",
            "all_fold_positive_net_r_pass",
            "all_direction_fold_brier_skill_pass",
            "asset_breadth_pass",
            "overall_positive_net_r_pass",
        )
        if (
            any(gates.get(field) is not False for field in expected_false_gates)
            or gates.get("positive_asset_count") != 0
            or review.get("absolute_gates_passed") is not False
            or review.get("development_viable") is not False
        ):
            raise RuntimeError(f"Terminal gate mismatch: {variant_id}.")
        _assert_empty_selection(
            review.get("raw_selected_overall", {}), f"{variant_id} raw overall"
        )
        _assert_empty_selection(
            review.get("nonoverlapping_selected_overall", {}),
            f"{variant_id} nonoverlapping overall",
        )
        if [item.get("asset") for item in review.get("assets", [])] != list(
            ASSET_ORDER
        ):
            raise RuntimeError(f"Terminal asset registry mismatch: {variant_id}.")
        for asset in review["assets"]:
            _assert_empty_selection(
                asset.get("nonoverlapping_selected", {}),
                f"{variant_id} {asset['asset']}",
            )
            if asset.get("positive_net_r_pass") is not False:
                raise RuntimeError(f"Terminal asset gate mismatch: {variant_id}.")
        folds = review.get("folds", [])
        if [item.get("fold_id") for item in folds] != [
            item["fold_id"] for item in FOLD_PLAN
        ]:
            raise RuntimeError(f"Terminal fold registry mismatch: {variant_id}.")
        for fold in folds:
            fold_id = fold["fold_id"]
            for name in ("raw_selected", "nonoverlapping_selected"):
                _assert_empty_selection(
                    fold.get(name, {}), f"{variant_id} {fold_id} {name}"
                )
            for field in (
                "raw_support_pass",
                "nonoverlap_support_pass",
                "positive_net_r_pass",
                "all_direction_brier_skill_pass",
            ):
                if fold.get(field) is not False:
                    raise RuntimeError(
                        f"Terminal fold gate mismatch: {variant_id} {fold_id}."
                    )
            support = fold.get("direction_support", {})
            if set(support) != set(DIRECTION_ORDER):
                raise RuntimeError(
                    f"Terminal direction registry mismatch: {variant_id} {fold_id}."
                )
            for direction, metrics in support.items():
                cell = f"{variant_id}|{fold_id}|{direction}"
                if metrics.get("supported") is True:
                    supported_cells.append(cell)
                    calibrated = _finite_float(
                        metrics.get("calibrated_brier_score"), f"{cell} Brier"
                    )
                    prevalence = _finite_float(
                        metrics.get("prevalence_brier_score"),
                        f"{cell} prevalence Brier",
                    )
                    if metrics.get("brier_skill_pass") is not (calibrated < prevalence):
                        raise RuntimeError(f"Terminal Brier gate mismatch: {cell}.")
                else:
                    unsupported_count += 1
                    if (
                        metrics.get("supported") is not False
                        or not metrics.get("support_failure")
                        or metrics.get("brier_skill_pass") is not False
                    ):
                        raise RuntimeError(f"Terminal support failure mismatch: {cell}.")

    if tuple(supported_cells) != EXPECTED_SUPPORTED_CELLS or unsupported_count != 10:
        raise RuntimeError("Terminal supported-cell registry mismatch.")
    control, context = reviews
    if control.get("incremental_gates") is not None:
        raise RuntimeError("Control cannot have incremental gates.")
    incremental = context.get("incremental_gates", {})
    for field in (
        "higher_overall_mean_net_r_pass",
        "higher_worst_fold_mean_net_r_pass",
        "fold_mean_wins_pass",
        "all_incremental_gates_passed",
    ):
        if incremental.get(field) is not False:
            raise RuntimeError("Terminal incremental-gate mismatch.")
    if incremental.get("fold_mean_win_count") != 0:
        raise RuntimeError("Terminal context fold-win count mismatch.")

    expected_artifact_ids = {
        f"{cell}|{kind}"
        for cell in EXPECTED_SUPPORTED_CELLS
        for kind in ("BASE", "CALIBRATOR")
    }
    if {item.get("artifact_id") for item in report.get("model_artifacts", [])} != (
        expected_artifact_ids
    ):
        raise RuntimeError("Terminal model-artifact registry mismatch.")
    prediction = report.get("prediction_artifact", {})
    if (
        prediction.get("path") != PREDICTIONS_FILENAME
        or prediction.get("checksum_path") != PREDICTIONS_SHA256_FILENAME
        or prediction.get("sha256") != EXPECTED_PREDICTION_SHA256
    ):
        raise RuntimeError("Terminal prediction-artifact binding mismatch.")
    return review_by_variant


def _validate_predictions(report, rows, review_by_variant):
    if not isinstance(rows, list) or len(rows) != EXPECTED_PREDICTION_COUNT:
        raise RuntimeError("Terminal prediction count mismatch.")
    if rows != sorted(
        rows,
        key=lambda row: (
            row["variant_id"],
            row["fold_id"],
            row["decision_timestamp"],
            row["asset"],
            row["direction"],
        ),
    ):
        raise RuntimeError("Terminal prediction ordering mismatch.")
    fold_registry = {item["fold_id"]: item for item in FOLD_PLAN}
    grouped = defaultdict(list)
    identities = set()
    for number, row in enumerate(rows, start=1):
        if set(row) != PREDICTION_COLUMNS:
            raise RuntimeError(f"Terminal prediction schema mismatch at row {number}.")
        cell = f"{row['variant_id']}|{row['fold_id']}|{row['direction']}"
        if cell not in EXPECTED_SUPPORTED_CELLS:
            raise RuntimeError(f"Unexpected terminal prediction cell: {cell}.")
        if row["asset"] not in ASSET_ORDER or row["regime"] != "SHORT_REGIME":
            raise RuntimeError(f"Terminal prediction identity mismatch at row {number}.")
        if type(row["context_confirmed"]) is not bool or type(
            row["positive_outcome"]
        ) is not bool:
            raise RuntimeError(f"Terminal boolean mismatch at row {number}.")
        decision = _utc(row["decision_timestamp"], "decision_timestamp")
        entry = _utc(row["entry_timestamp"], "entry_timestamp")
        event_end = _utc(row["event_end_timestamp"], "event_end_timestamp")
        fold = fold_registry[row["fold_id"]]
        if (
            not _utc(fold["validation_start_utc"], "validation_start")
            <= decision
            < _utc(fold["validation_end_exclusive_utc"], "validation_end")
            or decision >= entry
            or entry > event_end
        ):
            raise RuntimeError(f"Terminal prediction chronology mismatch at row {number}.")
        outcome = _finite_float(row["outcome_net_r"], "outcome_net_r")
        probability = _finite_float(
            row["positive_probability"], "positive_probability"
        )
        required = _finite_float(row["required_probability"], "required_probability")
        if not 0.0 <= probability <= 1.0 or not 0.0 <= required <= 1.0:
            raise RuntimeError(f"Terminal probability range mismatch at row {number}.")
        if row["positive_outcome"] is not (outcome > 0.0):
            raise RuntimeError(f"Terminal outcome polarity mismatch at row {number}.")
        expected_action = row["direction"] if probability > required else "HOLD_CASH"
        if row["action"] != expected_action:
            raise RuntimeError(f"Terminal threshold-action mismatch at row {number}.")
        identity = tuple(row[column] for column in IDENTITY_COLUMNS)
        if identity in identities:
            raise RuntimeError(f"Duplicate terminal prediction at row {number}.")
        identities.add(identity)
        grouped[cell].append(row)

    if set(grouped) != set(EXPECTED_SUPPORTED_CELLS):
        raise RuntimeError("Terminal prediction-cell coverage mismatch.")
    cell_diagnostics = {}
    for cell in EXPECTED_SUPPORTED_CELLS:
        variant_id, fold_id, direction = cell.split("|")
        cell_rows = grouped[cell]
        fold_review = next(
            item
            for item in review_by_variant[variant_id]["folds"]
            if item["fold_id"] == fold_id
        )
        metrics = fold_review["direction_support"][direction]
        probabilities = [float(row["positive_probability"]) for row in cell_rows]
        actual = [1.0 if row["positive_outcome"] else 0.0 for row in cell_rows]
        required_values = {float(row["required_probability"]) for row in cell_rows}
        if len(required_values) != 1:
            raise RuntimeError(f"Terminal threshold drift: {cell}.")
        required = required_values.pop()
        calibrated_brier = sum(
            (observed - probability) ** 2
            for observed, probability in zip(actual, probabilities, strict=True)
        ) / len(cell_rows)
        prevalence = _finite_float(
            metrics["outer_training_positive_prevalence"], f"{cell} prevalence"
        )
        prevalence_brier = sum(
            (observed - prevalence) ** 2 for observed in actual
        ) / len(cell_rows)
        checks = (
            len(cell_rows) == metrics["outer_validation_rows"],
            math.isclose(required, metrics["required_positive_probability"], abs_tol=1e-12),
            math.isclose(
                calibrated_brier, metrics["calibrated_brier_score"], abs_tol=1e-12
            ),
            math.isclose(
                prevalence_brier, metrics["prevalence_brier_score"], abs_tol=1e-12
            ),
        )
        if not all(checks):
            raise RuntimeError(f"Terminal prediction metric mismatch: {cell}.")
        cell_diagnostics[cell] = {
            "row_count": len(cell_rows),
            "positive_count": int(sum(actual)),
            "calibrated_brier_score": calibrated_brier,
            "prevalence_brier_score": prevalence_brier,
            "required_probability": required,
            "maximum_probability": max(probabilities),
            "selected_count": sum(row["action"] != "HOLD_CASH" for row in cell_rows),
        }

    for variant_id, review in review_by_variant.items():
        identities = [
            {column: row[column] for column in IDENTITY_COLUMNS}
            for row in rows
            if row["variant_id"] == variant_id
        ]
        digest = hashlib.sha256(canonical_json_bytes(identities)).hexdigest()
        if digest != review.get("prediction_row_identity_sha256"):
            raise RuntimeError(f"Terminal prediction identity hash mismatch: {variant_id}.")
    if any(item["selected_count"] for item in cell_diagnostics.values()):
        raise RuntimeError("Terminal result must contain zero selected predictions.")
    return cell_diagnostics


def analyze_terminal_result(report, predictions):
    review_by_variant = _validate_terminal_report(report)
    cell_diagnostics = _validate_predictions(report, predictions, review_by_variant)
    return {
        "terminal_status_validated": True,
        "threshold_actions_reconstructed": True,
        "brier_scores_recomputed": True,
        "supported_direction_fold_count": len(cell_diagnostics),
        "unsupported_direction_fold_count": 10,
        "selected_prediction_count": 0,
        "passing_development_hypotheses": [],
        "cell_diagnostics": cell_diagnostics,
        "terminal_kraken_12h_research_stop": True,
    }


def _inventory(root):
    return {
        path.relative_to(root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def read_regime_gated_selective_terminal_result(evidence_directory):
    root = Path(evidence_directory).resolve()
    before = _inventory(root)
    locked = read_regime_gated_selective_evidence(root)
    if locked["report_sha256"] != EXPECTED_REPORT_SHA256:
        raise RuntimeError("Regime-gated terminal report identity mismatch.")
    report_bytes = (root / REPORT_FILENAME).read_bytes()
    prediction_bytes = (root / PREDICTIONS_FILENAME).read_bytes()
    if hashlib.sha256(report_bytes).hexdigest() != EXPECTED_REPORT_SHA256:
        raise RuntimeError("Regime-gated terminal report hash mismatch.")
    if hashlib.sha256(prediction_bytes).hexdigest() != EXPECTED_PREDICTION_SHA256:
        raise RuntimeError("Regime-gated terminal prediction hash mismatch.")
    report = json.loads(report_bytes)
    predictions = json.loads(prediction_bytes)
    if canonical_json_bytes(report) != report_bytes:
        raise RuntimeError("Regime-gated terminal report is not canonical.")
    if canonical_json_bytes(predictions) != prediction_bytes:
        raise RuntimeError("Regime-gated terminal predictions are not canonical.")
    analysis = analyze_terminal_result(report, predictions)
    expected_paths = {
        REPORT_FILENAME,
        REPORT_SHA256_FILENAME,
        PREDICTIONS_FILENAME,
        PREDICTIONS_SHA256_FILENAME,
        *(item["path"] for item in report["model_artifacts"]),
    }
    if set(before) != expected_paths:
        raise RuntimeError("Regime-gated terminal evidence file registry mismatch.")
    after = _inventory(root)
    if before != after:
        raise RuntimeError("Regime-gated terminal review changed evidence bytes.")
    for cell, expected in EXPECTED_SUPPORTED_CELL_RESULTS.items():
        observed = analysis["cell_diagnostics"].get(cell, {})
        for field, expected_value in expected.items():
            observed_value = observed.get(field)
            if isinstance(expected_value, float):
                matches = math.isclose(
                    float(observed_value), expected_value, rel_tol=0.0, abs_tol=1e-12
                )
            else:
                matches = observed_value == expected_value
            if not matches:
                raise RuntimeError(f"Frozen terminal diagnostic mismatch: {cell} {field}.")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "execution_commit": EXECUTION_COMMIT,
        "status": STATUS,
        "learning_status": locked["learning_status"],
        "action": locked["action"],
        "report_sha256": locked["report_sha256"],
        "prediction_sha256": EXPECTED_PREDICTION_SHA256,
        "labeled_decision_count": report["labeled_decision_count"],
        "out_of_fold_prediction_count": locked["out_of_fold_prediction_count"],
        "trained_base_model_count": locked["trained_base_model_count"],
        "trained_calibrator_count": locked["trained_calibrator_count"],
        "trained_artifact_count": locked["trained_artifact_count"],
        **analysis,
        "evidence_file_count": len(before),
        "evidence_unchanged": True,
        "model_artifacts_unpickled": False,
        "labels_generated_by_review": False,
        "model_training_executed_by_review": False,
        "retry_authorized": False,
        "threshold_rescue_authorized": False,
        "automatic_successor_authorized": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": "FREEZE_TERMINAL_KRAKEN_12H_RESULT",
    }


def result_review_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "execution_commit": EXECUTION_COMMIT,
        "expected_report_sha256": EXPECTED_REPORT_SHA256,
        "expected_prediction_sha256": EXPECTED_PREDICTION_SHA256,
        "expected_labeled_decision_count": EXPECTED_LABELED_DECISION_COUNT,
        "expected_prediction_count": EXPECTED_PREDICTION_COUNT,
        "expected_base_model_count": EXPECTED_BASE_MODEL_COUNT,
        "expected_calibrator_count": EXPECTED_CALIBRATOR_COUNT,
        "expected_supported_cells": list(EXPECTED_SUPPORTED_CELLS),
        "terminal_status": STATUS_HOLD,
        "terminal_action": "HOLD_CASH",
        "external_evidence_opened": False,
        "model_artifacts_unpickled": False,
        "labels_generated": False,
        "model_training_executed": False,
        "retry_authorized": False,
        "threshold_rescue_authorized": False,
        "automatic_successor_authorized": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": STATIC_STATUS,
        "next_stage": "RUN_READ_ONLY_TERMINAL_RESULT_REVIEW",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Review the terminal regime-gated selective Development result."
    )
    parser.add_argument("--declaration-only", action="store_true")
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args(argv)
    if args.declaration_only:
        result = result_review_declaration()
    elif args.evidence:
        result = read_regime_gated_selective_terminal_result(args.evidence)
    else:
        parser.error("Use --declaration-only or --evidence.")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
