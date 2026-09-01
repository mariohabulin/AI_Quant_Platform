"""Hash-bound nonexecuting review of the Kraken V2 Stage 2 audit."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_data_sufficiency_audit import (
        AUDIT_ID,
        CANDIDATE_RESOLUTIONS,
        PROTOCOL_ID,
        STAGE_1_COMMIT,
        STATUS as AUDIT_COMPONENT_STATUS,
        audit_declaration,
    )
    from kraken_ai_driven_v2_true_learning_contract_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_data_sufficiency_audit import (
        AUDIT_ID,
        CANDIDATE_RESOLUTIONS,
        PROTOCOL_ID,
        STAGE_1_COMMIT,
        STATUS as AUDIT_COMPONENT_STATUS,
        audit_declaration,
    )
    from .kraken_ai_driven_v2_true_learning_contract_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_STAGE_2_DATA_SUFFICIENCY_AUDIT_"
    "REVIEWED_EXECUTION_AUTHORIZATION_REQUIRED"
)
PROTOCOL_NORMALIZED_SHA256 = (
    "344884ba11c42b3f0d04315d3b9bbaf197c64e368669148a3219924c0ba2a60a"
)
COMPONENT_NORMALIZED_SHA256 = (
    "260bf1c1fece5e8be054a20ce5251ebe51e231bea32082cb237e77d6cccf348e"
)
PARENT_BINDINGS = (
    {
        "label": "AI-driven v2 True Learning Contract V1 protocol",
        "path": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_TRUE_LEARNING_CONTRACT_V1.md",
        "sha256": "ef41ff0e6d5eadec0cacbab021c41b6877b7e497c86ba11b22f5973c9a277cdb",
    },
    {
        "label": "AI-driven v2 True Learning Contract V1 component",
        "path": "src/kraken_ai_driven_v2_true_learning_contract.py",
        "sha256": "01b95e21f99ca750164e48032b7a74011200bd888bea5a5554633842bfb2a4fb",
    },
    {
        "label": "AI-driven v2 True Learning Contract V1 review",
        "path": "src/kraken_ai_driven_v2_true_learning_contract_review.py",
        "sha256": "9dccf142848afa9cc668b7d92defa8dd23aaa0f571d436728538a5a7dd20835e",
    },
    {
        "label": "Kraken archive-only daily dataset lock protocol v2",
        "path": "KRAKEN_BTC_ETH_XRP_DAILY_DATASET_LOCK_PROTOCOL_V2.md",
        "sha256": "814cd561e1869023832315050683665c142f3b216ae354d45019a28edcc6a05a",
    },
    {
        "label": "Kraken archive-only dataset component",
        "path": "src/kraken_daily_dataset.py",
        "sha256": "82692459a4267f9f9e67f163a59e67c7a085fa3b7cc1cd81d3da8b147b3a4965",
    },
)
DEFAULT_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_"
    "DATA_SUFFICIENCY_RESOLUTION_AUDIT_PROTOCOL_V1.md"
)
DEFAULT_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_data_sufficiency_audit.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read Stage 2 audit input: {path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_exact(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(f"{label} SHA256 mismatch: {digest} != {expected_sha256}.")
    return digest


def load_protocol(path=DEFAULT_PROTOCOL_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PROTOCOL_NORMALIZED_SHA256:
        raise RuntimeError(
            "Stage 2 data-sufficiency audit protocol SHA256 mismatch: "
            f"{digest} != {PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        AUDIT_COMPONENT_STATUS,
        PROTOCOL_ID,
        AUDIT_ID,
        "1d, 12h and 4h",
        "timestamp-only",
        "90` elapsed UTC days",
        "30` elapsed UTC days",
        "9,000",
        "COARSEST_PASSING_CANDIDATE",
        "Calibration and Evaluation",
        "remain unopened",
        "Candidate v2 promotion",
    )
    if any(value not in text for value in required):
        raise RuntimeError("Stage 2 audit protocol required text is missing.")
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Stage 2 parent review mismatch.")
    bindings = declaration.get("stage_0_parent_binding_matches")
    if not isinstance(bindings, dict) or not bindings or not all(bindings.values()):
        raise RuntimeError("Stage 2 parent review binding mismatch.")
    for field in (
        "protocol_sha256_match",
        "component_sha256_match",
        "round_2_closed",
        "true_learning_contract_frozen",
        "parameters_learned_from_labels_required",
        "learned_model_artifact_required",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(f"Stage 2 parent review mismatch for {field}.")
    if declaration.get("selected_resolution") is not None:
        raise RuntimeError("Stage 2 parent unexpectedly selected a resolution.")
    for field in (
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "labels_generated",
        "model_training_executed",
        "walk_forward_executed",
        "candidate_v2_authorized",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(f"Stage 2 parent safety mismatch for {field}.")


def review_declaration(
    *binding_paths,
    protocol_path=DEFAULT_PROTOCOL_PATH,
    component_path=DEFAULT_COMPONENT_PATH,
    parent_reviewer=None,
):
    if not binding_paths:
        binding_paths = tuple(Path(item["path"]) for item in PARENT_BINDINGS)
    if len(binding_paths) != len(PARENT_BINDINGS):
        raise ValueError("Stage 2 audit binding path count mismatch.")
    binding_matches = {}
    for binding, path in zip(PARENT_BINDINGS, binding_paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, protocol_digest = load_protocol(protocol_path)
    component_digest = _load_exact(
        component_path,
        COMPONENT_NORMALIZED_SHA256,
        "Stage 2 data-sufficiency audit component",
    )
    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Stage 2 parent reviewer must be callable.")
    _validate_parent_review(reviewer())

    declaration = audit_declaration()
    if declaration.get("protocol_id") != PROTOCOL_ID:
        raise RuntimeError("Stage 2 audit protocol identity mismatch.")
    if declaration.get("audit_id") != AUDIT_ID:
        raise RuntimeError("Stage 2 audit identity mismatch.")
    for field in (
        "timestamp_column_only_reader_implemented",
        "archive_hash_verification_implemented",
        "independent_evidence_lock_implemented",
        "one_shot_atomic_evidence_implemented",
        "audit_runner_implemented",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(f"Stage 2 implementation mismatch for {field}.")
    for field in (
        "authorization_phrase_active",
        "source_archive_opened",
        "timestamp_columns_opened",
        "ohlcvt_value_columns_opened",
        "development_market_values_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "audit_run_authorized",
        "audit_run_executed",
        "performance_evaluation_executed",
        "labels_generated",
        "model_training_executed",
        "walk_forward_executed",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(f"Stage 2 safety mismatch for {field}.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "audit_component_status": declaration["status"],
        "protocol_id": PROTOCOL_ID,
        "audit_id": AUDIT_ID,
        "stage_1_commit": STAGE_1_COMMIT,
        "stage_1_parent_binding_matches": binding_matches,
        "protocol_sha256_match": protocol_digest == PROTOCOL_NORMALIZED_SHA256,
        "component_sha256_match": component_digest == COMPONENT_NORMALIZED_SHA256,
        "true_learning_contract_sha256": declaration[
            "true_learning_contract_sha256"
        ],
        "audit_configuration_sha256": declaration[
            "audit_configuration_sha256"
        ],
        "candidate_resolution_minutes": [
            item["interval_minutes"] for item in CANDIDATE_RESOLUTIONS
        ],
        "candidate_resolution_timeframes": [
            item["timeframe"] for item in CANDIDATE_RESOLUTIONS
        ],
        "fold_count": declaration["fold_count"],
        "selection_uses_performance": False,
        "timestamp_column_only_reader_implemented": True,
        "audit_runner_implemented": True,
        "independent_evidence_lock_implemented": True,
        "one_shot_atomic_evidence_implemented": True,
        "authorization_phrase": declaration["authorization_phrase"],
        "authorization_phrase_active": False,
        "source_archive_opened": False,
        "timestamp_columns_opened": False,
        "ohlcvt_value_columns_opened": False,
        "development_market_values_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "audit_run_authorized": False,
        "audit_run_executed": False,
        "performance_evaluation_executed": False,
        "selected_resolution": None,
        "selected_resolution_dataset_locked": False,
        "labels_generated": False,
        "model_training_authorized": False,
        "model_training_executed": False,
        "walk_forward_executed": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": declaration["next_stage"],
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review nonexecuting Kraken V2 Stage 2 audit."
    )
    for index, binding in enumerate(PARENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL_PATH))
    parser.add_argument("--component", default=str(DEFAULT_COMPONENT_PATH))
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [
        getattr(args, f"binding_{index}") for index in range(len(PARENT_BINDINGS))
    ]
    declaration = review_declaration(
        *binding_paths,
        protocol_path=args.protocol,
        component_path=args.component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
