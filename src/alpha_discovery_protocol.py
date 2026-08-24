"""Immutable boundary for bounded alpha discovery and nested calibration."""

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from numbers import Real
from pathlib import Path
import re

try:
    from alpha_development_protocol import (
        ALPHA_DEVELOPMENT_ID,
        VARIANT_ORDER,
    )
    from coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from research_evidence import canonical_json_bytes
    from strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256
except ImportError:  # package import when src is not placed directly on sys.path
    from src.alpha_development_protocol import (
        ALPHA_DEVELOPMENT_ID,
        VARIANT_ORDER,
    )
    from src.coinbase_research_dataset import (
        FIRST_CANDIDATE_DATASET_CONTRACT,
        CoinbaseResearchDatasetContract,
        CoinbaseResearchDatasetLock,
    )
    from src.research_evidence import canonical_json_bytes
    from src.strategy_family_screening import DEVELOPMENT_MANIFEST_SHA256


ALPHA_DISCOVERY_SCHEMA_VERSION = 1
ALPHA_DISCOVERY_ID = "regime-volume-trend-nested-calibration-development-v1"
RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256 = (
    "19627f7002fc3159729ea61d22ead0fa25deca455612764121ea96fd3eaf71a0"
)
PARAMETER_CATALOG_VERSION = "alpha-discovery-bounded-catalog-v1"
ASSET_SCOPE = ("BTC-USD", "ETH-USD")
EXPECTED_FAILED_DEVELOPMENT_GATES = frozenset(
    {
        "baseline_multi_asset_validated",
        "cost_stress_multi_asset_validated",
        "baseline_positive_oos_return_both_assets",
    }
)


def _validated_sha256(value, name):
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(
            f"{name} must be exactly 64 lowercase hexadecimal characters."
        )
    return value


def _finite_number(value, name, *, minimum=None, maximum=None):
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
class AlphaCalibrationParameterSet:
    """One member of the complete, pre-declared calibration catalog."""

    parameter_set_id: str
    adx_entry_threshold: float
    adx_exit_threshold: float
    atr_risk_distance_multiple: float
    breakeven_trigger_r: float | None
    reward_risk_ratio: float = 3.0
    adx_period: int = 14
    atr_period: int = 14
    cooldown_bars: int = 4
    required_market_regime: str = "BULLISH_NORMAL"
    required_volume_regime: str = "HIGH"
    volume_lookback: int = 20
    volume_baseline_lag: int = 1
    ema_fast_period: int = 50
    ema_slow_period: int = 200
    ema_slope_lookback: int = 4

    def __post_init__(self):
        if not isinstance(self.parameter_set_id, str) or not re.fullmatch(
            r"adx(20-15|25-20)-atr(1p5|2p0)-(static3r|be1r3r)",
            self.parameter_set_id,
        ):
            raise ValueError("Parameter-set ID is not part of catalog v1 syntax.")
        entry = _finite_number(
            self.adx_entry_threshold, "ADX entry threshold", minimum=1.0
        )
        exit_value = _finite_number(
            self.adx_exit_threshold, "ADX exit threshold", minimum=0.0
        )
        if exit_value >= entry:
            raise ValueError("ADX exit threshold must be below entry threshold.")
        if (entry, exit_value) not in ((20.0, 15.0), (25.0, 20.0)):
            raise ValueError("Catalog v1 permits only two frozen ADX bands.")
        atr_multiple = _finite_number(
            self.atr_risk_distance_multiple,
            "ATR risk-distance multiple",
            minimum=0.1,
        )
        if atr_multiple not in (1.5, 2.0):
            raise ValueError("Catalog v1 permits only 1.5 or 2.0 ATR risk.")
        if self.breakeven_trigger_r is not None:
            breakeven = _finite_number(
                self.breakeven_trigger_r,
                "Break-even trigger",
                minimum=0.1,
            )
            if breakeven != 1.0:
                raise ValueError("Catalog v1 permits only a 1R break-even trigger.")
        reward = _finite_number(
            self.reward_risk_ratio, "Reward/risk ratio", minimum=1.0
        )
        if reward != 3.0:
            raise ValueError("Catalog v1 preserves the frozen 3:1 target.")
        for value, name in (
            (self.adx_period, "ADX period"),
            (self.atr_period, "ATR period"),
            (self.cooldown_bars, "Cooldown bars"),
            (self.volume_lookback, "Volume lookback"),
            (self.volume_baseline_lag, "Volume baseline lag"),
            (self.ema_fast_period, "Fast EMA period"),
            (self.ema_slow_period, "Slow EMA period"),
            (self.ema_slope_lookback, "EMA slope lookback"),
        ):
            _positive_integer(value, name)
        if self.ema_fast_period >= self.ema_slow_period:
            raise ValueError("Fast EMA period must be below slow EMA period.")
        if self.required_market_regime != "BULLISH_NORMAL":
            raise ValueError("Catalog v1 requires the BULLISH_NORMAL regime.")
        if self.required_volume_regime != "HIGH":
            raise ValueError("Catalog v1 requires causal HIGH relative volume.")
        if self.volume_baseline_lag != 1:
            raise ValueError("Volume baseline must remain lagged by one bar.")
        expected_id = (
            f"adx{int(entry)}-{int(exit_value)}-"
            f"atr{'1p5' if atr_multiple == 1.5 else '2p0'}-"
            f"{'static3r' if self.breakeven_trigger_r is None else 'be1r3r'}"
        )
        if self.parameter_set_id != expected_id:
            raise ValueError("Parameter-set ID does not match its frozen values.")

    def as_dict(self):
        result = asdict(self)
        result.update(
            {
                "direction": "LONG_ONLY",
                "entry_execution": "NEXT_BAR_OPEN",
                "volume_exit_gate": "NONE_ENTRY_CONFIRMATION_ONLY",
                "trend_structure": (
                    "CLOSE_ABOVE_EMA_200_AND_EMA_50_POSITIVE_SLOPE"
                ),
                "obv_role": "DIAGNOSTIC_ONLY_NOT_ENTRY_GATE",
                "target_policy": "STATIC_3R",
                "breakeven_policy": (
                    "DISABLED"
                    if self.breakeven_trigger_r is None
                    else "MOVE_STOP_TO_ENTRY_AFTER_1R_ON_COMPLETED_BAR"
                ),
            }
        )
        return result


def alpha_calibration_parameter_catalog():
    """Return the complete ordered eight-member catalog; no hidden grid."""

    catalog = []
    for entry, exit_value, adx_id in (
        (20.0, 15.0, "20-15"),
        (25.0, 20.0, "25-20"),
    ):
        for atr_multiple, atr_id in ((1.5, "1p5"), (2.0, "2p0")):
            for breakeven, exit_id in (
                (None, "static3r"),
                (1.0, "be1r3r"),
            ):
                catalog.append(
                    AlphaCalibrationParameterSet(
                        parameter_set_id=(
                            f"adx{adx_id}-atr{atr_id}-{exit_id}"
                        ),
                        adx_entry_threshold=entry,
                        adx_exit_threshold=exit_value,
                        atr_risk_distance_multiple=atr_multiple,
                        breakeven_trigger_r=breakeven,
                    )
                )
    return tuple(catalog)


CALIBRATION_PARAMETER_CATALOG = alpha_calibration_parameter_catalog()
PARAMETER_SET_ORDER = tuple(
    parameter.parameter_set_id for parameter in CALIBRATION_PARAMETER_CATALOG
)


def parameter_catalog_fingerprint(catalog=CALIBRATION_PARAMETER_CATALOG):
    payload = {
        "catalog_version": PARAMETER_CATALOG_VERSION,
        "parameter_sets": [parameter.as_dict() for parameter in catalog],
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class NestedCalibrationConfig:
    """Frozen outer-test and inner-selection boundaries in six-hour bars."""

    outer_train_size: int = 5760
    outer_test_size: int = 720
    outer_step_size: int = 720
    inner_train_size: int = 2880
    inner_validation_size: int = 720
    inner_step_size: int = 720
    max_recent_inner_windows: int = 4
    minimum_outer_windows: int = 5
    minimum_inner_trades_per_asset: int = 12
    minimum_positive_inner_window_rate: float = 0.60
    maximum_drawdown_percent: float = 20.0
    maximum_annual_turnover_multiple: float = 12.0
    maximum_annual_baseline_cost_fraction: float = 0.10

    def __post_init__(self):
        for value, name in (
            (self.outer_train_size, "Outer train size"),
            (self.outer_test_size, "Outer test size"),
            (self.outer_step_size, "Outer step size"),
            (self.inner_train_size, "Inner train size"),
            (self.inner_validation_size, "Inner validation size"),
            (self.inner_step_size, "Inner step size"),
            (self.max_recent_inner_windows, "Maximum recent inner windows"),
            (self.minimum_outer_windows, "Minimum outer windows"),
            (
                self.minimum_inner_trades_per_asset,
                "Minimum inner trades per asset",
            ),
        ):
            _positive_integer(value, name)
        if self.outer_step_size < self.outer_test_size:
            raise ValueError("Outer test windows must not overlap.")
        if self.inner_step_size < self.inner_validation_size:
            raise ValueError("Inner validation windows must not overlap.")
        if self.inner_train_size + self.inner_validation_size > (
            self.outer_train_size
        ):
            raise ValueError("Initial outer train cannot contain an inner window.")
        _finite_number(
            self.minimum_positive_inner_window_rate,
            "Minimum positive inner-window rate",
            minimum=0.0,
            maximum=1.0,
        )
        _finite_number(
            self.maximum_drawdown_percent,
            "Maximum drawdown percent",
            minimum=0.0,
            maximum=100.0,
        )
        _finite_number(
            self.maximum_annual_turnover_multiple,
            "Maximum annual turnover multiple",
            minimum=0.0,
        )
        _finite_number(
            self.maximum_annual_baseline_cost_fraction,
            "Maximum annual baseline-cost fraction",
            minimum=0.0,
            maximum=1.0,
        )

    def as_dict(self):
        return asdict(self)


class NestedCalibrationPlanner:
    """Create expanding nested windows without inspecting any market values."""

    def __init__(self, configuration=None):
        self.configuration = configuration or NestedCalibrationConfig()
        if not isinstance(self.configuration, NestedCalibrationConfig):
            raise TypeError("Configuration must be NestedCalibrationConfig.")

    def _inner_windows(self, outer_train_end):
        config = self.configuration
        windows = []
        validation_start = config.inner_train_size
        while validation_start + config.inner_validation_size <= outer_train_end:
            windows.append(
                {
                    "inner_train_start": 0,
                    "inner_train_end": validation_start,
                    "inner_validation_start": validation_start,
                    "inner_validation_end": (
                        validation_start + config.inner_validation_size
                    ),
                }
            )
            validation_start += config.inner_step_size
        return windows[-config.max_recent_inner_windows :]

    def plan(self, total_rows):
        _positive_integer(total_rows, "Total rows")
        config = self.configuration
        windows = []
        outer_train_end = config.outer_train_size
        while outer_train_end + config.outer_test_size <= total_rows:
            inner = self._inner_windows(outer_train_end)
            if len(inner) != config.max_recent_inner_windows:
                raise ValueError(
                    "Every outer window must contain the frozen inner-window count."
                )
            windows.append(
                {
                    "outer_window": len(windows),
                    "outer_train_start": 0,
                    "outer_train_end": outer_train_end,
                    "selection_cutoff": outer_train_end,
                    "outer_test_start": outer_train_end,
                    "outer_test_end": outer_train_end + config.outer_test_size,
                    "inner_windows": inner,
                    "outer_test_available_to_selection": False,
                }
            )
            outer_train_end += config.outer_step_size
        if len(windows) < config.minimum_outer_windows:
            raise ValueError("Dataset does not provide minimum outer coverage.")
        return {
            "total_rows": total_rows,
            "outer_window_count": len(windows),
            "windows": windows,
            "unused_terminal_rows": total_rows - windows[-1]["outer_test_end"],
            "selection_scope": "INNER_VALIDATION_ONLY",
            "outer_test_used_for_selection": False,
        }


INNER_ASSET_METRICS = frozenset(
    {
        "baseline_median_net_return",
        "stress_median_net_return",
        "baseline_positive_window_rate",
        "stress_positive_window_rate",
        "maximum_drawdown_percent",
        "completed_trades",
        "annualized_turnover_multiple",
        "annualized_baseline_cost_fraction",
        "protective_policy_active",
    }
)


class AlphaCalibrationSelectionPolicy:
    """Select only from inner evidence; otherwise explicitly hold cash."""

    def __init__(self, catalog=None, configuration=None):
        self.catalog = tuple(catalog or CALIBRATION_PARAMETER_CATALOG)
        if not self.catalog or any(
            not isinstance(item, AlphaCalibrationParameterSet)
            for item in self.catalog
        ):
            raise TypeError("Catalog must contain calibration parameter sets.")
        ids = tuple(item.parameter_set_id for item in self.catalog)
        if len(set(ids)) != len(ids):
            raise ValueError("Calibration parameter-set IDs must be unique.")
        self.parameter_order = ids
        self.configuration = configuration or NestedCalibrationConfig()
        if not isinstance(self.configuration, NestedCalibrationConfig):
            raise TypeError("Configuration must be NestedCalibrationConfig.")

    @staticmethod
    def _validated_asset_metrics(metrics):
        if not isinstance(metrics, dict) or set(metrics) != INNER_ASSET_METRICS:
            raise ValueError("Inner asset evidence fields are not exact.")
        result = {}
        for name in INNER_ASSET_METRICS - {"protective_policy_active"}:
            result[name] = _finite_number(metrics[name], name)
        if metrics["protective_policy_active"] is not True:
            result["protective_policy_active"] = False
        else:
            result["protective_policy_active"] = True
        for name in (
            "baseline_positive_window_rate",
            "stress_positive_window_rate",
            "annualized_baseline_cost_fraction",
        ):
            if not 0.0 <= result[name] <= 1.0:
                raise ValueError(f"{name} must be a fraction from zero to one.")
        if result["completed_trades"] < 0.0:
            raise ValueError("Completed trades cannot be negative.")
        return result

    def select(self, inner_evidence):
        if not isinstance(inner_evidence, dict):
            raise TypeError("Inner evidence must be a dictionary.")
        if tuple(inner_evidence) != self.parameter_order:
            raise ValueError(
                "Inner evidence must match the complete frozen catalog order."
            )
        config = self.configuration
        records = {}
        eligible = []
        for order, parameter_id in enumerate(self.parameter_order):
            evidence = inner_evidence[parameter_id]
            if not isinstance(evidence, dict) or tuple(sorted(evidence)) != ASSET_SCOPE:
                raise ValueError("Every parameter set requires exact asset evidence.")
            assets = {
                asset: self._validated_asset_metrics(evidence[asset])
                for asset in ASSET_SCOPE
            }
            gates = {
                "positive_baseline_median_return_both_assets": all(
                    item["baseline_median_net_return"] > 0.0
                    for item in assets.values()
                ),
                "nonnegative_stress_median_return_both_assets": all(
                    item["stress_median_net_return"] >= 0.0
                    for item in assets.values()
                ),
                "baseline_inner_persistence": all(
                    item["baseline_positive_window_rate"]
                    >= config.minimum_positive_inner_window_rate
                    for item in assets.values()
                ),
                "stress_inner_persistence": all(
                    item["stress_positive_window_rate"]
                    >= config.minimum_positive_inner_window_rate
                    for item in assets.values()
                ),
                "minimum_inner_trades": all(
                    item["completed_trades"]
                    >= config.minimum_inner_trades_per_asset
                    for item in assets.values()
                ),
                "drawdown_within_limit": all(
                    item["maximum_drawdown_percent"]
                    <= config.maximum_drawdown_percent
                    for item in assets.values()
                ),
                "annual_turnover_within_budget": all(
                    item["annualized_turnover_multiple"]
                    <= config.maximum_annual_turnover_multiple
                    for item in assets.values()
                ),
                "annual_baseline_cost_within_budget": all(
                    item["annualized_baseline_cost_fraction"]
                    <= config.maximum_annual_baseline_cost_fraction
                    for item in assets.values()
                ),
                "protective_policy_active": all(
                    item["protective_policy_active"]
                    for item in assets.values()
                ),
            }
            worst_stress = min(
                item["stress_median_net_return"] for item in assets.values()
            )
            worst_baseline = min(
                item["baseline_median_net_return"] for item in assets.values()
            )
            mean_turnover = sum(
                item["annualized_turnover_multiple"] for item in assets.values()
            ) / len(assets)
            record = {
                "eligible": all(gates.values()),
                "gates": gates,
                "failed_gates": [name for name, passed in gates.items() if not passed],
                "selection_metrics": {
                    "worst_asset_stress_median_net_return": worst_stress,
                    "worst_asset_baseline_median_net_return": worst_baseline,
                    "mean_annualized_turnover_multiple": mean_turnover,
                },
            }
            records[parameter_id] = record
            if record["eligible"]:
                eligible.append(
                    (
                        -worst_stress,
                        -worst_baseline,
                        mean_turnover,
                        order,
                        parameter_id,
                    )
                )
        selected = min(eligible)[-1] if eligible else None
        return {
            "status": (
                "CALIBRATION_CONFIGURATION_SELECTED"
                if selected is not None
                else "NO_ELIGIBLE_CONFIGURATION_HOLD_CASH"
            ),
            "selected_parameter_set_id": selected,
            "hold_cash": selected is None,
            "selection_scope": "INNER_VALIDATION_ONLY",
            "outer_test_evidence_used": False,
            "global_hindsight_leaderboard_generated": False,
            "records": records,
        }


def alpha_discovery_configuration():
    nested = NestedCalibrationConfig()
    catalog = CALIBRATION_PARAMETER_CATALOG
    return {
        "parameter_catalog_version": PARAMETER_CATALOG_VERSION,
        "parameter_catalog_sha256": parameter_catalog_fingerprint(catalog),
        "parameter_set_order": list(PARAMETER_SET_ORDER),
        "parameter_sets": [parameter.as_dict() for parameter in catalog],
        "diagnostic_phase": {
            "exact_v2_variant_order": list(VARIANT_ORDER),
            "zero_cost_replay": True,
            "zero_cost_may_select_parameters": False,
            "trade_path_metrics": [
                "MAXIMUM_FAVORABLE_EXCURSION_R",
                "MAXIMUM_ADVERSE_EXCURSION_R",
                "REALIZED_R",
                "HOLDING_BARS",
                "BARS_TO_MAXIMUM_FAVORABLE_EXCURSION",
                "EXIT_REASON",
            ],
            "raw_trade_path_persisted": False,
        },
        "calibration_phase": {
            **nested.as_dict(),
            "selection_profiles": ["COINBASE_BASELINE", "COINBASE_STRESS"],
            "selection_assets": list(ASSET_SCOPE),
            "one_shared_parameter_set_across_assets": True,
            "outer_test_available_to_selection": False,
            "no_eligible_configuration_action": "HOLD_CASH",
            "selection_order": [
                "MAXIMIZE_WORST_ASSET_STRESS_MEDIAN_NET_RETURN",
                "MAXIMIZE_WORST_ASSET_BASELINE_MEDIAN_NET_RETURN",
                "MINIMIZE_MEAN_ANNUALIZED_TURNOVER",
                "IMMUTABLE_PARAMETER_CATALOG_ORDER",
            ],
            "global_hindsight_leaderboard": "PROHIBITED",
        },
        "common_execution": {
            "timeframe": "6h",
            "signal_observation": "COMPLETED_BAR_ONLY",
            "entry_execution": "NEXT_BAR_OPEN",
            "risk_per_trade_fraction": 0.005,
            "maximum_position_fraction": 0.50,
            "leverage": "NONE",
            "shorting": False,
            "commission_slippage_spread_on_every_fill": True,
        },
        "implementation_prerequisites": {
            "causal_ema_trend_structure": "REQUIRED",
            "completed_bar_breakeven_transition": "REQUIRED",
            "trade_path_excursion_metrics": "REQUIRED",
            "nested_calibration_runner": "REQUIRED_SEPARATE_REVIEW",
            "status": "NOT_YET_IMPLEMENTED",
        },
        "future_validation": {
            "inspected_development_data_may_form_candidate_evidence": False,
            "new_candidate_identity_required": True,
            "genuinely_unseen_data_required": True,
        },
    }


def _required_boolean(payload, name, expected):
    if payload.get(name) is not expected:
        raise ValueError(f"Recorded Alpha v2 {name} is invalid.")


def _validate_alpha_development_basis(payload):
    comparison = payload.get("comparison")
    if not isinstance(comparison, dict):
        raise ValueError("Recorded Alpha v2 comparison is missing.")
    counts = comparison.get("outcome_counts")
    if counts != {
        "INCONCLUSIVE": 0,
        "MECHANISM_RETAINS_DEVELOPMENT_INTEREST": 0,
        "SCREEN_OUT": 3,
    }:
        raise ValueError("Recorded Alpha v2 outcome counts are invalid.")
    if comparison.get("mechanisms_retaining_interest") != []:
        raise ValueError("Recorded Alpha v2 unexpectedly retained a mechanism.")
    variants = payload.get("variant_evidence")
    if not isinstance(variants, dict) or tuple(sorted(variants)) != tuple(
        sorted(VARIANT_ORDER)
    ):
        raise ValueError("Recorded Alpha v2 variant evidence scope is invalid.")
    for variant_id in VARIANT_ORDER:
        review = variants[variant_id].get("development_review", {})
        if review.get("outcome") != "SCREEN_OUT":
            raise ValueError("Recorded Alpha v2 variant outcome is invalid.")
        if frozenset(review.get("failed_gates", [])) != (
            EXPECTED_FAILED_DEVELOPMENT_GATES
        ):
            raise ValueError("Recorded Alpha v2 failed-gate basis is invalid.")
        gates = review.get("gates", {})
        for gate in (
            "minimum_walk_forward_windows",
            "minimum_development_trades_per_asset",
            "oos_drawdown_within_limit",
            "annual_turnover_within_budget",
            "annual_baseline_cost_within_budget",
            "protective_exit_policy_active_all_scenarios",
        ):
            if gates.get(gate) is not True:
                raise ValueError("Recorded Alpha v2 passed-gate basis is invalid.")


def load_recorded_alpha_development_report(
    report_path,
    expected_sha256=RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256,
):
    """Load only the exact canonical, safely closed Alpha v2 evidence."""

    expected_sha256 = _validated_sha256(
        expected_sha256, "Required Alpha Development report SHA-256"
    )
    path = Path(report_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Recorded Alpha Development report does not exist: {path}"
        )
    report_bytes = path.read_bytes()
    digest = hashlib.sha256(report_bytes).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Recorded Alpha Development report SHA-256 changed.")
    checksum_path = path.with_name("alpha_development_report.sha256")
    if not checksum_path.is_file():
        raise FileNotFoundError("Recorded Alpha Development checksum is missing.")
    expected_sidecar = f"{digest}  {path.name}\n".encode("ascii")
    if checksum_path.read_bytes() != expected_sidecar:
        raise ValueError("Recorded Alpha Development checksum is invalid.")
    try:
        payload = json.loads(report_bytes)
    except json.JSONDecodeError as exc:
        raise ValueError("Recorded Alpha Development report is not JSON.") from exc
    if canonical_json_bytes(payload) != report_bytes:
        raise ValueError("Recorded Alpha Development report is not canonical JSON.")
    if (
        payload.get("schema_version") != 1
        or payload.get("status") != "ALPHA_DEVELOPMENT_COMPLETED"
        or payload.get("alpha_development_id") != ALPHA_DEVELOPMENT_ID
        or payload.get("manifest_sha256") != DEVELOPMENT_MANIFEST_SHA256
        or payload.get("dataset_role") != "INSPECTED_DEVELOPMENT_ONLY"
        or payload.get("variant_order") != list(VARIANT_ORDER)
        or payload.get("variant_count") != len(VARIANT_ORDER)
        or payload.get("scenario_count") != 3
        or payload.get("joint_multi_asset_evaluations") != 9
    ):
        raise ValueError("Recorded Alpha Development identity or scope is invalid.")
    for name in (
        "joint_development_evaluation_executed",
        "protective_exit_engine_active",
    ):
        _required_boolean(payload, name, True)
    for name in (
        "parameter_sweep_executed",
        "parameter_calibration_executed",
        "automatic_ranking_generated",
        "automatic_strategy_selection",
        "formal_candidate_evaluation",
        "candidate_v2_authorized",
        "optimization_authorized",
        "bounded_forward_paper_review_eligible",
        "bounded_forward_paper_authorized",
        "live_execution_authorized",
    ):
        _required_boolean(payload, name, False)
    if payload.get("selected_variant") is not None:
        raise ValueError("Recorded Alpha v2 unexpectedly selected a variant.")
    _validate_alpha_development_basis(payload)
    return payload, digest


def _safety_boundary():
    return {
        "zero_cost_diagnostic_executed": False,
        "trade_path_analysis_executed": False,
        "nested_calibration_executed": False,
        "outer_development_test_executed": False,
        "parameter_selection_executed": False,
        "global_hindsight_leaderboard_generated": False,
        "formal_candidate_evaluation": False,
        "candidate_v2_authorized": False,
        "optimization_authorized": False,
        "bounded_forward_paper_review_eligible": False,
        "bounded_forward_paper_authorized": False,
        "live_execution_authorized": False,
    }


@dataclass(frozen=True)
class LockedAlphaDiscovery:
    contract: CoinbaseResearchDatasetContract
    assets: dict
    manifest_sha256: str
    alpha_development_report: dict
    alpha_development_report_sha256: str
    configuration: dict


class AlphaDiscoveryPreregistration:
    """Freeze the diagnostic/calibration procedure without executing it."""

    def __init__(
        self,
        contract=FIRST_CANDIDATE_DATASET_CONTRACT,
        required_manifest_sha256=DEVELOPMENT_MANIFEST_SHA256,
        required_alpha_report_sha256=(
            RECORDED_ALPHA_DEVELOPMENT_REPORT_SHA256
        ),
        dataset_lock=None,
        alpha_report_loader=load_recorded_alpha_development_report,
    ):
        if not isinstance(contract, CoinbaseResearchDatasetContract):
            raise TypeError("Contract must be a CoinbaseResearchDatasetContract.")
        if not callable(alpha_report_loader):
            raise TypeError("Alpha report loader must be callable.")
        self.contract = contract
        self.required_manifest_sha256 = _validated_sha256(
            required_manifest_sha256, "Required manifest SHA-256"
        )
        self.required_alpha_report_sha256 = _validated_sha256(
            required_alpha_report_sha256,
            "Required Alpha Development report SHA-256",
        )
        self.dataset_lock = dataset_lock or CoinbaseResearchDatasetLock(contract)
        self.alpha_report_loader = alpha_report_loader

    def declaration(self):
        return {
            "schema_version": ALPHA_DISCOVERY_SCHEMA_VERSION,
            "status": "ALPHA_DISCOVERY_EVIDENCE_LOCK_PENDING",
            "alpha_discovery_id": ALPHA_DISCOVERY_ID,
            "purpose": "BOUNDED_NESTED_ALPHA_DISCOVERY_NOT_CANDIDATE_SELECTION",
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": self.contract.timeframe,
            "assets": list(self.contract.products),
            "required_manifest_sha256": self.required_manifest_sha256,
            "required_alpha_development_report_sha256": (
                self.required_alpha_report_sha256
            ),
            "configuration": alpha_discovery_configuration(),
            "implementation_prerequisites_satisfied": False,
            "separate_runner_review_required": True,
            "runner_execution_authorized": False,
            **_safety_boundary(),
        }

    def lock(self, manifest_path, alpha_report_path):
        dataset = self.dataset_lock.lock(manifest_path)
        if dataset.manifest_sha256 != self.required_manifest_sha256:
            raise ValueError("Dataset does not match the frozen discovery manifest.")
        payload, digest = self.alpha_report_loader(
            alpha_report_path,
            expected_sha256=self.required_alpha_report_sha256,
        )
        if payload.get("manifest_sha256") != dataset.manifest_sha256:
            raise ValueError("Alpha evidence and dataset manifest do not match.")
        if tuple(sorted(dataset.assets)) != tuple(self.contract.products):
            raise ValueError("Locked asset scope does not match alpha discovery.")
        return LockedAlphaDiscovery(
            contract=self.contract,
            assets=dataset.assets,
            manifest_sha256=dataset.manifest_sha256,
            alpha_development_report=payload,
            alpha_development_report_sha256=digest,
            configuration=alpha_discovery_configuration(),
        )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Declare or evidence-lock bounded Alpha Discovery and Calibration "
            "Protocol v1 without executing diagnostics or calibration."
        )
    )
    parser.add_argument("--manifest", help="Exact frozen six-hour manifest.")
    parser.add_argument(
        "--alpha-report", help="Exact closed Alpha Development v2 report."
    )
    args = parser.parse_args(argv)
    if bool(args.manifest) != bool(args.alpha_report):
        parser.error("--manifest and --alpha-report must be supplied together.")

    preregistration = AlphaDiscoveryPreregistration()
    if args.manifest:
        locked = preregistration.lock(args.manifest, args.alpha_report)
        result = {
            "schema_version": ALPHA_DISCOVERY_SCHEMA_VERSION,
            "status": "ALPHA_DISCOVERY_EVIDENCE_LOCKED",
            "alpha_discovery_id": ALPHA_DISCOVERY_ID,
            "manifest_sha256": locked.manifest_sha256,
            "alpha_development_report_sha256": (
                locked.alpha_development_report_sha256
            ),
            "dataset_role": "INSPECTED_DEVELOPMENT_ONLY",
            "timeframe": locked.contract.timeframe,
            "assets": list(locked.contract.products),
            "asset_rows": {
                name: len(frame) for name, frame in sorted(locked.assets.items())
            },
            "parameter_set_order": list(PARAMETER_SET_ORDER),
            "parameter_catalog_sha256": parameter_catalog_fingerprint(),
            "configuration": locked.configuration,
            "implementation_prerequisites_satisfied": False,
            "separate_runner_review_required": True,
            "runner_execution_authorized": False,
            **_safety_boundary(),
        }
    else:
        result = preregistration.declaration()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
