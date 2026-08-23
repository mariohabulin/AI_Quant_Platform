"""One-shot evidence runner for the frozen first AI Alpha candidate."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

try:
    from first_strategy_candidate import FirstStrategyCandidatePreregistration
    from research_evidence import canonical_json_bytes
    from strategy_evaluation_protocol import StrategyEvaluationProtocol
except ImportError:  # package import when src is not placed directly on sys.path
    from src.first_strategy_candidate import FirstStrategyCandidatePreregistration
    from src.research_evidence import canonical_json_bytes
    from src.strategy_evaluation_protocol import StrategyEvaluationProtocol


REPORT_SCHEMA_VERSION = 1
EVALUATION_DIRECTORY_NAME = "evaluation_v1"
STAGING_DIRECTORY_NAME = ".evaluation_v1.staging"
REPORT_FILENAME = "evaluation_report.json"
CHECKSUM_FILENAME = "evaluation_report.sha256"
EXPECTED_MANIFEST_SHA256 = (
    "6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f"
)
ALLOWED_OUTCOMES = frozenset(
    {
        "PAPER_CANDIDATE",
        "RESEARCH_HOLD",
        "REJECTED",
    }
)


@dataclass(frozen=True)
class RecordedFirstCandidateEvaluation:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    outcome: str

    def as_dict(self):
        return {
            "status": "EVALUATION_RECORDED",
            "outcome": self.outcome,
            "report_path": str(self.report_path),
            "checksum_path": str(self.checksum_path),
            "report_sha256": self.report_sha256,
            "evaluation_executed": True,
            "optimization_authorized": False,
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }


class FirstCandidateEvaluationRunner:
    """Lock, evaluate, and atomically record the first candidate once."""

    def __init__(self, preregistration=None, protocol_factory=None):
        self.preregistration = (
            preregistration
            if preregistration is not None
            else FirstStrategyCandidatePreregistration()
        )
        self.protocol_factory = (
            protocol_factory
            if protocol_factory is not None
            else StrategyEvaluationProtocol
        )

    @staticmethod
    def _paths(manifest_path):
        manifest_path = Path(manifest_path).resolve()
        parent = manifest_path.parent
        output_directory = parent / EVALUATION_DIRECTORY_NAME
        staging_directory = parent / STAGING_DIRECTORY_NAME
        return manifest_path, output_directory, staging_directory

    @staticmethod
    def _assert_not_previously_executed(output_directory, staging_directory):
        if output_directory.exists():
            raise FileExistsError(
                "First-candidate evaluation evidence already exists; refusing "
                "to overwrite or repeat the frozen evaluation."
            )
        if staging_directory.exists():
            raise FileExistsError(
                "An incomplete first-candidate evaluation staging directory "
                "exists; review it before any retry."
            )

    @staticmethod
    def _validate_protocol_report(report):
        if not isinstance(report, dict):
            raise TypeError("Strategy Evaluation Protocol must return a dictionary.")
        outcome = report.get("status")
        if outcome not in ALLOWED_OUTCOMES:
            raise ValueError(
                "Strategy Evaluation Protocol returned an unknown outcome."
            )
        if report.get("live_execution_authorized") is not False:
            raise ValueError(
                "Strategy Evaluation Protocol must explicitly deny live execution."
            )
        required_evidence = {
            "baseline_evaluation",
            "cost_stress_evaluation",
        }
        if not required_evidence.issubset(report):
            raise ValueError(
                "Strategy Evaluation Protocol report is missing baseline or stress "
                "evidence."
            )
        return outcome

    def _evaluate(self, manifest_path):
        locked = self.preregistration.lock(manifest_path)
        if locked.manifest_sha256 != EXPECTED_MANIFEST_SHA256:
            raise ValueError(
                "Manifest SHA-256 does not match the exact frozen first-candidate "
                "dataset."
            )
        protocol = self.protocol_factory(
            locked.strategy_engine,
            locked.candidate,
            locked.configuration,
        )
        protocol_report = protocol.run(locked.assets)
        outcome = self._validate_protocol_report(protocol_report)
        evidence = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "EVALUATION_COMPLETED",
            "candidate": locked.candidate.as_dict(),
            "configuration": locked.configuration.as_dict(),
            "manifest_sha256": locked.manifest_sha256,
            "protocol_report": protocol_report,
            "evaluation_executed": True,
            "optimization_authorized": False,
            "bounded_forward_paper_review_eligible": (
                outcome == "PAPER_CANDIDATE"
            ),
            "bounded_forward_paper_authorized": False,
            "live_execution_authorized": False,
        }
        return evidence, outcome

    def run(self, manifest_path):
        manifest_path, output_directory, staging_directory = self._paths(
            manifest_path
        )
        self._assert_not_previously_executed(
            output_directory,
            staging_directory,
        )

        evidence, outcome = self._evaluate(manifest_path)
        report_bytes = canonical_json_bytes(evidence)
        report_sha256 = hashlib.sha256(report_bytes).hexdigest()
        checksum_bytes = f"{report_sha256}  {REPORT_FILENAME}\n".encode("ascii")

        staging_directory.mkdir(parents=False, exist_ok=False)
        staged_report = staging_directory / REPORT_FILENAME
        staged_checksum = staging_directory / CHECKSUM_FILENAME
        staged_report.write_bytes(report_bytes)
        staged_checksum.write_bytes(checksum_bytes)
        staging_directory.rename(output_directory)

        return RecordedFirstCandidateEvaluation(
            report_path=output_directory / REPORT_FILENAME,
            checksum_path=output_directory / CHECKSUM_FILENAME,
            report_sha256=report_sha256,
            outcome=outcome,
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Execute and record the frozen first-candidate evaluation once."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to the already frozen first-candidate manifest.",
    )
    args = parser.parse_args(argv)
    recorded = FirstCandidateEvaluationRunner().run(args.manifest)
    print(json.dumps(recorded.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
