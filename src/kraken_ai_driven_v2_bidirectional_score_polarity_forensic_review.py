"""Read-only score and polarity forensics for bidirectional Attempt 1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from kraken_ai_driven_v2_bidirectional_development_learning_runner import (
        PREDICTIONS_FILENAME,
        REPORT_FILENAME,
        STATUS_HOLD,
        canonical_json_bytes,
        read_bidirectional_learning_evidence,
    )
    from kraken_ai_driven_v2_bidirectional_hypothesis import (
        DIRECTION_ORDER,
        FOLD_PLAN,
        MATCHED_CONTROL,
        VARIANT_SPECS,
        select_bidirectional_action,
    )
    from kraken_ai_driven_v2_learning_core import ASSET_ORDER, CLASS_ORDER
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_bidirectional_development_learning_runner import (
        PREDICTIONS_FILENAME,
        REPORT_FILENAME,
        STATUS_HOLD,
        canonical_json_bytes,
        read_bidirectional_learning_evidence,
    )
    from .kraken_ai_driven_v2_bidirectional_hypothesis import (
        DIRECTION_ORDER,
        FOLD_PLAN,
        MATCHED_CONTROL,
        VARIANT_SPECS,
        select_bidirectional_action,
    )
    from .kraken_ai_driven_v2_learning_core import ASSET_ORDER, CLASS_ORDER


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-v2-bidirectional-score-polarity-forensic-review-v1"
)
COMPONENT_ID = "kraken-ai-v2-bidirectional-score-polarity-forensic-review-v1"
PARENT_COMMIT = "ca1cd9186ecfac934d4ad84000da12c572d633a3"
EXPECTED_REPORT_SHA256 = (
    "7176ca3a005b7bdbfbdcbc2259fafd11c154ee45b0517eab26894e675aa26b3f"
)
ATTEMPT_1_RESULT_DOCUMENT_SHA256 = (
    "e394f0daf01b5262f3d1b2318c1e8d443ec59ac9e63561d13dd9d0e6b1951996"
)
RUNNER_PROTOCOL_SHA256 = (
    "b9e5d092c24dfc8952766de480dd6db8daf2c9f8e83b25cc6c326b4ed37d794e"
)
RUNNER_COMPONENT_SHA256 = (
    "6b37f6a1df2c40941202216179b38c25997ac16d3cf5fb261809c579222ea6c4"
)
RUNNER_REVIEW_SHA256 = (
    "e0ccd282d00faab3b09ca2607c77df1d9bb2c810c85c988d3071f778fbb70da3"
)
EXPECTED_LABELED_DECISION_COUNT = 3793
EXPECTED_DIRECTIONAL_LABEL_COUNT = 7586
EXPECTED_PREDICTION_COUNT = 4210
EXPECTED_MODEL_COUNT = 12
QUANTILES = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
STATUS = "KRAKEN_AI_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_PASS"
STATIC_STATUS = (
    "KRAKEN_AI_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_"
    "REVIEWED_EXTERNAL_EVIDENCE_REQUIRED"
)

PREDICTION_COLUMNS = (
    "variant_id",
    "fold_id",
    "asset",
    "decision_timestamp",
    "entry_timestamp",
    "long_event_end_timestamp",
    "short_event_end_timestamp",
    "long_label",
    "short_label",
    "long_outcome_net_r",
    "short_outcome_net_r",
    "long_predicted_net_r",
    "short_predicted_net_r",
    "action",
    "selected_outcome_net_r",
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _finite_float(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{name} must be a finite number.")
    return parsed


def _correlation(left, right, method):
    left = pd.Series(left, dtype=float)
    right = pd.Series(right, dtype=float)
    if len(left) < 2 or left.nunique() < 2 or right.nunique() < 2:
        return None
    if method == "spearman":
        left = left.rank(method="average")
        right = right.rank(method="average")
    value = left.corr(right)
    return None if pd.isna(value) else float(value)


def _numeric_distribution(values):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return {
            "count": 0,
            "minimum": None,
            "maximum": None,
            "mean": None,
            "median": None,
            "quantiles": {f"p{int(point * 100):02d}": None for point in QUANTILES},
        }
    return {
        "count": int(len(values)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "quantiles": {
            f"p{int(point * 100):02d}": float(np.quantile(values, point))
            for point in QUANTILES
        },
    }


def _outcome_summary(frame):
    values = frame["outcome_net_r"].to_numpy(dtype=float)
    count = int(len(values))
    actions = frame["direction"].value_counts() if "direction" in frame else pd.Series()
    return {
        "count": count,
        "direction_counts": {
            direction: int(actions.get(direction, 0)) for direction in DIRECTION_ORDER
        },
        "cumulative_net_r": float(values.sum()),
        "mean_net_r": float(values.mean()) if count else None,
        "median_net_r": float(np.median(values)) if count else None,
        "positive_outcome_count": int((values > 0.0).sum()),
        "positive_outcome_fraction": float((values > 0.0).mean()) if count else None,
    }


def _prediction_relationship(frame):
    predicted = frame["predicted_net_r"].to_numpy(dtype=float)
    outcome = frame["outcome_net_r"].to_numpy(dtype=float)
    error = predicted - outcome
    predicted_positive = predicted > 0.0
    outcome_positive = outcome > 0.0
    return {
        "count": int(len(frame)),
        "prediction": _numeric_distribution(predicted),
        "outcome": _outcome_summary(frame),
        "mean_prediction_bias": float(error.mean()),
        "mean_absolute_error": float(np.abs(error).mean()),
        "root_mean_squared_error": float(np.sqrt(np.mean(np.square(error)))),
        "pearson": _correlation(predicted, outcome, "pearson"),
        "spearman": _correlation(predicted, outcome, "spearman"),
        "positive_score_count": int(predicted_positive.sum()),
        "positive_score_fraction": float(predicted_positive.mean()),
        "true_positive_count": int((predicted_positive & outcome_positive).sum()),
        "false_positive_count": int((predicted_positive & ~outcome_positive).sum()),
        "missed_positive_count": int((~predicted_positive & outcome_positive).sum()),
        "nonpositive_correct_count": int((~predicted_positive & ~outcome_positive).sum()),
    }


def _decile_table(frame):
    ranked = frame.sort_values(
        ["predicted_net_r", "decision_timestamp", "asset", "fold_id"],
        kind="stable",
    ).copy()
    ranked["score_decile"] = (
        np.floor(np.arange(len(ranked)) * 10 / len(ranked)).astype(int) + 1
    )
    deciles = []
    for decile in range(1, 11):
        bucket = ranked.loc[ranked["score_decile"] == decile]
        deciles.append(
            {
                "decile": decile,
                "score": _numeric_distribution(bucket["predicted_net_r"]),
                "outcome": _outcome_summary(bucket),
            }
        )
    return deciles, ranked.loc[ranked["score_decile"] == 10]


def _decile_forensics(frame):
    deciles, top = _decile_table(frame)
    by_fold = []
    for fold in FOLD_PLAN:
        fold_rows = frame.loc[frame["fold_id"] == fold["fold_id"]]
        _, fold_top = _decile_table(fold_rows)
        by_fold.append(
            {
                "fold_id": fold["fold_id"],
                "top_decile": _outcome_summary(fold_top),
                "top_decile_score": _numeric_distribution(
                    fold_top["predicted_net_r"]
                ),
            }
        )
    decile_means = [item["outcome"]["mean_net_r"] for item in deciles]
    return {
        "assignment": "EQUAL_COUNT_STABLE_SCORE_ASCENDING",
        "deciles": deciles,
        "decile_mean_outcome_spearman": _correlation(
            range(1, 11), decile_means, "spearman"
        ),
        "top_decile": _outcome_summary(top),
        "top_decile_by_fold": by_fold,
        "positive_top_decile_fold_count": sum(
            item["top_decile"]["mean_net_r"] is not None
            and item["top_decile"]["mean_net_r"] > 0.0
            for item in by_fold
        ),
        "top_decile_positive_in_every_fold": all(
            item["top_decile"]["mean_net_r"] is not None
            and item["top_decile"]["mean_net_r"] > 0.0
            for item in by_fold
        ),
    }


def _direction_frame(frame, direction):
    prefix = direction.lower()
    result = frame[
        [
            "variant_id",
            "fold_id",
            "asset",
            "decision_timestamp",
            "entry_timestamp",
            f"{prefix}_event_end_timestamp",
            f"{prefix}_label",
            f"{prefix}_outcome_net_r",
            f"{prefix}_predicted_net_r",
        ]
    ].copy()
    result.columns = (
        "variant_id",
        "fold_id",
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "event_end_timestamp",
        "label",
        "outcome_net_r",
        "predicted_net_r",
    )
    result["direction"] = direction
    return result


def _direction_diagnostics(frame, direction):
    directional = _direction_frame(frame, direction)
    by_fold = [
        {
            "fold_id": fold["fold_id"],
            **_prediction_relationship(
                directional.loc[directional["fold_id"] == fold["fold_id"]]
            ),
        }
        for fold in FOLD_PLAN
    ]
    by_asset = [
        {
            "asset": asset,
            **_prediction_relationship(
                directional.loc[directional["asset"] == asset]
            ),
        }
        for asset in ASSET_ORDER
    ]
    label_support = []
    for label in CLASS_ORDER:
        label_rows = directional.loc[directional["label"] == label]
        label_support.append(
            {
                "label": label,
                "count": int(len(label_rows)),
                "prediction": _numeric_distribution(label_rows["predicted_net_r"]),
                "outcome": _outcome_summary(label_rows),
            }
        )
    return {
        "direction": direction,
        "overall": _prediction_relationship(directional),
        "by_fold": by_fold,
        "by_asset": by_asset,
        "score_decile_forensics": _decile_forensics(directional),
        "label_support": label_support,
    }


def _nonoverlapping(frame):
    selected = []
    busy_until = {}
    ordered = frame.sort_values(["decision_timestamp", "asset"], kind="stable")
    for index, row in ordered.iterrows():
        asset = row["asset"]
        if asset not in busy_until or row["decision_timestamp"] >= busy_until[asset]:
            selected.append(index)
            busy_until[asset] = row["event_end_timestamp"]
    return frame.loc[selected].sort_values(
        ["decision_timestamp", "asset"], kind="stable"
    )


def _selected_frame(frame):
    selected = frame.loc[frame["action"] != "HOLD_CASH"].copy()
    if selected.empty:
        selected["direction"] = pd.Series(dtype=str)
        selected["event_end_timestamp"] = pd.Series(dtype="datetime64[ns, UTC]")
        selected["outcome_net_r"] = pd.Series(dtype=float)
        selected["winning_score"] = pd.Series(dtype=float)
        selected["directional_margin"] = pd.Series(dtype=float)
        return selected
    is_long = selected["action"] == "LONG"
    selected["direction"] = selected["action"]
    selected["event_end_timestamp"] = selected["long_event_end_timestamp"].where(
        is_long, selected["short_event_end_timestamp"]
    )
    selected["outcome_net_r"] = selected["selected_outcome_net_r"]
    selected["winning_score"] = selected["long_predicted_net_r"].where(
        is_long, selected["short_predicted_net_r"]
    )
    selected["directional_margin"] = (
        selected["long_predicted_net_r"] - selected["short_predicted_net_r"]
    ).abs()
    return selected


def _action_diagnostics(frame):
    selected = _selected_frame(frame)
    nonoverlap = _nonoverlapping(selected)
    action_counts = frame["action"].value_counts()
    nonoverlap_count = len(nonoverlap)
    return {
        "decision_count": int(len(frame)),
        "action_counts": {
            action: int(action_counts.get(action, 0))
            for action in ("LONG", "SHORT", "HOLD_CASH")
        },
        "raw_selected": _outcome_summary(selected),
        "nonoverlapping_selected": _outcome_summary(nonoverlap),
        "nonoverlapping_long_fraction": (
            float((nonoverlap["direction"] == "LONG").mean())
            if nonoverlap_count
            else None
        ),
        "nonoverlapping_short_fraction": (
            float((nonoverlap["direction"] == "SHORT").mean())
            if nonoverlap_count
            else None
        ),
        "winning_score": _numeric_distribution(selected["winning_score"]),
        "directional_margin": _numeric_distribution(selected["directional_margin"]),
        "by_fold": [
            {
                "fold_id": fold["fold_id"],
                "raw": _outcome_summary(
                    selected.loc[selected["fold_id"] == fold["fold_id"]]
                ),
                "nonoverlapping": _outcome_summary(
                    nonoverlap.loc[nonoverlap["fold_id"] == fold["fold_id"]]
                ),
            }
            for fold in FOLD_PLAN
        ],
        "by_asset": [
            {
                "asset": asset,
                "raw": _outcome_summary(selected.loc[selected["asset"] == asset]),
                "nonoverlapping": _outcome_summary(
                    nonoverlap.loc[nonoverlap["asset"] == asset]
                ),
            }
            for asset in ASSET_ORDER
        ],
    }


def _validate_predictions(predictions):
    if not isinstance(predictions, list) or not predictions:
        raise RuntimeError("Bidirectional forensic predictions must be non-empty.")
    if any(set(row) != set(PREDICTION_COLUMNS) for row in predictions):
        raise RuntimeError("Bidirectional forensic prediction schema mismatch.")
    frame = pd.DataFrame(predictions, columns=PREDICTION_COLUMNS)
    timestamp_columns = (
        "decision_timestamp",
        "entry_timestamp",
        "long_event_end_timestamp",
        "short_event_end_timestamp",
    )
    for column in timestamp_columns:
        try:
            frame[column] = pd.to_datetime(frame[column], utc=True)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Bidirectional forensic timestamp mismatch.") from exc
    if (frame["entry_timestamp"] <= frame["decision_timestamp"]).any():
        raise RuntimeError("Bidirectional forensic entry chronology mismatch.")
    for direction in DIRECTION_ORDER:
        prefix = direction.lower()
        if (frame[f"{prefix}_event_end_timestamp"] < frame["entry_timestamp"]).any():
            raise RuntimeError("Bidirectional forensic outcome chronology mismatch.")
        if not set(frame[f"{prefix}_label"]).issubset(set(CLASS_ORDER)):
            raise RuntimeError("Bidirectional forensic label registry mismatch.")
        for column in (f"{prefix}_outcome_net_r", f"{prefix}_predicted_net_r"):
            frame[column] = [
                _finite_float(value, "Bidirectional forensic value")
                for value in frame[column]
            ]
        target = frame[f"{prefix}_label"] == "TARGET_3R_FIRST"
        stop = frame[f"{prefix}_label"] == "STOP_1R_FIRST"
        if (frame.loc[target, f"{prefix}_outcome_net_r"] <= 0.0).any():
            raise RuntimeError(f"{direction} target-label polarity mismatch.")
        if (frame.loc[stop, f"{prefix}_outcome_net_r"] >= 0.0).any():
            raise RuntimeError(f"{direction} stop-label polarity mismatch.")
    frame["selected_outcome_net_r"] = [
        _finite_float(value, "Selected outcome net R")
        for value in frame["selected_outcome_net_r"]
    ]
    if set(frame["variant_id"]) != set(VARIANT_SPECS):
        raise RuntimeError("Bidirectional forensic variant registry mismatch.")
    if set(frame["fold_id"]) != {fold["fold_id"] for fold in FOLD_PLAN}:
        raise RuntimeError("Bidirectional forensic fold registry mismatch.")
    if set(frame["asset"]) != set(ASSET_ORDER):
        raise RuntimeError("Bidirectional forensic asset registry mismatch.")
    identity = ["variant_id", "fold_id", "asset", "decision_timestamp"]
    if frame.duplicated(identity).any():
        raise RuntimeError("Bidirectional forensic duplicate prediction identity.")
    expected_actions = [
        select_bidirectional_action(long_score, short_score)
        for long_score, short_score in zip(
            frame["long_predicted_net_r"],
            frame["short_predicted_net_r"],
            strict=True,
        )
    ]
    if expected_actions != frame["action"].tolist():
        raise RuntimeError("Bidirectional forensic action-rule mismatch.")
    expected_outcomes = np.select(
        [frame["action"] == "LONG", frame["action"] == "SHORT"],
        [frame["long_outcome_net_r"], frame["short_outcome_net_r"]],
        default=0.0,
    ).astype(float)
    if not np.allclose(
        expected_outcomes,
        frame["selected_outcome_net_r"].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
    ):
        raise RuntimeError("Bidirectional forensic selected-outcome mismatch.")
    return frame


def _assert_matched_rows(frame, context_id, control_id):
    columns = (
        "fold_id",
        "asset",
        "decision_timestamp",
        "entry_timestamp",
        "long_event_end_timestamp",
        "short_event_end_timestamp",
        "long_label",
        "short_label",
        "long_outcome_net_r",
        "short_outcome_net_r",
    )
    ordering = ("fold_id", "decision_timestamp", "asset")
    context = frame.loc[frame["variant_id"] == context_id, columns].sort_values(
        list(ordering), kind="stable"
    ).reset_index(drop=True)
    control = frame.loc[frame["variant_id"] == control_id, columns].sort_values(
        list(ordering), kind="stable"
    ).reset_index(drop=True)
    if not context.equals(control):
        raise RuntimeError(f"Bidirectional forensic matched-row mismatch: {context_id}.")


def analyze_bidirectional_scores(report, predictions):
    frame = _validate_predictions(predictions)
    report_reviews = {
        item["variant_id"]: item for item in report.get("variant_reviews", [])
    }
    if set(report_reviews) != set(VARIANT_SPECS):
        raise RuntimeError("Bidirectional forensic report variant mismatch.")
    variants = []
    for variant_id in VARIANT_SPECS:
        subset = frame.loc[frame["variant_id"] == variant_id].copy()
        variants.append(
            {
                "variant_id": variant_id,
                "feature_set": report_reviews[variant_id]["feature_set"],
                "development_viable": bool(
                    report_reviews[variant_id]["development_viable"]
                ),
                "direction_forensics": [
                    _direction_diagnostics(subset, direction)
                    for direction in DIRECTION_ORDER
                ],
                "frozen_action_forensics": _action_diagnostics(subset),
            }
        )
    registry = {item["variant_id"]: item for item in variants}
    matched_pairs = []
    for context_id, control_id in MATCHED_CONTROL.items():
        _assert_matched_rows(frame, context_id, control_id)
        context_directions = {
            item["direction"]: item
            for item in registry[context_id]["direction_forensics"]
        }
        control_directions = {
            item["direction"]: item
            for item in registry[control_id]["direction_forensics"]
        }
        matched_pairs.append(
            {
                "context_variant": context_id,
                "control_variant": control_id,
                "identical_outcome_rows": True,
                "direction_comparison": [
                    {
                        "direction": direction,
                        "context_spearman": context_directions[direction]["overall"][
                            "spearman"
                        ],
                        "control_spearman": control_directions[direction]["overall"][
                            "spearman"
                        ],
                        "context_top_decile_mean_net_r": context_directions[direction][
                            "score_decile_forensics"
                        ]["top_decile"]["mean_net_r"],
                        "control_top_decile_mean_net_r": control_directions[direction][
                            "score_decile_forensics"
                        ]["top_decile"]["mean_net_r"],
                    }
                    for direction in DIRECTION_ORDER
                ],
            }
        )
    return {
        "action_rule_reconstructed": True,
        "action_rule_mismatch_count": 0,
        "label_polarity_validated": True,
        "matched_pair_forensics": matched_pairs,
        "variant_forensics": variants,
        "cost_decomposition_available": False,
        "cost_decomposition_limitation": (
            "OOF evidence contains net R only; gross return, commission, spread "
            "and slippage are not separately attributable."
        ),
        "retrospective_threshold_search_executed": False,
        "polarity_flip_simulated": False,
        "automatic_next_experiment_selection": False,
        "interpretation_boundary": "HUMAN_REVIEW_REQUIRED",
    }


def read_bidirectional_score_polarity_forensics(evidence_directory):
    root = Path(evidence_directory).resolve()
    before = {
        path.relative_to(root).as_posix(): (path.stat().st_size, _sha256(path))
        for path in root.rglob("*")
        if path.is_file()
    }
    independent = read_bidirectional_learning_evidence(root)
    if independent["report_sha256"] != EXPECTED_REPORT_SHA256:
        raise RuntimeError("Bidirectional forensic report SHA-256 mismatch.")
    if independent["learning_status"] != STATUS_HOLD:
        raise RuntimeError("Bidirectional forensic learning status mismatch.")
    if independent["trained_model_count"] != EXPECTED_MODEL_COUNT:
        raise RuntimeError("Bidirectional forensic model count mismatch.")
    report_bytes = (root / REPORT_FILENAME).read_bytes()
    prediction_bytes = (root / PREDICTIONS_FILENAME).read_bytes()
    report = json.loads(report_bytes)
    predictions = json.loads(prediction_bytes)
    if (
        canonical_json_bytes(report) != report_bytes
        or canonical_json_bytes(predictions) != prediction_bytes
    ):
        raise RuntimeError("Bidirectional forensic input JSON is not canonical.")
    if report.get("labeled_decision_count") != EXPECTED_LABELED_DECISION_COUNT:
        raise RuntimeError("Bidirectional forensic labeled-decision count mismatch.")
    if report.get("directional_label_count") != EXPECTED_DIRECTIONAL_LABEL_COUNT:
        raise RuntimeError("Bidirectional forensic directional-label count mismatch.")
    if report.get("out_of_fold_prediction_count") != EXPECTED_PREDICTION_COUNT:
        raise RuntimeError("Bidirectional forensic report prediction count mismatch.")
    if len(predictions) != EXPECTED_PREDICTION_COUNT:
        raise RuntimeError("Bidirectional forensic prediction artifact count mismatch.")
    analysis = analyze_bidirectional_scores(report, predictions)
    after = {
        path.relative_to(root).as_posix(): (path.stat().st_size, _sha256(path))
        for path in root.rglob("*")
        if path.is_file()
    }
    if after != before:
        raise RuntimeError("Bidirectional evidence changed during read-only forensics.")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "status": STATUS,
        "learning_report_sha256": EXPECTED_REPORT_SHA256,
        "learning_status": independent["learning_status"],
        "labeled_decision_count": EXPECTED_LABELED_DECISION_COUNT,
        "directional_label_count": EXPECTED_DIRECTIONAL_LABEL_COUNT,
        "out_of_fold_prediction_count": EXPECTED_PREDICTION_COUNT,
        "trained_model_count": EXPECTED_MODEL_COUNT,
        **analysis,
        "development_evidence_opened": True,
        "evidence_modified": False,
        "model_artifacts_unpickled": False,
        "labels_generated": False,
        "model_training_executed": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": (
            "HUMAN_REVIEW_BIDIRECTIONAL_SCORE_POLARITY_BEFORE_ANY_NEW_HYPOTHESIS"
        ),
    }


def forensic_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "expected_learning_report_sha256": EXPECTED_REPORT_SHA256,
        "attempt_1_result_document_sha256": ATTEMPT_1_RESULT_DOCUMENT_SHA256,
        "runner_protocol_sha256": RUNNER_PROTOCOL_SHA256,
        "runner_component_sha256": RUNNER_COMPONENT_SHA256,
        "runner_review_sha256": RUNNER_REVIEW_SHA256,
        "variant_order": list(VARIANT_SPECS),
        "direction_order": list(DIRECTION_ORDER),
        "matched_control": MATCHED_CONTROL,
        "fixed_quantiles": list(QUANTILES),
        "fixed_decile_count": 10,
        "action_reconstruction_implemented": True,
        "matched_row_validation_implemented": True,
        "label_polarity_validation_implemented": True,
        "direction_calibration_diagnostics_implemented": True,
        "fixed_score_deciles_implemented": True,
        "selected_policy_economics_implemented": True,
        "read_only_forensics_implemented": True,
        "cost_decomposition_available": False,
        "external_evidence_opened": False,
        "model_artifacts_unpickled": False,
        "labels_generated": False,
        "model_training_executed": False,
        "retrospective_threshold_search_authorized": False,
        "polarity_flip_authorized": False,
        "automatic_next_experiment_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": (
            "KRAKEN_AI_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_"
            "IMPLEMENTED_EXTERNAL_EVIDENCE_REQUIRED"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only bidirectional score and polarity forensics."
    )
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--declare", action="store_true")
    args = parser.parse_args(argv)
    if args.declare == (args.evidence is not None):
        parser.error("Choose exactly one of --declare or --evidence.")
    result = (
        forensic_declaration()
        if args.declare
        else read_bidirectional_score_polarity_forensics(args.evidence)
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
