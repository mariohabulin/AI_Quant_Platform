"""Read-only economic review of immutable 12h Development OOF evidence."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from statistics import median

from sklearn.metrics import average_precision_score

try:
    from kraken_ai_driven_v2_12h_development_learning_runner import (
        ASSET_ORDER,
        CLASS_ORDER,
        FOLD_PLAN,
        MODEL_SPECS,
        PREDICTIONS_FILENAME,
        REVIEW_REQUIRED_STATUS,
        KrakenAIDrivenV212hLearningEvidenceLock,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_12h_development_learning_runner import (
        ASSET_ORDER,
        CLASS_ORDER,
        FOLD_PLAN,
        MODEL_SPECS,
        PREDICTIONS_FILENAME,
        REVIEW_REQUIRED_STATUS,
        KrakenAIDrivenV212hLearningEvidenceLock,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-12h-development-economic-evidence-review-v1"
COMPONENT_ID = "kraken-ai-v2-12h-development-economic-evidence-review-v1"
PARENT_COMMIT = "9c1156e0527c34c71f9efec381f3770fdc7b4238"
EXPECTED_LEARNING_REPORT_SHA256 = (
    "30d020bd9c30306f3e8931b47c0958fea7e11a33bff3795c3473806ddcaa09cf"
)

MINIMUM_RAW_SELECTIONS_PER_FOLD = 30
MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD = 10
MINIMUM_POSITIVE_FOLDS = 3
MINIMUM_POSITIVE_ASSETS = 2

HOLD_CASH_STATUS = "KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_HOLD_CASH"
INTEREST_STATUS = (
    "KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_INTEREST_REVIEW_REQUIRED"
)

_PROBABILITY_FIELDS = (
    "p_target_3r_first",
    "p_stop_1r_first",
    "p_timeout_no_barrier",
)
_REQUIRED_FIELDS = (
    "fold_id",
    "model_id",
    "asset",
    "decision_timestamp",
    "event_end_timestamp",
    "training_end_timestamp",
    "actual_label",
    "actual_outcome_net_r",
    *_PROBABILITY_FIELDS,
)


def _timestamp(value, field):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RuntimeError(f"OOF {field} must be a UTC Z timestamp.")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise RuntimeError(f"OOF {field} is invalid.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise RuntimeError(f"OOF {field} must be UTC.")
    return parsed


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"OOF {field} must be numeric.")
    number = float(value)
    if not math.isfinite(number):
        raise RuntimeError(f"OOF {field} must be finite.")
    return number


def validate_prediction_records(records):
    if not isinstance(records, list) or not records:
        raise RuntimeError("Completed learning evidence requires OOF records.")
    expected_folds = {fold["fold_id"]: fold for fold in FOLD_PLAN}
    expected_models = set(MODEL_SPECS)
    expected_assets = set(ASSET_ORDER)
    observed_groups = set()
    observed_keys = set()
    validated = []

    for original in records:
        if not isinstance(original, dict) or any(field not in original for field in _REQUIRED_FIELDS):
            raise RuntimeError("OOF prediction record schema mismatch.")
        fold_id = original["fold_id"]
        model_id = original["model_id"]
        asset = original["asset"]
        if fold_id not in expected_folds or model_id not in expected_models or asset not in expected_assets:
            raise RuntimeError("OOF prediction identity mismatch.")
        if original["actual_label"] not in CLASS_ORDER:
            raise RuntimeError("OOF actual label mismatch.")

        decision = _timestamp(original["decision_timestamp"], "decision_timestamp")
        event_end = _timestamp(original["event_end_timestamp"], "event_end_timestamp")
        training_end = _timestamp(original["training_end_timestamp"], "training_end_timestamp")
        if event_end <= decision or training_end > decision:
            raise RuntimeError("OOF chronological boundary mismatch.")
        fold = expected_folds[fold_id]
        expected_training_end = _timestamp(
            fold["training_end_exclusive_utc"], "training_end_exclusive_utc"
        )
        validation_start = _timestamp(fold["validation_start_utc"], "validation_start_utc")
        validation_end = _timestamp(
            fold["validation_end_exclusive_utc"], "validation_end_exclusive_utc"
        )
        if training_end != expected_training_end or not (
            validation_start <= decision < validation_end and event_end < validation_end
        ):
            raise RuntimeError("OOF fold boundary mismatch.")

        probabilities = [
            _finite_number(original[field], field) for field in _PROBABILITY_FIELDS
        ]
        if any(value < 0.0 or value > 1.0 for value in probabilities):
            raise RuntimeError("OOF probability is outside [0, 1].")
        if not math.isclose(sum(probabilities), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise RuntimeError("OOF probabilities do not sum to one.")
        actual_r = _finite_number(original["actual_outcome_net_r"], "actual_outcome_net_r")

        key = (fold_id, model_id, asset, decision)
        if key in observed_keys:
            raise RuntimeError("OOF prediction key is duplicated.")
        observed_keys.add(key)
        observed_groups.add((fold_id, model_id, asset))
        record = dict(original)
        record["_decision"] = decision
        record["_event_end"] = event_end
        record["_actual_r"] = actual_r
        record["_predicted_net_r_floor"] = 3.0 * probabilities[0] - probabilities[1]
        validated.append(record)

    expected_groups = {
        (fold["fold_id"], model_id, asset)
        for fold in FOLD_PLAN
        for model_id in MODEL_SPECS
        for asset in ASSET_ORDER
    }
    if observed_groups != expected_groups:
        raise RuntimeError("OOF fold/model/asset coverage mismatch.")

    # The two model families must predict the identical OOF event set.
    event_sets = {}
    for model_id in MODEL_SPECS:
        event_sets[model_id] = {
            (row["fold_id"], row["asset"], row["decision_timestamp"], row["event_end_timestamp"], row["actual_label"], row["_actual_r"])
            for row in validated
            if row["model_id"] == model_id
        }
    first = event_sets[next(iter(MODEL_SPECS))]
    if any(events != first for events in event_sets.values()):
        raise RuntimeError("OOF model families do not share the same event set.")
    return validated


def _class_counts(rows):
    counts = Counter(row["actual_label"] for row in rows)
    return {label: int(counts.get(label, 0)) for label in CLASS_ORDER}


def _summary(rows):
    values = [row["_actual_r"] for row in rows]
    count = len(values)
    counts = _class_counts(rows)
    return {
        "count": count,
        "label_counts": counts,
        "target_rate": counts[CLASS_ORDER[0]] / count if count else None,
        "stop_rate": counts[CLASS_ORDER[1]] / count if count else None,
        "timeout_rate": counts[CLASS_ORDER[2]] / count if count else None,
        "positive_outcome_count": sum(value > 0.0 for value in values),
        "cumulative_net_r": float(sum(values)),
        "mean_net_r": float(sum(values) / count) if count else None,
        "median_net_r": float(median(values)) if count else None,
        "minimum_net_r": float(min(values)) if count else None,
        "maximum_net_r": float(max(values)) if count else None,
    }


def _eligible(rows):
    return [row for row in rows if row["_predicted_net_r_floor"] > 0.0]


def _nonoverlapping(rows):
    selected = []
    busy_until = {}
    for row in sorted(rows, key=lambda item: (item["_decision"], item["asset"])):
        asset = row["asset"]
        if asset not in busy_until or row["_decision"] >= busy_until[asset]:
            selected.append(row)
            busy_until[asset] = row["_event_end"]
    return selected


def _predictive_fold_summary(rows):
    target = [1 if row["actual_label"] == CLASS_ORDER[0] else 0 for row in rows]
    probability = [row["p_target_3r_first"] for row in rows]
    prevalence = sum(target) / len(target)
    precision_recall_auc = float(average_precision_score(target, probability))
    return {
        "validation_count": len(rows),
        "target_prevalence": prevalence,
        "target_precision_recall_auc": precision_recall_auc,
        "target_precision_recall_auc_lift": precision_recall_auc - prevalence,
    }


def review_prediction_records(records):
    rows = validate_prediction_records(records)
    model_reviews = []
    interested_models = []

    for model_id in MODEL_SPECS:
        model_rows = [row for row in rows if row["model_id"] == model_id]
        raw_eligible = _eligible(model_rows)
        nonoverlap = _nonoverlapping(raw_eligible)
        fold_reviews = []
        for fold in FOLD_PLAN:
            fold_id = fold["fold_id"]
            all_fold = [row for row in model_rows if row["fold_id"] == fold_id]
            raw_fold = [row for row in raw_eligible if row["fold_id"] == fold_id]
            nonoverlap_fold = [row for row in nonoverlap if row["fold_id"] == fold_id]
            predictive = _predictive_fold_summary(all_fold)
            raw_summary = _summary(raw_fold)
            nonoverlap_summary = _summary(nonoverlap_fold)
            fold_reviews.append(
                {
                    "fold_id": fold_id,
                    "predictive": predictive,
                    "raw_eligible": raw_summary,
                    "nonoverlapping_eligible": nonoverlap_summary,
                    "raw_support_pass": raw_summary["count"] >= MINIMUM_RAW_SELECTIONS_PER_FOLD,
                    "nonoverlap_support_pass": nonoverlap_summary["count"]
                    >= MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
                    "positive_nonoverlap_net_r_pass": (
                        nonoverlap_summary["mean_net_r"] is not None
                        and nonoverlap_summary["mean_net_r"] > 0.0
                        and nonoverlap_summary["cumulative_net_r"] > 0.0
                    ),
                    "positive_target_pr_auc_lift_pass": predictive[
                        "target_precision_recall_auc_lift"
                    ]
                    > 0.0,
                }
            )

        asset_reviews = []
        for asset in ASSET_ORDER:
            summary = _summary([row for row in nonoverlap if row["asset"] == asset])
            asset_reviews.append(
                {
                    "asset": asset,
                    "nonoverlapping_eligible": summary,
                    "positive_net_r_pass": summary["cumulative_net_r"] > 0.0,
                }
            )
        overall = _summary(nonoverlap)
        positive_folds = sum(item["positive_nonoverlap_net_r_pass"] for item in fold_reviews)
        positive_assets = sum(item["positive_net_r_pass"] for item in asset_reviews)
        gates = {
            "all_fold_raw_support_pass": all(item["raw_support_pass"] for item in fold_reviews),
            "all_fold_nonoverlap_support_pass": all(
                item["nonoverlap_support_pass"] for item in fold_reviews
            ),
            "positive_fold_count": positive_folds,
            "all_folds_positive_net_r_pass": positive_folds >= MINIMUM_POSITIVE_FOLDS,
            "positive_asset_count": positive_assets,
            "asset_breadth_pass": positive_assets >= MINIMUM_POSITIVE_ASSETS,
            "overall_positive_net_r_pass": (
                overall["mean_net_r"] is not None
                and overall["mean_net_r"] > 0.0
                and overall["cumulative_net_r"] > 0.0
            ),
            "all_folds_positive_target_pr_auc_lift_pass": all(
                item["positive_target_pr_auc_lift_pass"] for item in fold_reviews
            ),
        }
        interest = all(
            value
            for key, value in gates.items()
            if key.endswith("_pass")
        )
        if interest:
            interested_models.append(model_id)
        model_reviews.append(
            {
                "model_id": model_id,
                "fixed_rule": "3*p_target_3r_first-p_stop_1r_first>0",
                "folds": fold_reviews,
                "assets": asset_reviews,
                "raw_eligible_overall": _summary(raw_eligible),
                "nonoverlapping_eligible_overall": overall,
                "gates": gates,
                "development_economic_interest": interest,
            }
        )

    status = INTEREST_STATUS if interested_models else HOLD_CASH_STATUS
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "status": status,
        "action": "REVIEW_DEVELOPMENT_ECONOMIC_INTEREST" if interested_models else "HOLD_CASH",
        "model_families_with_interest": interested_models,
        "automatic_model_selection": False,
        "candidate_v2_authorized": False,
        "model_reviews": model_reviews,
    }


class KrakenAIDrivenV212hDevelopmentEconomicReview:
    def review(self, evidence_directory):
        locked = KrakenAIDrivenV212hLearningEvidenceLock().lock(evidence_directory)
        if locked.report_sha256 != EXPECTED_LEARNING_REPORT_SHA256:
            raise RuntimeError("12h learning report SHA-256 is outside the frozen review scope.")
        if locked.payload.get("learning_status") != REVIEW_REQUIRED_STATUS:
            raise RuntimeError("Completed learned OOF evidence is required for economic review.")
        prediction_path = Path(evidence_directory) / PREDICTIONS_FILENAME
        prediction_payload = json.loads(prediction_path.read_text(encoding="utf-8"))
        result = review_prediction_records(prediction_payload["records"])
        result.update(
            {
                "parent_commit": PARENT_COMMIT,
                "learning_report_sha256": locked.report_sha256,
                "learning_evidence_lock_status": "KRAKEN_AI_V2_12H_DEVELOPMENT_LEARNING_EVIDENCE_LOCK_PASS",
                "evidence_file_count": sum(
                    path.is_file() for path in Path(evidence_directory).rglob("*")
                ),
                "evidence_written": False,
                "source_archive_opened": False,
                "model_artifacts_unpickled": False,
                "labels_generated": False,
                "model_training_executed": False,
                "calibration_data_opened": False,
                "evaluation_data_opened": False,
                "bounded_forward_paper_authorized": False,
                "cloud_execution_authorized": False,
                "real_orders_submitted": False,
                "live_execution_authorized": False,
                "next_stage": (
                    "OPERATOR_REVIEW_BEFORE_ANY_CANDIDATE_FREEZE"
                    if result["model_families_with_interest"]
                    else "CLOSE_12H_V1_HYPOTHESIS_HOLD_CASH"
                ),
            }
        )
        return result


def economic_review_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "expected_learning_report_sha256": EXPECTED_LEARNING_REPORT_SHA256,
        "fixed_rule": "3*p_target_3r_first-p_stop_1r_first>0",
        "minimum_raw_selections_per_fold": MINIMUM_RAW_SELECTIONS_PER_FOLD,
        "minimum_nonoverlapping_selections_per_fold": MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
        "minimum_positive_folds": MINIMUM_POSITIVE_FOLDS,
        "minimum_positive_assets": MINIMUM_POSITIVE_ASSETS,
        "threshold_sweep_authorized": False,
        "learning_evidence_opened": False,
        "source_archive_opened": False,
        "model_artifacts_unpickled": False,
        "labels_generated": False,
        "model_training_executed": False,
        "automatic_model_selection": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "status": "KRAKEN_AI_V2_12H_DEVELOPMENT_ECONOMIC_REVIEW_IMPLEMENTED_EXTERNAL_EVIDENCE_REQUIRED",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only Kraken V2 Development OOF economic review.")
    parser.add_argument("--evidence-directory", type=Path)
    args = parser.parse_args(argv)
    result = (
        KrakenAIDrivenV212hDevelopmentEconomicReview().review(args.evidence_directory)
        if args.evidence_directory
        else economic_review_declaration()
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
