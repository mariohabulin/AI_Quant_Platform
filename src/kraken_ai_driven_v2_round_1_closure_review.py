"""Hash-bound nonexecuting review for Kraken AI-driven V2 Round 1 closure."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_round_1_closure import (
        CLOSURE_PROTOCOL_ID,
        CLOSURE_STATUS,
        EXECUTION_COMMIT,
        RECORDED_REPORT_SHA256,
        closure_contract_declaration,
    )
    from kraken_ai_driven_v2_round_1_discovery_runner_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_1_closure import (
        CLOSURE_PROTOCOL_ID,
        CLOSURE_STATUS,
        EXECUTION_COMMIT,
        RECORDED_REPORT_SHA256,
        closure_contract_declaration,
    )
    from .kraken_ai_driven_v2_round_1_discovery_runner_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_ROUND_1_CLOSURE_REVIEWED_EXTERNAL_EVIDENCE_REQUIRED"
)
CLOSURE_DOCUMENT_NORMALIZED_SHA256 = (
    "7e10a8ee49174ffb8d278231ca4561046ea0e6312a7a5252d1587ff238162f84"
)
CLOSURE_COMPONENT_NORMALIZED_SHA256 = (
    "dd6b74c01727d5127c311fe7cb272a02471107cb65eec1dfa818b5814c22ba87"
)
PARENT_BINDINGS = (
    {
        "label": "AI-driven v2 Round 1 discovery runner protocol",
        "path": "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_1_DISCOVERY_RUNNER_PROTOCOL_V1.md",
        "sha256": "d84b9408a409a0be99aa584c744bd27bf98b7a2628180f1020ec01298e277e5a",
    },
    {
        "label": "AI-driven v2 Round 1 discovery runner component",
        "path": "src/kraken_ai_driven_v2_round_1_discovery_runner.py",
        "sha256": "0f1376d03d6a170da09a1faf023879e74c358ee3445be0bcbfe05a1e9c3db5ab",
    },
    {
        "label": "AI-driven v2 Round 1 discovery runner review",
        "path": "src/kraken_ai_driven_v2_round_1_discovery_runner_review.py",
        "sha256": "402da66752b8e23ea1adcc8cc91ba32235c018e46844dcf4ebeedbc4318d0a67",
    },
)
DEFAULT_CLOSURE_DOCUMENT_PATH = Path("KRAKEN_AI_DRIVEN_V2_ROUND_1_CLOSURE.md")
DEFAULT_CLOSURE_COMPONENT_PATH = Path("src/kraken_ai_driven_v2_round_1_closure.py")


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"Unable to read AI-driven v2 Round 1 closure input: {path}") from exc
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
            "AI-driven v2 Round 1 closure document SHA256 mismatch: "
            f"{digest} != {CLOSURE_DOCUMENT_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        CLOSURE_STATUS,
        EXECUTION_COMMIT,
        RECORDED_REPORT_SHA256,
        "Round 1 rerun authorization is permanently false",
        "Feedback describes frozen evidence",
        "Round 2 is not registered",
        "Calibration, Evaluation and Candidate v2 remain unauthorized",
    )
    if any(value not in text for value in required):
        raise RuntimeError("Round 1 closure required contract text is missing.")
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Round 1 closure parent review mismatch.")
    matches = declaration.get("parent_source_binding_matches")
    if not isinstance(matches, dict) or not matches or not all(matches.values()):
        raise RuntimeError("Round 1 closure parent binding mismatch.")
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
            raise RuntimeError(f"Round 1 closure parent mismatch for {field}.")
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
            raise RuntimeError(f"Round 1 closure parent safety mismatch for {field}.")


def review_declaration(
    parent_protocol_path=Path(PARENT_BINDINGS[0]["path"]),
    parent_component_path=Path(PARENT_BINDINGS[1]["path"]),
    parent_review_path=Path(PARENT_BINDINGS[2]["path"]),
    *,
    closure_document_path=DEFAULT_CLOSURE_DOCUMENT_PATH,
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
    _, document_digest = load_closure_document(closure_document_path)
    component_digest = _load_exact(
        closure_component_path,
        CLOSURE_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 Round 1 closure component",
    )
    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Round 1 closure parent reviewer must be callable.")
    _validate_parent_review(reviewer())

    contract = closure_contract_declaration()
    if contract.get("closure_protocol_id") != CLOSURE_PROTOCOL_ID:
        raise RuntimeError("Round 1 closure protocol identity mismatch.")
    if contract.get("execution_commit") != EXECUTION_COMMIT:
        raise RuntimeError("Round 1 closure execution commit mismatch.")
    if contract.get("recorded_report_sha256") != RECORDED_REPORT_SHA256:
        raise RuntimeError("Round 1 closure report identity mismatch.")
    for field in (
        "round_1_closure_implemented",
        "offline_feedback_attribution_implemented",
    ):
        if contract.get(field) is not True:
            raise RuntimeError(f"Round 1 closure contract mismatch for {field}.")
    for field in (
        "round_2_manifest_registered",
        "round_1_evidence_opened",
        "round_1_rerun_authorized",
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
            raise RuntimeError(f"Round 1 closure contract safety mismatch for {field}.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "closure_protocol_id": CLOSURE_PROTOCOL_ID,
        "execution_commit": EXECUTION_COMMIT,
        "recorded_report_sha256": RECORDED_REPORT_SHA256,
        "expected_closure_status": CLOSURE_STATUS,
        "parent_source_binding_matches": binding_matches,
        "closure_document_sha256_match": document_digest == CLOSURE_DOCUMENT_NORMALIZED_SHA256,
        "closure_component_sha256_match": component_digest == CLOSURE_COMPONENT_NORMALIZED_SHA256,
        "parent_discovery_runner_review_passed": True,
        "round_1_closure_implemented": True,
        "offline_feedback_attribution_implemented": True,
        "external_evidence_required_for_closure": True,
        "round_1_evidence_opened": False,
        "round_1_closed": False,
        "round_1_rerun_authorized": False,
        "round_2_manifest_registered": False,
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
        "next_stage": "RUN_READ_ONLY_ROUND_1_CLOSURE_ON_LOCKED_EVIDENCE",
    }


def _parser():
    parser = argparse.ArgumentParser(description="Review nonexecuting Kraken V2 Round 1 closure.")
    for index, binding in enumerate(PARENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument("--closure-document", default=str(DEFAULT_CLOSURE_DOCUMENT_PATH))
    parser.add_argument("--closure-component", default=str(DEFAULT_CLOSURE_COMPONENT_PATH))
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(3)]
    declaration = review_declaration(
        *binding_paths,
        closure_document_path=args.closure_document,
        closure_component_path=args.closure_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
