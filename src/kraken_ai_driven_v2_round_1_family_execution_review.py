"""Hash-bound nonexecuting review for Kraken V2 Round 1 family execution."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_round_1_causal_signals_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from kraken_ai_driven_v2_round_1_family_execution import (
        BASELINE_COST_PROFILE_ID,
        FAMILY_EXECUTION_COMPONENT_ID,
        FAMILY_ORDER,
        STRESS_COST_PROFILE_ID,
        execution_component_declaration,
        family_execution_adapters,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_1_causal_signals_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from .kraken_ai_driven_v2_round_1_family_execution import (
        BASELINE_COST_PROFILE_ID,
        FAMILY_EXECUTION_COMPONENT_ID,
        FAMILY_ORDER,
        STRESS_COST_PROFILE_ID,
        execution_component_declaration,
        family_execution_adapters,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_ROUND_1_FAMILY_EXECUTION_REVIEWED_"
    "DISCOVERY_RUNNER_REQUIRED"
)
EXECUTION_PROTOCOL_NORMALIZED_SHA256 = (
    "4e142762ae8a7af1dc18408b60faa29c3bf8fc5b3312f7e01a0e2d8f13525331"
)
EXECUTION_COMPONENT_NORMALIZED_SHA256 = (
    "e0235ea7fa7bae84b817ad9a65fba525ff5eeb76da30b31f7cd967341b3367b6"
)
COMPONENT_BINDINGS = (
    {
        "label": "AI-driven v2 Round 1 causal signals protocol",
        "path": (
            "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_"
            "ROUND_1_CAUSAL_SIGNALS_PROTOCOL_V1.md"
        ),
        "sha256": "5dd4a39698913f9d01ed725ba96cb3d5027abc592c1f3161ec35a74d5baeb76b",
    },
    {
        "label": "AI-driven v2 Round 1 causal signals component",
        "path": "src/kraken_ai_driven_v2_round_1_causal_signals.py",
        "sha256": "c76a27cc71e35e7f504a473c24120ad4af7f216707fec9c07c552dcea53a6c1c",
    },
    {
        "label": "AI-driven v2 Round 1 causal signals review",
        "path": "src/kraken_ai_driven_v2_round_1_causal_signals_review.py",
        "sha256": "4902438b1fd2906784ba7266902310ec58399987ca9dbe61c4320026a771784d",
    },
)
DEFAULT_EXECUTION_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_1_FAMILY_EXECUTION_PROTOCOL_V1.md"
)
DEFAULT_EXECUTION_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_round_1_family_execution.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 Round 1 family execution input: {path}"
        ) from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path):
    return hashlib.sha256(_normalized_text_bytes(path)).hexdigest()


def _load_exact(path, expected_sha256, label):
    digest = normalized_text_sha256(path)
    if digest != expected_sha256:
        raise RuntimeError(
            f"{label} SHA256 mismatch: {digest} != {expected_sha256}."
        )
    return digest


def load_execution_protocol(path=DEFAULT_EXECUTION_PROTOCOL_PATH):
    raw = _normalized_text_bytes(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXECUTION_PROTOCOL_NORMALIZED_SHA256:
        raise RuntimeError(
            "AI-driven v2 Round 1 family execution protocol SHA256 mismatch: "
            f"{digest} != {EXECUTION_PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        "four family-specific execution adapters",
        "stop gap before scheduled exit",
        "same-bar stop and target: `STOP_FIRST`",
        "execution components implemented: `true`",
        "development data opened: `false`",
        "real orders submitted: `false`",
        "Reference A",
        "Candidate v2",
    )
    if any(value not in text for value in required):
        raise RuntimeError(
            "AI-driven v2 Round 1 family execution required contract text "
            "is missing."
        )
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Round 1 family execution parent review mismatch.")
    bindings = declaration.get("parent_source_binding_matches")
    if not isinstance(bindings, dict) or not bindings or not all(bindings.values()):
        raise RuntimeError("Round 1 family execution parent binding mismatch.")
    for field in (
        "signal_protocol_sha256_match",
        "signal_component_sha256_match",
        "parent_round_1_review_passed",
        "feature_component_implemented",
        "regime_components_implemented",
        "signal_components_implemented",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(
                f"Round 1 family execution parent mismatch for {field}."
            )
    for field in (
        "execution_components_implemented",
        "discovery_runner_implemented",
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "performance_evaluation_executed",
        "candidate_v2_authorized",
        "live_execution_authorized",
    ):
        if declaration.get(field) is not False:
            raise RuntimeError(
                f"Round 1 family execution parent safety mismatch for {field}."
            )


def review_declaration(
    parent_protocol_path=Path(COMPONENT_BINDINGS[0]["path"]),
    parent_component_path=Path(COMPONENT_BINDINGS[1]["path"]),
    parent_review_path=Path(COMPONENT_BINDINGS[2]["path"]),
    *,
    execution_protocol_path=DEFAULT_EXECUTION_PROTOCOL_PATH,
    execution_component_path=DEFAULT_EXECUTION_COMPONENT_PATH,
    parent_reviewer=None,
):
    paths = (parent_protocol_path, parent_component_path, parent_review_path)
    binding_matches = {}
    for binding, path in zip(COMPONENT_BINDINGS, paths):
        digest = _load_exact(path, binding["sha256"], binding["label"])
        binding_matches[binding["label"]] = digest == binding["sha256"]
    _, protocol_digest = load_execution_protocol(execution_protocol_path)
    component_digest = _load_exact(
        execution_component_path,
        EXECUTION_COMPONENT_NORMALIZED_SHA256,
        "AI-driven v2 Round 1 family execution component",
    )

    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Round 1 family execution parent reviewer must be callable.")
    parent_review = reviewer()
    _validate_parent_review(parent_review)

    component = execution_component_declaration()
    adapters = family_execution_adapters()
    if component.get("component_id") != FAMILY_EXECUTION_COMPONENT_ID:
        raise RuntimeError("Round 1 family execution component ID mismatch.")
    if tuple(component.get("family_order", ())) != FAMILY_ORDER:
        raise RuntimeError("Round 1 family execution order mismatch.")
    if tuple(adapters) != FAMILY_ORDER:
        raise RuntimeError("Round 1 family adapter order mismatch.")
    for field in (
        "family_execution_components_implemented",
        "baseline_cost_profile_implemented",
        "stress_cost_profile_implemented",
        "shared_safety_envelope_implemented",
        "protective_execution_implemented",
    ):
        if component.get(field) is not True:
            raise RuntimeError(
                f"Round 1 family execution component mismatch for {field}."
            )
    for field in (
        "discovery_runner_implemented",
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "performance_evaluation_executed",
        "real_orders_submitted",
        "candidate_v2_authorized",
        "live_execution_authorized",
    ):
        if component.get(field) is not False:
            raise RuntimeError(
                f"Round 1 family execution safety mismatch for {field}."
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "component_id": FAMILY_EXECUTION_COMPONENT_ID,
        "round_1_configuration_sha256": component[
            "round_1_configuration_sha256"
        ],
        "family_order": list(FAMILY_ORDER),
        "family_count": len(FAMILY_ORDER),
        "cost_profile_ids": [
            BASELINE_COST_PROFILE_ID,
            STRESS_COST_PROFILE_ID,
        ],
        "parent_source_binding_matches": binding_matches,
        "execution_protocol_sha256_match": (
            protocol_digest == EXECUTION_PROTOCOL_NORMALIZED_SHA256
        ),
        "execution_component_sha256_match": (
            component_digest == EXECUTION_COMPONENT_NORMALIZED_SHA256
        ),
        "parent_causal_signal_review_passed": True,
        "feature_component_implemented": True,
        "regime_components_implemented": True,
        "signal_components_implemented": True,
        "family_execution_components_implemented": True,
        "baseline_cost_profile_implemented": True,
        "stress_cost_profile_implemented": True,
        "shared_safety_envelope_implemented": True,
        "protective_execution_implemented": True,
        "discovery_runner_implemented": False,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": False,
        "performance_evaluation_executed": False,
        "parameter_sweep_authorized": False,
        "automatic_ranking_authorized": False,
        "automatic_strategy_selection_authorized": False,
        "runtime_learning_authorized": False,
        "calibration_authorized": False,
        "evaluation_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
        "next_stage": "IMPLEMENT_ROUND_1_DEVELOPMENT_DISCOVERY_RUNNER",
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review nonexecuting Kraken V2 Round 1 family execution."
    )
    for index, binding in enumerate(COMPONENT_BINDINGS):
        parser.add_argument(f"--binding-{index}", default=binding["path"])
    parser.add_argument(
        "--execution-protocol", default=str(DEFAULT_EXECUTION_PROTOCOL_PATH)
    )
    parser.add_argument(
        "--execution-component", default=str(DEFAULT_EXECUTION_COMPONENT_PATH)
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    binding_paths = [getattr(args, f"binding_{index}") for index in range(3)]
    declaration = review_declaration(
        *binding_paths,
        execution_protocol_path=args.execution_protocol,
        execution_component_path=args.execution_component,
    )
    print(json.dumps(declaration, indent=2, sort_keys=True))
    return declaration


if __name__ == "__main__":  # pragma: no cover
    main()
