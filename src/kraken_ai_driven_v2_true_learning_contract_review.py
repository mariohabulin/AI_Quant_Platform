"""Hash-bound nonexecuting review for the True Learning Contract V1."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_round_2_closure_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from kraken_ai_driven_v2_true_learning_contract import (
        ARTIFACT_REQUIREMENTS,
        CONTRACT_ID,
        LABEL_CONTRACT,
        MODEL_BUDGET,
        PROTOCOL_ID,
        STATUS as CONTRACT_STATUS,
        learning_contract_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_2_closure_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from .kraken_ai_driven_v2_true_learning_contract import (
        ARTIFACT_REQUIREMENTS,
        CONTRACT_ID,
        LABEL_CONTRACT,
        MODEL_BUDGET,
        PROTOCOL_ID,
        STATUS as CONTRACT_STATUS,
        learning_contract_declaration,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_TRUE_LEARNING_CONTRACT_REVIEWED_STAGE_2_AUDIT_REQUIRED"
)
PROTOCOL_NORMALIZED_SHA256 = (
    "ef41ff0e6d5eadec0cacbab021c41b6877b7e497c86ba11b22f5973c9a277cdb"
)
COMPONENT_NORMALIZED_SHA256 = (
    "01b95e21f99ca750164e48032b7a74011200bd888bea5a5554633842bfb2a4fb"
)
PARENT_BINDINGS = (
    {
        "label": "AI-driven v2 Round 2 closure document",
        "path": "KRAKEN_AI_DRIVEN_V2_ROUND_2_CLOSURE.md",
        "sha256": "725cdf931d34dac4d92aa7777d52cd8dab8476ffcf37e7630f1379e54f2b3ec3",
    },
    {
        "label": "AI-driven v2 scope-gap correction document",
        "path": "KRAKEN_AI_DRIVEN_V2_SCOPE_GAP_CORRECTION_V1.md",
        "sha256": "8e088fccfef44432f2dfbe885c8e9480b6718b505ba4677d5f23f646edc659db",
    },
    {
        "label": "AI-driven v2 Round 2 closure component",
        "path": "src/kraken_ai_driven_v2_round_2_closure.py",
        "sha256": "ed239adffcce8221bc1a5f828fa95d9c2fc42df0aa80d81af80df4a17ae60cac",
    },
    {
        "label": "AI-driven v2 Round 2 closure review",
        "path": "src/kraken_ai_driven_v2_round_2_closure_review.py",
        "sha256": "f1d9a28bf4263ae8f9d9d155e6844d005d5672da21617f36fa6294547327d147",
    },
)
DEFAULT_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_TRUE_LEARNING_CONTRACT_V1.md"
)
DEFAULT_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_true_learning_contract.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 True Learning Contract input: {path}"
        ) from exc
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
            "AI-driven v2 True Learning Contract protocol SHA256 mismatch: "
            f"{digest} != {PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        CONTRACT_STATUS,
        PROTOCOL_ID,
        CONTRACT_ID,
        "What one training example means",
        "TARGET_3R_FIRST",
        "STOP_1R_FIRST",
        "TIMEOUT_NO_BARRIER",
        "Resolution is not selected in Stage 1",
        "two model families and no more than twelve total variants",
        "learned model artifact",
        "Calibration and Evaluation remain unopened",
        "Candidate v2 remains unauthorized",
    )
    if any(value not in text for value in required):
        raise RuntimeError(
            "AI-driven v2 True Learning Contract required text is missing."
        )
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("True Learning Contract parent review mismatch.")
    bindings = declaration.get("parent_source_binding_matches")
    if not isinstance(bindings, dict) or not bindings or not all(bindings.values()):
        raise RuntimeError("True Learning Contract parent binding mismatch.")
    for field in (
        "closure_component_sha256_match",
        "closure_document_sha256_match",
        "scope_correction_document_sha256_match",
        "parent_discovery_runner_review_passed",
        "round_2_closure_implemented",
        "offline_feedback_attribution_implemented",
        "scope_gap_correction_recorded",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(f"True Learning Contract parent mismatch for {field}.")
    for field in (
        "true_learning_engine_implemented",
        "round_2_evidence_opened",
        "round_2_closed",
        "round_2_rerun_authorized",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(
                f"True Learning Contract parent safety mismatch for {field}."
            )


def review_declaration(
    *binding_paths,
    protocol_path=DEFAULT_PROTOCOL_PATH,
    component_path=DEFAULT_COMPONENT_PATH,
    parent_reviewer=None,
):
    if not binding_paths:
        binding_paths = tuple(Path(item["path"]) for item in PARENT_BINDINGS)
    if len(binding_paths) != len(PARENT_BINDINGS):
        raise ValueError("True Learning Contract binding path count mismatch.")

    binding_matches = {}
    for binding, path in zip(PARENT_BINDINGS, binding_paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, protocol_digest = load_protocol(protocol_path)
    component_digest = _load_exact(
        component_path,
        COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 True Learning Contract component",
    )

    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("True Learning Contract parent reviewer must be callable.")
    _validate_parent_review(reviewer())

    contract = learning_contract_declaration()
    if contract.get("protocol_id") != PROTOCOL_ID:
        raise RuntimeError("True Learning Contract protocol identity mismatch.")
    if contract.get("contract_id") != CONTRACT_ID:
        raise RuntimeError("True Learning Contract identity mismatch.")
    for field in (
        "round_2_closed",
        "rule_discovery_foundation_complete",
        "true_learning_contract_frozen",
    ):
        if contract.get(field) is not True:
            raise RuntimeError(f"True Learning Contract mismatch for {field}.")
    for field in (
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "labels_generated",
        "model_training_authorized",
        "model_training_executed",
        "walk_forward_executed",
        "parameter_sweep_executed",
        "automatic_model_selection_executed",
        "runtime_learning_authorized",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if contract.get(field) is not False:
            raise RuntimeError(
                f"True Learning Contract safety mismatch for {field}."
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "contract_status": contract["status"],
        "protocol_id": PROTOCOL_ID,
        "contract_id": CONTRACT_ID,
        "contract_sha256": contract["contract_sha256"],
        "stage_0_commit": contract["stage_0_commit"],
        "round_2_report_sha256": contract["round_2_report_sha256"],
        "stage_0_parent_binding_matches": binding_matches,
        "protocol_sha256_match": protocol_digest == PROTOCOL_NORMALIZED_SHA256,
        "component_sha256_match": component_digest == COMPONENT_NORMALIZED_SHA256,
        "round_2_closed": True,
        "round_2_rerun_authorized": False,
        "true_learning_contract_frozen": True,
        "label_id": LABEL_CONTRACT["label_id"],
        "label_class_order": list(LABEL_CONTRACT["class_order"]),
        "selected_resolution": contract["resolution_contract"][
            "selected_resolution"
        ],
        "model_family_count": MODEL_BUDGET["maximum_model_families"],
        "maximum_total_variants": MODEL_BUDGET["maximum_total_variants"],
        "parameters_learned_from_labels_required": MODEL_BUDGET[
            "parameters_learned_from_labels"
        ],
        "learned_model_artifact_required": ARTIFACT_REQUIREMENTS[
            "learned_model_bytes_sha256"
        ],
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "labels_generated": False,
        "model_training_authorized": False,
        "model_training_executed": False,
        "walk_forward_executed": False,
        "parameter_sweep_executed": False,
        "runtime_learning_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": contract["next_stage"],
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review nonexecuting Kraken V2 True Learning Contract."
    )
    for index, binding in enumerate(PARENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL_PATH))
    parser.add_argument("--component", default=str(DEFAULT_COMPONENT_PATH))
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(4)]
    declaration = review_declaration(
        *binding_paths,
        protocol_path=args.protocol,
        component_path=args.component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
