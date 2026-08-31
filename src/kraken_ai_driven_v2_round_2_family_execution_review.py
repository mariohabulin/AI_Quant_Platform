"""Hash-bound nonexecuting review for Kraken V2 Round 2 family execution."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from kraken_ai_driven_v2_round_2_causal_signals_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from kraken_ai_driven_v2_round_2_family_execution import (
        BASELINE_COST_PROFILE_ID,
        FAMILY_EXECUTION_COMPONENT_ID,
        FAMILY_ORDER,
        STRESS_COST_PROFILE_ID,
        execution_component_declaration,
        family_execution_adapters,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_round_2_causal_signals_review import (
        REVIEW_STATUS as PARENT_REVIEW_STATUS,
        review_declaration as parent_review_declaration,
    )
    from .kraken_ai_driven_v2_round_2_family_execution import (
        BASELINE_COST_PROFILE_ID,
        FAMILY_EXECUTION_COMPONENT_ID,
        FAMILY_ORDER,
        STRESS_COST_PROFILE_ID,
        execution_component_declaration,
        family_execution_adapters,
    )


SCHEMA_VERSION = 1
REVIEW_STATUS = (
    "KRAKEN_AI_V2_ROUND_2_FAMILY_EXECUTION_REVIEWED_"
    "DISCOVERY_RUNNER_REQUIRED"
)
EXECUTION_PROTOCOL_NORMALIZED_SHA256 = (
    "74b2fa5258258005a2c7ea2393d5fbd68fadf06c143a3a5b2d795d0f1fb446e9"
)
EXECUTION_COMPONENT_NORMALIZED_SHA256 = (
    "dc9b38a5819d570c8ff0405e19b10405f0516cc858bbaa9fb6a08df693733d7b"
)
COMPONENT_BINDINGS = (
    {
        "label": "AI-driven v2 Round 2 causal signals protocol",
        "path": (
            "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_"
            "ROUND_2_CAUSAL_SIGNALS_PROTOCOL_V1.md"
        ),
        "sha256": "b3ff8ff40272d4a0af0ec15f598dd127461af9f3f206de2095e39d46dcad2c6f",
    },
    {
        "label": "AI-driven v2 Round 2 causal signals component",
        "path": "src/kraken_ai_driven_v2_round_2_causal_signals.py",
        "sha256": "80cc6512bdcca299424a2d86c509121286ad45ccec63d70d9e2aa5df96e0e63e",
    },
    {
        "label": "AI-driven v2 Round 2 causal signals review",
        "path": "src/kraken_ai_driven_v2_round_2_causal_signals_review.py",
        "sha256": "3d2f60160bbfa6f356064f7a2fc7a1efb3d892c5677bb9c0654ea23b92a3b1a5",
    },
)
DEFAULT_EXECUTION_PROTOCOL_PATH = Path(
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ROUND_2_FAMILY_EXECUTION_PROTOCOL_V1.md"
)
DEFAULT_EXECUTION_COMPONENT_PATH = Path(
    "src/kraken_ai_driven_v2_round_2_family_execution.py"
)


def _normalized_text_bytes(path):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(
            f"Unable to read AI-driven v2 Round 2 family execution input: {path}"
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
            "AI-driven v2 Round 2 family execution protocol SHA256 mismatch: "
            f"{digest} != {EXECUTION_PROTOCOL_NORMALIZED_SHA256}."
        )
    text = raw.decode("utf-8")
    required = (
        "three exact family execution adapters",
        "Open priority is stop gap",
        "same-bar stop/target conflict is `STOP_FIRST`",
        "three Round 2 execution components implemented: `true`",
        "Development data opened: `false`",
        "real orders submitted: `false`",
        "3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b",
        "Candidate v2",
        "IMPLEMENT_ROUND_2_DEVELOPMENT_DISCOVERY_RUNNER",
    )
    if any(value not in text for value in required):
        raise RuntimeError(
            "AI-driven v2 Round 2 family execution required contract text "
            "is missing."
        )
    return text, digest


def _validate_parent_review(declaration):
    if declaration.get("status") != PARENT_REVIEW_STATUS:
        raise RuntimeError("Round 2 family execution parent review mismatch.")
    bindings = declaration.get("parent_source_binding_matches")
    if not isinstance(bindings, dict) or not bindings or not all(bindings.values()):
        raise RuntimeError("Round 2 family execution parent binding mismatch.")
    for field in (
        "signal_protocol_sha256_match",
        "signal_component_sha256_match",
        "parent_round_2_review_passed",
        "feature_component_implemented",
        "regime_components_implemented",
        "signal_components_implemented",
    ):
        if declaration.get(field) is not True:
            raise RuntimeError(
                f"Round 2 family execution parent mismatch for {field}."
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
                f"Round 2 family execution parent safety mismatch for {field}."
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
        "AI-driven v2 Round 2 family execution component",
    )

    reviewer = parent_reviewer or parent_review_declaration
    if not callable(reviewer):
        raise TypeError("Round 2 family execution parent reviewer must be callable.")
    parent_review = reviewer()
    _validate_parent_review(parent_review)

    component = execution_component_declaration()
    adapters = family_execution_adapters()
    if component.get("component_id") != FAMILY_EXECUTION_COMPONENT_ID:
        raise RuntimeError("Round 2 family execution component ID mismatch.")
    if tuple(component.get("family_order", ())) != FAMILY_ORDER:
        raise RuntimeError("Round 2 family execution order mismatch.")
    if tuple(adapters) != FAMILY_ORDER:
        raise RuntimeError("Round 2 family adapter order mismatch.")
    for field in (
        "family_execution_components_implemented",
        "baseline_cost_profile_implemented",
        "stress_cost_profile_implemented",
        "shared_safety_envelope_implemented",
        "protective_execution_implemented",
    ):
        if component.get(field) is not True:
            raise RuntimeError(
                f"Round 2 family execution component mismatch for {field}."
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
                f"Round 2 family execution safety mismatch for {field}."
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": REVIEW_STATUS,
        "component_id": FAMILY_EXECUTION_COMPONENT_ID,
        "round_2_configuration_sha256": component[
            "round_2_configuration_sha256"
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
        "next_stage": "IMPLEMENT_ROUND_2_DEVELOPMENT_DISCOVERY_RUNNER",
    }


def _parser():
    parser = argparse.ArgumentParser(
        description="Review nonexecuting Kraken V2 Round 2 family execution."
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
