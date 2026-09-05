"""Read-only score forensics for derivatives-context Development Attempt 1."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from kraken_ai_driven_v2_derivatives_context_development_learning_runner import (
        MATCHED_CONTROL,
        PREDICTIONS_FILENAME,
        REPORT_FILENAME,
        STATUS_HOLD,
        VARIANT_SPECS,
        canonical_json_bytes,
        read_context_learning_evidence,
    )
    from kraken_ai_driven_v2_derivatives_context_hypothesis import (
        ASSET_ORDER,
        FOLD_PLAN,
    )
    from kraken_ai_driven_v2_learning_core import CLASS_ORDER
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_derivatives_context_development_learning_runner import (
        MATCHED_CONTROL,
        PREDICTIONS_FILENAME,
        REPORT_FILENAME,
        STATUS_HOLD,
        VARIANT_SPECS,
        canonical_json_bytes,
        read_context_learning_evidence,
    )
    from .kraken_ai_driven_v2_derivatives_context_hypothesis import (
        ASSET_ORDER,
        FOLD_PLAN,
    )
    from .kraken_ai_driven_v2_learning_core import CLASS_ORDER


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-v2-context-score-forensic-review-v1"
COMPONENT_ID = "kraken-ai-v2-context-score-forensic-review-v1"
PARENT_COMMIT = "4e3867dfadc9795ca39e24ebafc7f405d40f3c8d"
EXPECTED_REPORT_SHA256 = (
    "bddb6f7c0a9b056dcf8a4ca79fc3b8128dbf4ded4aac47e19022a84222215fb4"
)
ATTEMPT_1_RESULT_DOCUMENT_SHA256 = (
    "16c357ecde8104dfd8aee920219b56b3748e9cb522e100ec122f568720e16f4a"
)
RUNNER_PROTOCOL_SHA256 = (
    "91dc2ca8e9348e7eae9c0a056b750894418d945a10f6257d80f453f863711de3"
)
RUNNER_COMPONENT_SHA256 = (
    "e31d4062cd714fcf067ed308ac12428a8ec4db20c6ce6015c83d404aa5b59108"
)
EXPECTED_LABELED_ROW_COUNT = 3793
EXPECTED_PREDICTION_COUNT = 8468
EXPECTED_MODEL_COUNT = 12
QUANTILES = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
STATUS = "KRAKEN_AI_V2_CONTEXT_SCORE_FORENSIC_REVIEW_PASS"
STATIC_STATUS = (
    "KRAKEN_AI_V2_CONTEXT_SCORE_FORENSIC_REVIEW_REVIEWED_EXTERNAL_EVIDENCE_REQUIRED"
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


def _spearman(left, right):
    left = pd.Series(left, dtype=float)
    right = pd.Series(right, dtype=float)
    if len(left) < 2 or left.nunique() < 2 or right.nunique() < 2:
        return None
    left = left.rank(method="average")
    right = right.rank(method="average")
    value = left.corr(right)
    return None if pd.isna(value) else float(value)


def _outcome_summary(frame):
    values = frame["outcome_net_r"].to_numpy(dtype=float)
    return {
        "count": int(len(frame)),
        "cumulative_net_r": float(values.sum()),
        "mean_net_r": float(values.mean()) if len(values) else None,
    }


def _nonoverlapping(frame):
    selected = []
    busy_until = {}
    ordered = frame.sort_values(
        ["decision_timestamp", "asset", "fold_id"], kind="stable"
    )
    for index, row in ordered.iterrows():
        asset = row["asset"]
        if asset not in busy_until or row["decision_timestamp"] >= busy_until[asset]:
            selected.append(index)
            busy_until[asset] = row["event_end_timestamp"]
    return frame.loc[selected].sort_values(
        ["decision_timestamp", "asset", "fold_id"], kind="stable"
    )


def _score_statistics(frame):
    values = frame["score"].to_numpy(dtype=float)
    return {
        "count": int(len(values)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "mean": float(values.mean()),
        "positive_count": int((values > 0.0).sum()),
        "positive_fraction": float((values > 0.0).mean()),
        "quantiles": {
            f"p{int(point * 100):02d}": float(np.quantile(values, point))
            for point in QUANTILES
        },
    }


def _relationship(frame):
    return {
        "count": int(len(frame)),
        "score_outcome_spearman": _spearman(frame["score"], frame["outcome_net_r"]),
    }


def _duration_summary(frame):
    duration = (
        frame["event_end_timestamp"] - frame["decision_timestamp"]
    ).dt.total_seconds() / 86400.0
    return {
        "count": int(len(duration)),
        "minimum_days": float(duration.min()),
        "median_days": float(duration.median()),
        "mean_days": float(duration.mean()),
        "maximum_days": float(duration.max()),
    }


def _decile_forensics(frame):
    ranked = frame.sort_values(
        ["score", "decision_timestamp", "asset", "fold_id"], kind="stable"
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
                "score_minimum": float(bucket["score"].min()),
                "score_maximum": float(bucket["score"].max()),
                "raw": _outcome_summary(bucket),
                "nonoverlapping": _outcome_summary(_nonoverlapping(bucket)),
            }
        )
    top = ranked.loc[ranked["score_decile"] == 10]
    by_fold = []
    for fold in FOLD_PLAN:
        fold_rows = top.loc[top["fold_id"] == fold["fold_id"]]
        by_fold.append(
            {
                "fold_id": fold["fold_id"],
                "raw": _outcome_summary(fold_rows),
                "nonoverlapping": _outcome_summary(_nonoverlapping(fold_rows)),
            }
        )
    means = [item["raw"]["mean_net_r"] for item in deciles]
    return {
        "assignment": "EQUAL_COUNT_STABLE_SCORE_ASCENDING",
        "deciles": deciles,
        "decile_mean_outcome_spearman": _spearman(range(1, 11), means),
        "top_decile": {
            "raw": _outcome_summary(top),
            "nonoverlapping": _outcome_summary(_nonoverlapping(top)),
            "by_fold": by_fold,
            "positive_nonoverlapping_mean_in_every_fold": all(
                item["nonoverlapping"]["mean_net_r"] is not None
                and item["nonoverlapping"]["mean_net_r"] > 0.0
                for item in by_fold
            ),
        },
    }


def _validate_predictions(predictions):
    required = {
        "variant_id",
        "fold_id",
        "asset",
        "decision_timestamp",
        "event_end_timestamp",
        "label",
        "outcome_net_r",
        "score",
        "eligible",
    }
    if not isinstance(predictions, list) or not predictions:
        raise RuntimeError("Score-forensic predictions must be a non-empty list.")
    if any(set(row) != required for row in predictions):
        raise RuntimeError("Score-forensic prediction schema mismatch.")
    frame = pd.DataFrame(predictions)
    for column in ("decision_timestamp", "event_end_timestamp"):
        try:
            frame[column] = pd.to_datetime(frame[column], utc=True)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Score-forensic timestamp mismatch.") from exc
    if (frame["event_end_timestamp"] < frame["decision_timestamp"]).any():
        raise RuntimeError("Score-forensic event chronology mismatch.")
    frame["score"] = [
        _finite_float(value, "Prediction score") for value in frame["score"]
    ]
    frame["outcome_net_r"] = [
        _finite_float(value, "Outcome net R") for value in frame["outcome_net_r"]
    ]
    if any(type(value) is not bool for value in frame["eligible"]):
        raise RuntimeError("Score-forensic eligibility type mismatch.")
    if any(frame["eligible"] != (frame["score"] > 0.0)):
        raise RuntimeError("Score-forensic eligibility rule mismatch.")
    if set(frame["variant_id"]) != set(VARIANT_SPECS):
        raise RuntimeError("Score-forensic variant registry mismatch.")
    if set(frame["fold_id"]) != {fold["fold_id"] for fold in FOLD_PLAN}:
        raise RuntimeError("Score-forensic fold registry mismatch.")
    if set(frame["asset"]) != set(ASSET_ORDER) or set(frame["label"]) != set(CLASS_ORDER):
        raise RuntimeError("Score-forensic asset or label registry mismatch.")
    identity = ["variant_id", "fold_id", "asset", "decision_timestamp"]
    if frame.duplicated(identity).any():
        raise RuntimeError("Score-forensic duplicate prediction identity.")
    return frame


def _assert_matched_rows(frame, context_id, control_id):
    columns = [
        "fold_id",
        "asset",
        "decision_timestamp",
        "event_end_timestamp",
        "label",
        "outcome_net_r",
    ]
    ordering = ["fold_id", "decision_timestamp", "asset"]
    context = frame.loc[frame["variant_id"] == context_id, columns].sort_values(
        ordering, kind="stable"
    ).reset_index(drop=True)
    control = frame.loc[frame["variant_id"] == control_id, columns].sort_values(
        ordering, kind="stable"
    ).reset_index(drop=True)
    if not context.equals(control):
        raise RuntimeError(f"Score-forensic matched row mismatch: {context_id}.")


def analyze_context_scores(report, predictions):
    frame = _validate_predictions(predictions)
    report_reviews = {
        item["variant_id"]: item for item in report.get("variant_reviews", [])
    }
    if set(report_reviews) != set(VARIANT_SPECS):
        raise RuntimeError("Score-forensic report variant review mismatch.")
    variants = []
    for variant_id in VARIANT_SPECS:
        subset = frame.loc[frame["variant_id"] == variant_id].copy()
        by_fold = []
        for fold in FOLD_PLAN:
            fold_rows = subset.loc[subset["fold_id"] == fold["fold_id"]]
            by_fold.append({"fold_id": fold["fold_id"], **_relationship(fold_rows)})
        by_asset = []
        for asset in ASSET_ORDER:
            asset_rows = subset.loc[subset["asset"] == asset]
            by_asset.append({"asset": asset, **_relationship(asset_rows)})
        class_support = []
        for fold in FOLD_PLAN:
            fold_rows = subset.loc[subset["fold_id"] == fold["fold_id"]]
            counts = {label: int((fold_rows["label"] == label).sum()) for label in CLASS_ORDER}
            class_support.append(
                {
                    "fold_id": fold["fold_id"],
                    "row_count": int(len(fold_rows)),
                    "label_counts": counts,
                    "label_fractions": {
                        label: float(counts[label] / len(fold_rows)) for label in CLASS_ORDER
                    },
                }
            )
        duration_by_label = [
            {
                "label": label,
                **_duration_summary(subset.loc[subset["label"] == label]),
            }
            for label in CLASS_ORDER
        ]
        variants.append(
            {
                "variant_id": variant_id,
                "objective": report_reviews[variant_id]["objective"],
                "development_viable": bool(report_reviews[variant_id]["development_viable"]),
                "score_statistics": _score_statistics(subset),
                "score_outcome_relationship": {
                    "overall": _relationship(subset),
                    "by_fold": by_fold,
                    "by_asset": by_asset,
                },
                "score_decile_forensics": _decile_forensics(subset),
                "class_support_by_fold": class_support,
                "event_duration": {
                    "overall": _duration_summary(subset),
                    "by_label": duration_by_label,
                },
            }
        )
    variant_registry = {item["variant_id"]: item for item in variants}
    pairs = []
    for context_id, control_id in MATCHED_CONTROL.items():
        _assert_matched_rows(frame, context_id, control_id)
        incremental = report_reviews[context_id].get("incremental_gates") or {}
        pairs.append(
            {
                "context_variant": context_id,
                "control_variant": control_id,
                "identical_prediction_rows": True,
                "predictive_fold_win_count": incremental.get("predictive_fold_win_count"),
                "context_score_outcome_spearman": variant_registry[context_id][
                    "score_outcome_relationship"
                ]["overall"]["score_outcome_spearman"],
                "control_score_outcome_spearman": variant_registry[control_id][
                    "score_outcome_relationship"
                ]["overall"]["score_outcome_spearman"],
                "context_top_decile": variant_registry[context_id][
                    "score_decile_forensics"
                ]["top_decile"],
                "control_top_decile": variant_registry[control_id][
                    "score_decile_forensics"
                ]["top_decile"],
            }
        )
    return {
        "variant_forensics": variants,
        "matched_pair_forensics": pairs,
        "cost_decomposition_available": False,
        "cost_decomposition_limitation": (
            "Prediction evidence contains realized net R only; gross return, commission, "
            "spread and slippage are not separately attributable."
        ),
        "automatic_experiment_2_selection": False,
        "interpretation_boundary": "HUMAN_REVIEW_REQUIRED",
    }


def read_context_score_forensics(evidence_directory):
    root = Path(evidence_directory).resolve()
    before = {
        path.relative_to(root).as_posix(): (path.stat().st_size, _sha256(path))
        for path in root.rglob("*")
        if path.is_file()
    }
    independent = read_context_learning_evidence(root)
    if independent["report_sha256"] != EXPECTED_REPORT_SHA256:
        raise RuntimeError("Score-forensic Attempt 1 report SHA-256 mismatch.")
    if independent["learning_status"] != STATUS_HOLD:
        raise RuntimeError("Score-forensic Attempt 1 learning status mismatch.")
    if independent["trained_model_count"] != EXPECTED_MODEL_COUNT:
        raise RuntimeError("Score-forensic model count mismatch.")
    report_bytes = (root / REPORT_FILENAME).read_bytes()
    prediction_bytes = (root / PREDICTIONS_FILENAME).read_bytes()
    report = json.loads(report_bytes)
    predictions = json.loads(prediction_bytes)
    if canonical_json_bytes(report) != report_bytes or canonical_json_bytes(predictions) != prediction_bytes:
        raise RuntimeError("Score-forensic input JSON is not canonical.")
    if report.get("labeled_row_count") != EXPECTED_LABELED_ROW_COUNT:
        raise RuntimeError("Score-forensic labeled-row count mismatch.")
    if report.get("out_of_fold_prediction_count") != EXPECTED_PREDICTION_COUNT:
        raise RuntimeError("Score-forensic report prediction count mismatch.")
    if len(predictions) != EXPECTED_PREDICTION_COUNT:
        raise RuntimeError("Score-forensic prediction artifact count mismatch.")
    analysis = analyze_context_scores(report, predictions)
    after = {
        path.relative_to(root).as_posix(): (path.stat().st_size, _sha256(path))
        for path in root.rglob("*")
        if path.is_file()
    }
    if after != before:
        raise RuntimeError("Score-forensic evidence changed during read-only review.")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "status": STATUS,
        "learning_report_sha256": EXPECTED_REPORT_SHA256,
        "learning_status": independent["learning_status"],
        "labeled_row_count": EXPECTED_LABELED_ROW_COUNT,
        "out_of_fold_prediction_count": EXPECTED_PREDICTION_COUNT,
        "trained_model_count": EXPECTED_MODEL_COUNT,
        **analysis,
        "evidence_modified": False,
        "model_artifacts_unpickled": False,
        "model_training_executed": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "real_orders_submitted": False,
        "next_stage": "HUMAN_REVIEW_SCORE_FORENSICS_BEFORE_EXPERIMENT_2",
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
        "variant_order": list(VARIANT_SPECS),
        "matched_control": MATCHED_CONTROL,
        "fixed_quantiles": list(QUANTILES),
        "fixed_decile_count": 10,
        "read_only_forensics_implemented": True,
        "matched_row_validation_implemented": True,
        "nonoverlapping_decile_economics_implemented": True,
        "cost_decomposition_available": False,
        "external_evidence_opened": False,
        "model_artifacts_unpickled": False,
        "labels_generated": False,
        "model_training_executed": False,
        "threshold_sweep_authorized": False,
        "automatic_experiment_2_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": "KRAKEN_AI_V2_CONTEXT_SCORE_FORENSIC_REVIEW_IMPLEMENTED_EXTERNAL_EVIDENCE_REQUIRED",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only context score forensics.")
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--declare", action="store_true")
    args = parser.parse_args(argv)
    if args.declare == (args.evidence is not None):
        parser.error("Choose exactly one of --declare or --evidence.")
    result = forensic_declaration() if args.declare else read_context_score_forensics(args.evidence)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
