"""Hash-bound nonexecuting review for Round 2 closure and scope correction."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_round_2_closure import (
        CLOSURE_PROTOCOL_ID,
        CLOSURE_STATUS,
        EXECUTION_COMMIT,
        RECORDED_REPORT_SHA256,
        closure_contract_declaration,
    )
    from kraken_ai_driven_v2_round_2_discovery_runner_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_2_closure import (
        CLOSURE_PROTOCOL_ID,
        CLOSURE_STATUS,
        EXECUTION_COMMIT,
        RECORDED_REPORT_SHA256,
        closure_contract_declaration,
    )
    from .kraken_ai_driven_v2_round_2_discovery_runner_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_ROUND_2_CLOSURE_REVIEWED_EXTERNAL_EVIDENCE_REQUIRED"
)
CLOSURE_DOCUMENT_NORMALIZED_SHA256 = (
    "725cdf931d34dac4d92aa7777d52cd8dab8476ffcf37e7630f1379e54f2b3ec3"
)
SCOPE_CORRECTION_DOCUMENT_NORMALIZED_SHA256 = (
    "8e088fccfef44432f2dfbe885c8e9480b6718b505ba4677d5f23f646edc659db"
)
CLOSURE_COMPONENT_NORMALIZED_SHA256 = (
    "ed239adffcce8221bc1a5f828fa95d9c2fc42df0aa80d81af80df4a17ae60cac"
)
PARENT_BINDINGS = (
    {
        "label": "AI-driven v2 Round 2 discovery runner protocol",
        "path": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_2_DISCOVERY_RUNNER_PROTOCOL_V1.md",
        "sha256": "11cf6181923578379fc10e7fa7d89a210a25b2cbd73cd3cd3fb0c99f274e2aae",
    },
    {
        "label": "AI-driven v2 Round 2 discovery runner component",
        "path": "src/kraken_ai_driven_v2_round_2_discovery_runner.py",
        "sha256": "1d6dc71b1d896c04e798ed2e8e9aabf45fafd2050b8654d0683d4381018c9252",
    },
    {
        "label": "AI-driven v2 Round 2 discovery runner review",
        "path": "src/kraken_ai_driven_v2_round_2_discovery_runner_review.py",
        "sha256": "cc05a528a5386aac334eef5ef7bd2991d49c4e85a15424ba1042363f11aab470",
    },
)
DEFAULT_CLOSURE_DOCUMENT_PATH = Path("KRAKEN_AI_DRIVEN_V2_ROUND_2_CLOSURE.md")
DEFAULT_SCOPE_CORRECTION_DOCUMENT_PATH = Path(
    "KRAKEN_AI_DRIVEN_V2_SCOPE_GAP_CORRECTION_V1.md"
)
DEFAULT_CLOSURE_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_round_2_closure.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 Round 2 closure input: {path}"
        ) from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_exact(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(f"{label} SHA256 mismatch: {digest} != {expected_sha256}.")
    return digest


def load_closure_document(path=DEFAULT_CLOSURE_DOCUMENT_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CLOSURE_DOCUMENT_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 Round 2 closure document SHA256 mismatch: "
            f"{digest} != {CLOSURE_DOCUMENT_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        CLOSURE_STATUS,
        EXECUTION_COMMIT,
        RECORDED_REPORT_SHA256,
        "Round 2 rerun authorization is permanently false",
        "Feedback describes frozen evidence",
        "Rule Discovery Foundation is not a Learning Engine",
        "Calibration, Evaluation and Candidate v2 remain unauthorized",
    )
    if any(value not in text for value in required):
        raise RuntimeError("Round 2 closure required contract text is missing.")
    return text, digest


def load_scope_correction_document(path=DEFAULT_SCOPE_CORRECTION_DOCUMENT_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SCOPE_CORRECTION_DOCUMENT_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 scope correction document SHA256 mismatch: "
            f"{digest} != {SCOPE_CORRECTION_DOCUMENT_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        "True Learning Engine is not implemented",
        "Rule Discovery Foundation",
        "offline learning",
        "learned model artifact",
        "Stage 1 — freeze the True Learning Contract",
        "Candidate v2 promotion is explicit and separately authorized",
    )
    if any(value not in text for value in required):
        raise RuntimeError("AI-driven v2 scope correction contract text is missing.")
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Round 2 closure parent review mismatch.")
    matches = declaration.get("parent_source_binding_matches")
    if not isinstance(matches, dict) or not matches or not all(matches.values()):
        raise RuntimeError("Round 2 closure parent binding mismatch.")
    for field in (
        "runner_protocol_sha256_match",
        "runner_component_sha256_match",
        "parent_family_execution_review_passed",
        "development_only_reader_reused",
        "independent_evidence_lock_implemented",
        "one_shot_atomic_evidence_implemented",
        "absolute_route_gates_implemented",
        "round_interest_gate_implemented",
        "discovery_runner_implemented",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(f"Round 2 closure parent mismatch for {field}.")
    for field in (
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "development_run_authorized",
        "development_run_executed",
        "performance_evaluation_executed",
        "automatic_ranking_generated",
        "automatic_strategy_selection",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(f"Round 2 closure parent safety mismatch for {field}.")


def review_declaration(
    parent_protocol_path=Path(PARENT_BINDINGS[0]["path"]),
    parent_component_path=Path(PARENT_BINDINGS[1]["path"]),
    parent_review_path=Path(PARENT_BINDINGS[2]["path"]),
    *,
    closure_document_path=DEFAULT_CLOSURE_DOCUMENT_PATH,
    scope_correction_document_path=DEFAULT_SCOPE_CORRECTION_DOCUMENT_PATH,
    closure_component_path=DEFAULT_CLOSURE_COMPONENT_PATH,
    parent_reviewer=None,
):
    binding_matches = {}
    for binding, path in zip(
        PARENT_BINDINGS,
        (parent_protocol_path, parent_component_path, parent_review_path),
    ):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, closure_document_digest = load_closure_document(closure_document_path)
    _, scope_document_digest = load_scope_correction_document(
        scope_correction_document_path
    )
    component_digest = _load_exact(
        closure_component_path,
        CLOSURE_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 Round 2 closure component",
    )

    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Round 2 closure parent reviewer must be callable.")
    _validate_parent_review(reviewer())

    contract = closure_contract_declaration()
    if contract.get("closure_protocol_id") != CLOSURE_PROTOCOL_ID:
        raise RuntimeError("Round 2 closure protocol identity mismatch.")
    if contract.get("execution_commit") != EXECUTION_COMMIT:
        raise RuntimeError("Round 2 closure execution commit mismatch.")
    if contract.get("recorded_report_sha256") != RECORDED_REPORT_SHA256:
        raise RuntimeError("Round 2 closure report identity mismatch.")
    for field in (
        "round_2_closure_implemented",
        "offline_feedback_attribution_implemented",
        "scope_gap_correction_recorded",
    ):
        if contract.get(field) is not True:
            raise RuntimeError(f"Round 2 closure contract mismatch for {field}.")
    for field in (
        "true_learning_engine_implemented",
        "round_2_evidence_opened",
        "round_2_rerun_authorized",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "automatic_ranking_generated",
        "automatic_strategy_selection",
        "runtime_learning_authorized",
        "candidate_v2_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    ):
        if contract.get(field) is not False:
            raise RuntimeError(f"Round 2 closure contract safety mismatch for {field}.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "closure_protocol_id": CLOSURE_PROTOCOL_ID,
        "execution_commit": EXECUTION_COMMIT,
        "recorded_report_sha256": RECORDED_REPORT_SHA256,
        "expected_closure_status": CLOSURE_STATUS,
        "parent_source_binding_matches": binding_matches,
        "closure_document_sha256_match": (
            closure_document_digest == CLOSURE_DOCUMENT_NORMALIZED_SHA256
        ),
        "scope_correction_document_sha256_match": (
            scope_document_digest == SCOPE_CORRECTION_DOCUMENT_NORMALIZED_SHA256
        ),
        "closure_component_sha256_match": (
            component_digest == CLOSURE_COMPONENT_NORMALIZED_SHA256
        ),
        "parent_discovery_runner_review_passed": True,
        "round_2_closure_implemented": True,
        "offline_feedback_attribution_implemented": True,
        "scope_gap_correction_recorded": True,
        "true_learning_engine_implemented": False,
        "external_evidence_required_for_closure": True,
        "round_2_evidence_opened": False,
        "round_2_closed": False,
        "round_2_rerun_authorized": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "runtime_learning_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": (
            "RUN_READ_ONLY_ROUND_2_CLOSURE_THEN_IMPLEMENT_TRUE_LEARNING_CONTRACT_V1"
        ),
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review nonexecuting Kraken V2 Round 2 closure."
    )
    for index, binding in enumerate(PARENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument(
        "--closure-document", default=str(DEFAULT_CLOSURE_DOCUMENT_PATH)
    )
    parser.add_argument(
        "--scope-correction-document",
        default=str(DEFAULT_SCOPE_CORRECTION_DOCUMENT_PATH),
    )
    parser.add_argument(
        "--closure-component", default=str(DEFAULT_CLOSURE_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(3)]
    declaration = review_declaration(
        *binding_paths,
        closure_document_path=args.closure_document,
        scope_correction_document_path=args.scope_correction_document,
        closure_component_path=args.closure_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
