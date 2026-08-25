"""Immutable boundary for trend-pullback and volume re-expansion research."""

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from numbers import Real
from pathlib import Path
import re

try:
    from alpha_discovery_protocol import (
        ALPHA_DISCOVERY_ID,
        ASSET_SCOPE,
        PARAMETER_SET_ORDER as CLOSED_DISCOVERY_PARAMETER_ORDER,
        parameter_catalog_fingerprint as closed_discovery_catalog_fingerprint,
    )
    from coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from research_evidence import canonical_json_bytes
    from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
except ImportError:  # package import when src is not placed directly on sys.path
    from src.alpha_discovery_protocol import (
        ALPHA_DISCOVERY_ID,
        ASSET_SCOPE,
        PARAMETER_SET_ORDER as CLOSED_DISCOVERY_PARAMETER_ORDER,
        parameter_catalog_fingerprint as closed_discovery_catalog_fingerprint,
    )
    from src.coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from src.research_evidence import canonical_json_bytes
    from src.strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256


TREND_PULLBACK_PROTOCOL_SCHEMA_VERSION = 1
TREND_PULLBACK_DEVELOPMENT_ID = (
    "ema-pullback-volume-reexpansion-btc-eth-6h-development-v1"
)
RECORDED_ALPHA_DISCOVERY_REPORT_SHA256 = (
    "2fc8f4d1a5d690c072408bc2d299516904feb58b2e2f40345983641bf26ed678"
)
PULLBACK_PARAMETER_CATALOG_VERSION = "trend-pullback-volume-bounded-catalog-v1"
EXPECTED_DISCOVERY_FAILED_GATES = frozenset(
    {
        "at_least_one_selected_window",
        "positive_baseline_median_return_both_assets",
        "baseline_outer_persistence",
        "stress_outer_persistence",
    }
)
EXPECTED_INNER_GATE_COUNTS = {
    "annual_baseline_cost_within_budget": {"pass": 56, "fail": 0},
    "annual_turnover_within_budget": {"pass": 56, "fail": 0},
    "baseline_inner_persistence": {"pass": 0, "fail": 56},
    "drawdown_within_limit": {"pass": 56, "fail": 0},
    "minimum_inner_trades": {"pass": 56, "fail": 0},
    "nonnegative_stress_median_return_both_assets": {"pass": 0, "fail": 56},
    "positive_baseline_median_return_both_assets": {"pass": 5, "fail": 51},
    "protective_policy_active": {"pass": 56, "fail": 0},
    "stress_inner_persistence": {"pass": 0, "fail": 56},
}


def _validated_sha256(value, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(
            f"{name} must be exactly 64 lowercase hexadecimal characters."
        )
    return value


def _finite(value, name, *, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    if maximum is not None and result > maximum:
        raise ValueError(f"{name} must be at most {maximum}.")
    return result


def _positive_integer(value, name):
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


@dataclass(frozen=True)
class TrendPullbackVolumeParameterSet:
    """One exact entry-timing member of the four-member development catalog."""

    parameter_set_id: str
    pullback_distance_atr: float
    trigger_relative_volume: float
    adx_period: int = 14
    atr_period: int = 14
    prior_adx_confirmation: float = 25.0
    current_adx_floor: float = 20.0
    adx_exit_threshold: float = 15.0
    setup_lookback_bars: int = 8
    volume_lookback: int = 20
    volume_baseline_lag: int = 1
    pullback_relative_volume_ceiling: float = 1.0
    ema_fast_period: int = 50
    ema_slow_period: int = 200
    ema_slope_lookback: int = 4
    initial_stop_atr: float = 2.0
    reward_risk_ratio: float = 3.0
    cooldown_bars: int = 4

    def __post_init__(self):
        if not isinstance(self.parameter_set_id, str) or not re.fullmatch(
            r"pb(0p5|1p0)-rv(1p2|1p5)-2atr-static3r",
            self.parameter_set_id,
        ):
            raise ValueError("Parameter-set ID is not part of catalog v1 syntax.")
        pullback = _finite(
            self.pullback_distance_atr,
            "Pullback distance ATR",
            minimum=0.1,
        )
        trigger_volume = _finite(
            self.trigger_relative_volume,
            "Trigger relative volume",
            minimum=1.0,
        )
        if pullback not in (0.5, 1.0):
            raise ValueError("Catalog v1 permits only 0.5 or 1.0 ATR pullbacks.")
        if trigger_volume not in (1.2, 1.5):
            raise ValueError("Catalog v1 permits only 1.2 or 1.5 trigger volume.")
        for value, name in (
            (self.adx_period, "ADX period"),
            (self.atr_period, "ATR period"),
            (self.setup_lookback_bars, "Setup lookback"),
            (self.volume_lookback, "Volume lookback"),
            (self.volume_baseline_lag, "Volume baseline lag"),
            (self.ema_fast_period, "Fast EMA period"),
            (self.ema_slow_period, "Slow EMA period"),
            (self.ema_slope_lookback, "EMA slope lookback"),
            (self.cooldown_bars, "Cooldown bars"),
        ):
            _positive_integer(value, name)
        for value, name in (
            (self.prior_adx_confirmation, "Prior ADX confirmation"),
            (self.current_adx_floor, "Current ADX floor"),
            (self.adx_exit_threshold, "ADX exit threshold"),
            (
                self.pullback_relative_volume_ceiling,
                "Pullback relative-volume ceiling",
            ),
            (self.initial_stop_atr, "Initial stop ATR"),
            (self.reward_risk_ratio, "Reward/risk ratio"),
        ):
            _finite(value, name, minimum=0.0)
        if not (
            self.adx_exit_threshold
            < self.current_adx_floor
            < self.prior_adx_confirmation
        ):
            raise ValueError("ADX confirmation, floor and exit order changed.")
        if self.volume_baseline_lag != 1:
            raise ValueError("Volume baseline must remain lagged by one bar.")
        if self.pullback_relative_volume_ceiling != 1.0:
            raise ValueError("Pullback volume ceiling must remain 1.0.")
        if self.ema_fast_period >= self.ema_slow_period:
            raise ValueError("Fast EMA period must be below slow EMA period.")
        if self.initial_stop_atr != 2.0 or self.reward_risk_ratio != 3.0:
            raise ValueError("Catalog v1 preserves 2 ATR risk and a 3R target.")
        expected_id = (
            f"pb{'0p5' if pullback == 0.5 else '1p0'}-"
            f"rv{'1p2' if trigger_volume == 1.2 else '1p5'}-"
            "2atr-static3r"
        )
        if self.parameter_set_id != expected_id:
            raise ValueError("Parameter-set ID does not match frozen values.")

    def as_dict(self):
        result = asdict(self)
        result.update(
            {
                "direction": "LONG_ONLY",
                "trend_structure": (
                    "CLOSE_ABOVE_EMA_200_AND_EMA_50_POSITIVE_SLOPE"
                ),
                "setup": (
                    "PULLBACK_WITHIN_ATR_DISTANCE_OF_EMA_50_ON_"
                    "CONTRACTING_OR_NORMAL_RELATIVE_VOLUME"
                ),
                "prior_strength": (
                    "ADX_REACHED_25_WITHIN_PRIOR_EIGHT_COMPLETED_BARS"
                ),
                "trigger": (
                    "CLOSE_ABOVE_PREVIOUS_HIGH_AND_EMA_50_WITH_VOLUME_"
                    "REEXPANSION_PLUS_DI_ABOVE_MINUS_DI"
                ),
                "entry_execution": "NEXT_BAR_OPEN",
                "signal_exit": (
                    "CLOSE_BELOW_EMA_50_OR_ADX_BELOW_15_OR_PLUS_DI_NOT_ABOVE_MINUS_DI"
                ),
                "protective_management": "STATIC_2ATR_STOP_AND_3R_TARGET",
                "obv_role": "DIAGNOSTIC_ONLY_NOT_ENTRY_GATE",
            }
        )
        return result


def trend_pullback_parameter_catalog():
    catalog = []
    for pullback, pullback_id in ((0.5, "0p5"), (1.0, "1p0")):
        for volume, volume_id in ((1.2, "1p2"), (1.5, "1p5")):
            catalog.append(
                TrendPullbackVolumeParameterSet(
                    parameter_set_id=(
                        f"pb{pullback_id}-rv{volume_id}-2atr-static3r"
                    ),
                    pullback_distance_atr=pullback,
                    trigger_relative_volume=volume,
                )
            )
    return tuple(catalog)


TREND_PULLBACK_PARAMETER_CATALOG = trend_pullback_parameter_catalog()
TREND_PULLBACK_PARAMETER_ORDER = tuple(
    item.parameter_set_id for item in TREND_PULLBACK_PARAMETER_CATALOG
)
TREND_PULLBACK_PARAMETER_CATALOG_SHA256 = (
    "952046ddb7a9f9a85a8976f3ccafe43a017a745c887e592a44c39c2146ba8e00"
)


def trend_pullback_catalog_fingerprint(catalog=TREND_PULLBACK_PARAMETER_CATALOG):
    payload = {
        "catalog_version": PULLBACK_PARAMETER_CATALOG_VERSION,
        "parameter_sets": [item.as_dict() for item in catalog],
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def trend_pullback_configuration():
    if (
        trend_pullback_catalog_fingerprint()
        != TREND_PULLBACK_PARAMETER_CATALOG_SHA256
    ):
        raise ValueError("Trend-pullback parameter catalog identity changed.")
    return {
        "hypothesis": (
            "Within a causal bullish trend, a controlled EMA-50 pullback on "
            "contracting or normal relative volume followed by price recovery "
            "and renewed volume expansion will be more persistent after costs "
            "than entering an already-developed high-volume ADX impulse."
        ),
        "parameter_catalog_version": PULLBACK_PARAMETER_CATALOG_VERSION,
        "parameter_catalog_sha256": TREND_PULLBACK_PARAMETER_CATALOG_SHA256,
        "parameter_set_order": list(TREND_PULLBACK_PARAMETER_ORDER),
        "parameter_sets": [
            item.as_dict() for item in TREND_PULLBACK_PARAMETER_CATALOG
        ],
        "causal_setup_state": {
            "observation": "COMPLETED_BARS_ONLY",
            "setup_expiry_bars": 8,
            "pullback_volume_role": "CONTRACTION_OR_NORMAL",
            "trigger_volume_role": "REEXPANSION",
            "entry_execution": "FOLLOWING_BAR_OPEN",
            "future_bar_access": False,
        },
        "risk_and_exit": {
            "risk_per_trade_fraction": 0.005,
            "maximum_position_fraction": 0.50,
            "initial_stop_atr": 2.0,
            "reward_risk_ratio": 3.0,
            "breakeven_enabled": False,
            "leverage": "NONE",
            "shorting": False,
        },
        "future_runner_boundary": {
            "outer_train_size": 5760,
            "outer_test_size": 720,
            "outer_step_size": 720,
            "inner_train_size": 2880,
            "inner_validation_size": 720,
            "inner_step_size": 720,
            "max_recent_inner_windows": 4,
            "minimum_positive_inner_window_rate": 0.60,
            "minimum_inner_trades_per_asset": 12,
            "maximum_drawdown_percent": 20.0,
            "maximum_annual_turnover_multiple": 12.0,
            "maximum_annual_baseline_cost_fraction": 0.10,
            "selection_profiles": ["COINBASE_BASELINE", "COINBASE_STRESS"],
            "selection_assets": list(ASSET_SCOPE),
            "no_eligible_configuration_action": "HOLD_CASH",
            "outer_test_available_to_selection": False,
            "global_hindsight_leaderboard": "PROHIBITED",
        },
        "implementation_prerequisites": {
            "causal_setup_state_machine": "REQUIRED_SEPARATE_REVIEW",
            "pullback_volume_strategy": "REQUIRED_SEPARATE_REVIEW",
            "nested_runner": "REQUIRED_SEPARATE_REVIEW",
            "status": "PROTOCOL_ONLY_NOT_EXECUTABLE",
        },
        "future_validation": {
            "development_data_role": "INSPECTED_DEVELOPMENT_ONLY",
            "candidate_v2_created": False,
            "genuinely_unseen_data_required_after_development": True,
        },
    }


def _required_boolean(payload, name, expected):
    if payload.get(name) is not expected:
        raise ValueError(f"Recorded Alpha Discovery {name} is invalid.")


def _inner_gate_counts(payload):
    counts = {
        name: {"pass": 0, "fail": 0}
        for name in EXPECTED_INNER_GATE_COUNTS
    }
    windows = payload.get("nested_calibration", {}).get("outer_windows")
    if not isinstance(windows, list) or len(windows) != 7:
        raise ValueError("Recorded Alpha Discovery outer-window count changed.")
    for window in windows:
        selection = window.get("selection", {})
        records = selection.get("records")
        if (
            selection.get("status") != "NO_ELIGIBLE_CONFIGURATION_HOLD_CASH"
            or selection.get("selected_parameter_set_id") is not None
            or selection.get("hold_cash") is not True
            or selection.get("outer_test_evidence_used") is not False
            or not isinstance(records, dict)
            or tuple(sorted(records))
            != tuple(sorted(CLOSED_DISCOVERY_PARAMETER_ORDER))
        ):
            raise ValueError("Recorded Alpha Discovery selection basis changed.")
        outer = window.get("outer_evaluation")
        if outer != {"action": "HOLD_CASH", "parameter_set_id": None, "profiles": {}}:
            raise ValueError("Recorded Alpha Discovery outer action changed.")
        for record in records.values():
            if record.get("eligible") is not False:
                raise ValueError("Recorded Alpha Discovery retained a parameter.")
            gates = record.get("gates")
            if not isinstance(gates, dict) or set(gates) != set(counts):
                raise ValueError("Recorded Alpha Discovery gate scope changed.")
            for name, passed in gates.items():
                if not isinstance(passed, bool):
                    raise ValueError("Recorded Alpha Discovery gate is not boolean.")
                counts[name]["pass" if passed else "fail"] += 1
    return counts


def _validate_recorded_discovery(payload):
    if (
        payload.get("schema_version") != 1
        or payload.get("status") != "ALPHA_DISCOVERY_COMPLETED"
        or payload.get("alpha_discovery_id") != ALPHA_DISCOVERY_ID
        or payload.get("manifest_sha256") != DEVELOPMENT_MANIFEST_SHA256
        or payload.get("parameter_catalog_sha256")
        != closed_discovery_catalog_fingerprint()
        or payload.get("parameter_set_order")
        != list(CLOSED_DISCOVERY_PARAMETER_ORDER)
        or payload.get("dataset_role") != "INSPECTED_DEVELOPMENT_ONLY"
        or payload.get("development_data_only") is not True
    ):
        raise ValueError("Recorded Alpha Discovery identity is invalid.")
    for name, expected in (
        ("zero_cost_diagnostic_executed", True),
        ("trade_path_analysis_executed", True),
        ("nested_calibration_executed", True),
        ("outer_development_test_executed", True),
        ("parameter_selection_executed", True),
        ("global_hindsight_leaderboard_generated", False),
        ("formal_candidate_evaluation", False),
        ("candidate_v2_authorized", False),
        ("optimization_authorized", False),
        ("bounded_forward_paper_review_eligible", False),
        ("bounded_forward_paper_authorized", False),
        ("live_execution_authorized", False),
    ):
        _required_boolean(payload, name, expected)
    review = payload.get("adaptive_review")
    if (
        not isinstance(review, dict)
        or review.get("outcome") != "SCREEN_OUT"
        or review.get("selected_outer_windows") != 0
        or review.get("hold_cash_outer_windows") != 7
        or set(review.get("failed_gates", [])) != EXPECTED_DISCOVERY_FAILED_GATES
    ):
        raise ValueError("Recorded Alpha Discovery review basis is invalid.")
    if _inner_gate_counts(payload) != EXPECTED_INNER_GATE_COUNTS:
        raise ValueError("Recorded Alpha Discovery inner-gate counts changed.")
    diagnostic = payload.get("diagnostic")
    if (
        not isinstance(diagnostic, dict)
        or diagnostic.get("status")
        != "ZERO_COST_TRADE_PATH_DIAGNOSTIC_COMPLETED"
        or diagnostic.get("zero_cost_may_select_parameters") is not False
        or diagnostic.get("raw_trade_paths_persisted") is not False
    ):
        raise ValueError("Recorded Alpha Discovery diagnostic basis is invalid.")


def load_recorded_alpha_discovery_report(report_path, expected_sha256=None):
    report_path = Path(report_path)
    if report_path.name != "alpha_discovery_report.json":
        raise ValueError("Alpha Discovery report filename is invalid.")
    report_bytes = report_path.read_bytes()
    digest = hashlib.sha256(report_bytes).hexdigest()
    expected = _validated_sha256(
        expected_sha256 or RECORDED_ALPHA_DISCOVERY_REPORT_SHA256,
        "Expected Alpha Discovery report SHA-256",
    )
    if digest != expected:
        raise ValueError("Alpha Discovery report SHA-256 changed.")
    checksum_path = report_path.with_name("alpha_discovery_report.sha256")
    expected_checksum = f"{digest}  {report_path.name}\n".encode("ascii")
    if checksum_path.read_bytes() != expected_checksum:
        raise ValueError("Alpha Discovery report checksum is invalid.")
    try:
        payload = json.loads(report_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Alpha Discovery report is not valid JSON.") from exc
    if canonical_json_bytes(payload) != report_bytes:
        raise ValueError("Alpha Discovery report is not canonical JSON.")
    _validate_recorded_discovery(payload)
    return payload, digest


@dataclass(frozen=True)
class LockedTrendPullbackDevelopment:
    contract: CoinbaseResearchDatasetContract
    assets: dict
    manifest_sha256: str
    alpha_discovery_report: dict
    alpha_discovery_report_sha256: str
    configuration: dict


def _safety_boundary():
    return {
        "performance_evaluation_executed": False,
        "parameter_calibration_executed": False,
        "parameter_selection_executed": False,
        "optimization_authorized": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


class TrendPullbackVolumePreregistration:
    """Bind the new hypothesis only to exact closed development evidence."""

    def __init__(
        self,
        contract=FIRST_CANDIDATE_DATASET_CONTRACT,
        required_manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
        required_discovery_report_sha256=(
            RECORDED_ALPHA_DISCOVERY_REPORT_SHA256
        ),
        dataset_lock=None,
        discovery_report_loader=load_recorded_alpha_discovery_report,
    ):
        if not isinstance(contract, CoinbaseResearchDatasetContract):
            raise TypeError("Contract must be a CoinbaseResearchDatasetContract.")
        if not callable(discovery_report_loader):
            raise TypeError("Discovery report loader must be callable.")
        self.contract = contract
        self.required_manifest_sha256 = _validated_sha256(
            required_manifest_sha256, "Required manifest SHA-256"
        )
        self.required_discovery_report_sha256 = _validated_sha256(
            required_discovery_report_sha256,
            "Required Alpha Discovery report SHA-256",
        )
        self.dataset_lock = dataset_lock or CoinbaseResearchDatasetLock(contract)
        self.discovery_report_loader = discovery_report_loader

    def declaration(self):
        return {
            "schema_version": TREND_PULLBACK_PROTOCOL_SCHEMA_VERSION,
            "status": "TREND_PULLBACK_VOLUME_EVIDENCE_LOCK_PENDING",
            "development_id": TREND_PULLBACK_DEVELOPMENT_ID,
            "purpose": "STRUCTURALLY_NEW_DEVELOPMENT_HYPOTHESIS_NOT_CANDIDATE_V2",
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": self.contract.timeframe,
            "assets": list(self.contract.products),
            "required_manifest_sha256": self.required_manifest_sha256,
            "required_alpha_discovery_report_sha256": (
                self.required_discovery_report_sha256
            ),
            "configuration": trend_pullback_configuration(),
            "implementation_prerequisites_satisfied": False,
            "runner_execution_authorized": False,
            **_safety_boundary(),
        }

    def lock(self, manifest_path, discovery_report_path):
        dataset = self.dataset_lock.lock(manifest_path)
        if dataset.manifest_sha256 != self.required_manifest_sha256:
            raise ValueError("Dataset does not match the frozen manifest.")
        payload, digest = self.discovery_report_loader(
            discovery_report_path,
            expected_sha256=self.required_discovery_report_sha256,
        )
        if payload.get("manifest_sha256") != dataset.manifest_sha256:
            raise ValueError("Discovery evidence and dataset manifest do not match.")
        if tuple(sorted(dataset.assets)) != tuple(self.contract.products):
            raise ValueError("Locked asset scope does not match development scope.")
        return LockedTrendPullbackDevelopment(
            contract=self.contract,
            assets=dataset.assets,
            manifest_sha256=dataset.manifest_sha256,
            alpha_discovery_report=payload,
            alpha_discovery_report_sha256=digest,
            configuration=trend_pullback_configuration(),
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Declare or evidence-lock Trend Pullback and Volume Re-expansion "
            "Protocol v1 without evaluating performance."
        )
    )
    parser.add_argument("--manifest", help="Exact frozen six-hour manifest.")
    parser.add_argument(
        "--discovery-report", help="Exact closed Alpha Discovery v1 report."
    )
    args = parser.parse_args(argv)
    if bool(args.manifest) != bool(args.discovery_report):
        parser.error("--manifest and --discovery-report must be supplied together.")

    preregistration = TrendPullbackVolumePreregistration()
    if args.manifest:
        locked = preregistration.lock(args.manifest, args.discovery_report)
        result = {
            "schema_version": TREND_PULLBACK_PROTOCOL_SCHEMA_VERSION,
            "status": "TREND_PULLBACK_VOLUME_EVIDENCE_LOCKED",
            "development_id": TREND_PULLBACK_DEVELOPMENT_ID,
            "manifest_sha256": locked.manifest_sha256,
            "alpha_discovery_report_sha256": (
                locked.alpha_discovery_report_sha256
            ),
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": locked.contract.timeframe,
            "assets": list(locked.contract.products),
            "asset_rows": {
                name: len(frame) for name, frame in sorted(locked.assets.items())
            },
            "parameter_set_order": list(TREND_PULLBACK_PARAMETER_ORDER),
            "parameter_catalog_sha256": (
                TREND_PULLBACK_PARAMETER_CATALOG_SHA256
            ),
            "configuration": locked.configuration,
            "implementation_prerequisites_satisfied": False,
            "runner_execution_authorized": False,
            **_safety_boundary(),
        }
    else:
        result = preregistration.declaration()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
