from dataclasses import dataclass

from src.replay_consistency import ReplayConsistencyReport


_ALLOWED_CLASSIFICATIONS = {"MATCH", "INTENDED", "DEFECT", "CONFIGURATION_MISMATCH"}


@dataclass(frozen=True)
class ReadinessScenario:
    name: str
    validator: object
    data: object
    stop_resolver: object = None
    target_resolver: object = None
    expected_difference_fields: tuple = ()
    divergence_classification: str = "DEFECT"


@dataclass(frozen=True)
class ReadinessEvidence:
    name: str
    classification: str
    gate_passed: bool
    report: ReplayConsistencyReport
    unexpected_difference_fields: tuple


@dataclass(frozen=True)
class PaperReadinessReport:
    status: str
    evidence: tuple

    @property
    def is_ready(self):
        return self.status == "READY"

    @property
    def blocking_evidence(self):
        return tuple(item for item in self.evidence if not item.gate_passed)


class PaperReadinessGate:
    """Turn replay-consistency diagnostics into explicit readiness evidence.

    The gate never hides divergence. A scenario passes only when it is fully
    consistent, or when every observed difference was explicitly expected and
    classified as an intended semantic difference. Defects and configuration
    mismatches remain blocking evidence.
    """

    def __init__(self, scenarios):
        scenarios = tuple(scenarios)
        if not scenarios:
            raise ValueError("At least one readiness scenario is required.")
        names = [scenario.name for scenario in scenarios]
        if any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("Every readiness scenario requires a non-empty name.")
        if len(set(names)) != len(names):
            raise ValueError("Readiness scenario names must be unique.")
        for scenario in scenarios:
            if scenario.divergence_classification not in _ALLOWED_CLASSIFICATIONS - {"MATCH"}:
                raise ValueError("Invalid divergence classification.")
        self.scenarios = scenarios

    @staticmethod
    def _evaluate(scenario, report):
        observed = {difference.field for difference in report.differences}
        expected = set(scenario.expected_difference_fields)
        unexpected = tuple(sorted(observed - expected))

        if report.is_consistent:
            classification = "MATCH"
            gate_passed = not expected
        else:
            classification = scenario.divergence_classification
            gate_passed = (
                classification == "INTENDED"
                and not unexpected
                and observed == expected
            )

        return ReadinessEvidence(
            name=scenario.name,
            classification=classification,
            gate_passed=gate_passed,
            report=report,
            unexpected_difference_fields=unexpected,
        )

    def run(self):
        evidence = []
        for scenario in self.scenarios:
            report = scenario.validator.run(
                scenario.data,
                stop_resolver=scenario.stop_resolver,
                target_resolver=scenario.target_resolver,
            )
            evidence.append(self._evaluate(scenario, report))

        evidence = tuple(evidence)
        status = "READY" if all(item.gate_passed for item in evidence) else "BLOCKED"
        return PaperReadinessReport(status=status, evidence=evidence)
