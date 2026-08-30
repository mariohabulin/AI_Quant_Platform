"""One-shot Development discovery runner for Kraken AI-driven V2 Round 1."""

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

try:
    from kraken_ai_driven_v2_development_runner import (
        KrakenAIDrivenV2DevelopmentDatasetReader,
    )
    from kraken_ai_driven_v2_hybrid_discovery_round_1 import (
        DEVELOPMENT_SLICES,
        ROUND_1_CONFIGURATION_LOCK,
        ROUND_1_ROUTE_INTEREST_GATES,
        ROUND_1_SELECTION_GATES,
        PROTOCOL_ID as ROUND_1_PROTOCOL_ID,
        ROUND_ID,
    )
    from kraken_ai_driven_v2_partition import (
        ASSET_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        DEVELOPMENT_END_EXCLUSIVE_UTC,
        PARTITION_PROTOCOL_ID,
        REFERENCE_PARTITION_CONTRACT,
        RESEARCH_START_UTC,
    )
    from kraken_ai_driven_v2_round_1_causal_signals import (
        ACTION_INTENT_COLUMN,
        ENTER_NEXT_OPEN,
        FAMILY_ORDER,
        KrakenAIDrivenV2Round1SignalEngine,
    )
    from kraken_ai_driven_v2_round_1_family_execution import (
        BASELINE_COST_PROFILE_ID,
        FAMILY_EXECUTION_COMPONENT_ID,
        STRESS_COST_PROFILE_ID,
        family_execution_adapters,
    )
    from research_evidence import canonical_json_bytes
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_development_runner import (
        KrakenAIDrivenV2DevelopmentDatasetReader,
    )
    from .kraken_ai_driven_v2_hybrid_discovery_round_1 import (
        DEVELOPMENT_SLICES,
        ROUND_1_CONFIGURATION_LOCK,
        ROUND_1_ROUTE_INTEREST_GATES,
        ROUND_1_SELECTION_GATES,
        PROTOCOL_ID as ROUND_1_PROTOCOL_ID,
        ROUND_ID,
    )
    from .kraken_ai_driven_v2_partition import (
        ASSET_ORDER,
        DATASET_ID,
        DATASET_MANIFEST_SHA256,
        DEVELOPMENT_END_EXCLUSIVE_UTC,
        PARTITION_PROTOCOL_ID,
        REFERENCE_PARTITION_CONTRACT,
        RESEARCH_START_UTC,
    )
    from .kraken_ai_driven_v2_round_1_causal_signals import (
        ACTION_INTENT_COLUMN,
        ENTER_NEXT_OPEN,
        FAMILY_ORDER,
        KrakenAIDrivenV2Round1SignalEngine,
    )
    from .kraken_ai_driven_v2_round_1_family_execution import (
        BASELINE_COST_PROFILE_ID,
        FAMILY_EXECUTION_COMPONENT_ID,
        STRESS_COST_PROFILE_ID,
        family_execution_adapters,
    )
    from .research_evidence import canonical_json_bytes


SCHEMA_VERSION = 1
DISCOVERY_RUNNER_PROTOCOL_ID = (
    "kraken-btc-eth-xrp-ai-driven-v2-round-1-discovery-runner-v1"
)
DISCOVERY_RUN_ID = "kraken-ai-v2-round-1-development-discovery-v1"
AUTHORIZATION_PHRASE = "EXECUTE_KRAKEN_AI_V2_ROUND_1_DISCOVERY_ONCE"
INITIAL_CAPITAL = 5000.0
QUOTE_CURRENCY = "USD_RESEARCH_NOTIONAL"
EVIDENCE_DIRECTORY_NAME = "round_1_development_discovery_v1"
STAGING_DIRECTORY_NAME = ".round_1_development_discovery_v1.staging"
REPORT_FILENAME = "kraken_ai_v2_round_1_discovery_report.json"
REPORT_SHA256_FILENAME = "kraken_ai_v2_round_1_discovery_report.sha256"
COST_PROFILE_ORDER = (BASELINE_COST_PROFILE_ID, STRESS_COST_PROFILE_ID)
ROUTE_ORDER = tuple(
    f"{asset}|{family}" for asset in ASSET_ORDER for family in FAMILY_ORDER
)


def _slice_id(timestamp):
    timestamp = pd.Timestamp(timestamp)
    for slice_id, start, end in DEVELOPMENT_SLICES:
        if pd.Timestamp(start) <= timestamp < pd.Timestamp(end):
            return slice_id
    raise ValueError("Closed trade entry is outside frozen Development slices.")


def discovery_runner_configuration():
    return {
        "schema_version": SCHEMA_VERSION,
        "discovery_runner_protocol_id": DISCOVERY_RUNNER_PROTOCOL_ID,
        "discovery_run_id": DISCOVERY_RUN_ID,
        "round_1_protocol_id": ROUND_1_PROTOCOL_ID,
        "round_id": ROUND_ID,
        "round_1_configuration_sha256": ROUND_1_CONFIGURATION_LOCK.sha256,
        "family_execution_component_id": FAMILY_EXECUTION_COMPONENT_ID,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "partition_protocol_id": PARTITION_PROTOCOL_ID,
        "partition_plan_sha256": REFERENCE_PARTITION_CONTRACT.plan_sha256(),
        "partition": "DEVELOPMENT",
        "development_start_utc": RESEARCH_START_UTC,
        "development_end_exclusive_utc": DEVELOPMENT_END_EXCLUSIVE_UTC,
        "asset_order": list(ASSET_ORDER),
        "family_order": list(FAMILY_ORDER),
        "route_order": list(ROUTE_ORDER),
        "cost_profile_order": list(COST_PROFILE_ORDER),
        "development_slices": [
            {"slice_id": value[0], "start_utc": value[1], "end_exclusive_utc": value[2]}
            for value in DEVELOPMENT_SLICES
        ],
        "initial_capital_per_route_profile": INITIAL_CAPITAL,
        "quote_currency": QUOTE_CURRENCY,
        "route_ledger_semantics": "INDEPENDENT_ASSET_FAMILY_COST_PROFILE",
        "trade_slice_attribution": "ENTRY_TIMESTAMP",
        "slice_boundary_state_reset": False,
        "gap_feature_signal_position_reset": True,
        "gap_with_open_position_policy": "HALT_ROUTE_INCONCLUSIVE_UNRESOLVED",
        "terminal_position_policy": "PRESERVE_UNRESOLVED_NO_SYNTHETIC_FORCE_CLOSE",
        "same_open_phase_order": [
            "EXISTING_POSITION_PROTECTIVE_OR_SCHEDULED_EXIT",
            "PREVIOUS_COMPLETED_BAR_PENDING_ENTRY",
            "ACTIVE_POSITION_INTRABAR_PROTECTION",
            "COMPLETED_BAR_EXIT_SCHEDULING",
            "COMPLETED_BAR_SIGNAL_CAPTURE",
            "ADVERSE_COMPLETED_CLOSE_MARK",
        ],
        "route_interest_gates": dict(ROUND_1_ROUTE_INTEREST_GATES),
        "round_interest_gates": dict(ROUND_1_SELECTION_GATES),
        "minimum_count_gates_apply_to_both_cost_profiles": True,
        "largest_trade_share_gate_applies_to_both_cost_profiles": True,
        "no_trade_slice_counts_as_nonnegative": False,
        "performance_comparison_policy": "ABSOLUTE_GATES_NO_LEADERBOARD",
        "same_asset_multiple_pass_policy": "SEPARATE_PORTFOLIO_REVIEW_REQUIRED",
        "parameter_sweep_authorized": False,
        "automatic_ranking_authorized": False,
        "automatic_strategy_selection_authorized": False,
        "calibration_access_authorized": False,
        "evaluation_access_authorized": False,
        "candidate_v2_authorized": False,
        "real_order_submission": False,
        "live_execution_authorized": False,
    }


@dataclass(frozen=True)
class RecordedRound1DiscoveryEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    round_status: str
    eligible_route_count: int
    eligible_asset_count: int
    status: str = "KRAKEN_AI_V2_ROUND_1_DISCOVERY_EVIDENCE_RECORDED"

    def as_dict(self):
        result = asdict(self)
        result["report_path"] = str(self.report_path)
        result["checksum_path"] = str(self.checksum_path)
        result.update(
            {
                "development_run_authorized": True,
                "development_run_executed": True,
                "development_data_opened": True,
                "calibration_data_opened": False,
                "evaluation_data_opened": False,
                "candidate_v2_authorized": False,
                "real_orders_submitted": False,
                "live_execution_authorized": False,
            }
        )
        return result


@dataclass(frozen=True)
class LockedRound1DiscoveryEvidence:
    report_path: Path
    checksum_path: Path
    report_sha256: str
    report: dict
    status: str = "KRAKEN_AI_V2_ROUND_1_DISCOVERY_EVIDENCE_LOCK_PASS"


def _profit_factor(trades):
    gains = sum(max(0.0, trade["net_pnl"]) for trade in trades)
    losses = -sum(min(0.0, trade["net_pnl"]) for trade in trades)
    if losses == 0.0:
        return None, gains > 0.0
    return gains / losses, False


def _profile_gate_value(profile, field, *, infinite_pass=False):
    value = profile[field]
    if value is None:
        if infinite_pass and profile.get("profit_factor_is_infinite"):
            return math.inf
        return 0.0
    return value


def evaluate_route_interest(baseline, stress):
    """Apply every frozen absolute gate; never rank or select a route."""

    gates = ROUND_1_ROUTE_INTEREST_GATES
    checks = {
        "minimum_closed_trades": all(
            item["closed_trade_count"] >= gates["minimum_closed_trades"]
            for item in (baseline, stress)
        ),
        "minimum_slices_with_trade": all(
            item["slices_with_trade"] >= gates["minimum_slices_with_trade"]
            for item in (baseline, stress)
        ),
        "minimum_nonnegative_slices": all(
            item["nonnegative_slices"] >= gates["minimum_nonnegative_slices"]
            for item in (baseline, stress)
        ),
        "minimum_baseline_net_expectancy_r": (
            baseline["net_expectancy_r"]
            >= gates["minimum_baseline_net_expectancy_r"]
        ),
        "minimum_stress_net_expectancy_r": (
            stress["net_expectancy_r"]
            >= gates["minimum_stress_net_expectancy_r"]
        ),
        "minimum_baseline_profit_factor": (
            _profile_gate_value(baseline, "profit_factor", infinite_pass=True)
            >= gates["minimum_baseline_profit_factor"]
        ),
        "minimum_stress_profit_factor": (
            _profile_gate_value(stress, "profit_factor", infinite_pass=True)
            >= gates["minimum_stress_profit_factor"]
        ),
        "maximum_baseline_marked_drawdown_fraction": (
            baseline["maximum_marked_drawdown_fraction"]
            <= gates["maximum_baseline_marked_drawdown_fraction"]
        ),
        "maximum_stress_marked_drawdown_fraction": (
            stress["maximum_marked_drawdown_fraction"]
            <= gates["maximum_stress_marked_drawdown_fraction"]
        ),
        "maximum_largest_trade_net_profit_share": all(
            item["largest_trade_net_profit_share"]
            <= gates["maximum_largest_trade_net_profit_share"]
            for item in (baseline, stress)
        ),
        "required_unresolved_position_count": all(
            item["unresolved_position_count"]
            == gates["required_unresolved_position_count"]
            for item in (baseline, stress)
        ),
    }
    return {
        "gate_id": "kraken-ai-v2-r1-route-interest-gates-v1",
        "checks": checks,
        "eligible": all(checks.values()),
        "action": "RETAIN_FOR_SEPARATE_PORTFOLIO_REVIEW" if all(checks.values()) else "HOLD_CASH",
    }


def summarize_round_interest(route_results):
    eligible_routes = [item["route_id"] for item in route_results if item["interest_gate"]["eligible"]]
    eligible_assets = [
        asset
        for asset in ASSET_ORDER
        if any(item["asset"] == asset for item in route_results if item["interest_gate"]["eligible"])
    ]
    per_asset = {
        asset: [
            item["route_id"]
            for item in route_results
            if item["asset"] == asset and item["interest_gate"]["eligible"]
        ]
        for asset in ASSET_ORDER
    }
    round_pass = (
        len(eligible_routes) >= ROUND_1_SELECTION_GATES["minimum_eligible_route_count"]
        and len(eligible_assets) >= ROUND_1_SELECTION_GATES["minimum_eligible_asset_count"]
    )
    multiple = {asset: routes for asset, routes in per_asset.items() if len(routes) > 1}
    if not round_pass:
        status = "KRAKEN_AI_V2_ROUND_1_DEVELOPMENT_NO_INTEREST_HOLD_CASH"
        next_action = "CLOSE_ROUND_OR_PRE_REGISTER_VERSIONED_FEEDBACK"
    elif multiple:
        status = "KRAKEN_AI_V2_ROUND_1_DEVELOPMENT_INTEREST_PORTFOLIO_REVIEW_REQUIRED"
        next_action = "SEPARATE_PORTFOLIO_REVIEW_REQUIRED"
    else:
        status = "KRAKEN_AI_V2_ROUND_1_DEVELOPMENT_INTEREST_RETAINED"
        next_action = "SEPARATE_CALIBRATION_AUTHORIZATION_DECISION_REQUIRED"
    return {
        "status": status,
        "round_interest_gate_passed": round_pass,
        "eligible_route_count": len(eligible_routes),
        "eligible_asset_count": len(eligible_assets),
        "eligible_route_ids": eligible_routes,
        "eligible_assets": eligible_assets,
        "eligible_routes_by_asset": per_asset,
        "same_asset_multiple_eligible_routes": multiple,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "candidate_v2_authorized": False,
        "next_action": next_action,
    }


class KrakenAIDrivenV2Round1DiscoveryEvidenceLock:
    """Independently lock canonical one-shot Round 1 discovery evidence."""

    def lock(self, evidence_directory):
        evidence_directory = Path(evidence_directory)
        report_path = evidence_directory / REPORT_FILENAME
        checksum_path = evidence_directory / REPORT_SHA256_FILENAME
        try:
            report_bytes = report_path.read_bytes()
            checksum = checksum_path.read_text(encoding="ascii").strip().split()
        except (OSError, UnicodeError) as exc:
            raise ValueError("Unable to read Round 1 discovery evidence.") from exc
        digest = hashlib.sha256(report_bytes).hexdigest()
        if checksum != [digest, REPORT_FILENAME]:
            raise ValueError("Round 1 discovery evidence SHA-256 sidecar mismatch.")
        try:
            report = json.loads(report_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("Unable to decode Round 1 discovery evidence.") from exc
        if report_bytes != canonical_json_bytes(report):
            raise ValueError("Round 1 discovery report bytes are not canonical.")
        expected = {
            "schema_version": SCHEMA_VERSION,
            "discovery_runner_protocol_id": DISCOVERY_RUNNER_PROTOCOL_ID,
            "discovery_run_id": DISCOVERY_RUN_ID,
            "round_1_protocol_id": ROUND_1_PROTOCOL_ID,
            "round_1_configuration_sha256": ROUND_1_CONFIGURATION_LOCK.sha256,
            "dataset_id": DATASET_ID,
            "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
            "partition_protocol_id": PARTITION_PROTOCOL_ID,
            "partition_plan_sha256": REFERENCE_PARTITION_CONTRACT.plan_sha256(),
            "configuration": discovery_runner_configuration(),
            "route_order": list(ROUTE_ORDER),
            "dataset_opened": True,
            "development_data_opened": True,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "development_run_authorized": True,
            "development_run_executed": True,
            "performance_evaluation_executed": True,
            "parameter_sweep_executed": False,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "candidate_v2_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
        }
        for key, value in expected.items():
            if report.get(key) != value:
                raise ValueError(f"Round 1 discovery evidence field is invalid: {key}.")
        if len(report.get("route_results", ())) != len(ROUTE_ORDER):
            raise ValueError("Round 1 discovery evidence route count mismatch.")
        if [item.get("route_id") for item in report["route_results"]] != list(ROUTE_ORDER):
            raise ValueError("Round 1 discovery evidence route order mismatch.")
        if report.get("calibration_rows_parsed") != 0 or report.get("evaluation_rows_parsed") != 0:
            raise ValueError("Round 1 discovery evidence parsed nondevelopment rows.")
        return LockedRound1DiscoveryEvidence(report_path, checksum_path, digest, report)


class KrakenAIDrivenV2Round1DiscoveryRunner:
    """Evaluate every frozen asset-family route once on Development only."""

    def __init__(self, *, dataset_reader=None, signal_engine_factory=None, adapter_factory=None):
        self.dataset_reader = dataset_reader or KrakenAIDrivenV2DevelopmentDatasetReader()
        self.signal_engine_factory = signal_engine_factory or KrakenAIDrivenV2Round1SignalEngine
        self.adapter_factory = adapter_factory or family_execution_adapters
        if not hasattr(self.dataset_reader, "read"):
            raise TypeError("Round 1 discovery dataset reader must provide read().")
        if not callable(self.signal_engine_factory) or not callable(self.adapter_factory):
            raise TypeError("Round 1 discovery factories must be callable.")

    @staticmethod
    def _mark_value(position, close, adapter):
        fill = adapter.costs.sell_fill(float(close))
        return fill * position.units - adapter.costs.commission(fill, position.units)

    def _simulate_profile(self, asset, family, segments, cost_profile_id):
        adapter = self.adapter_factory(cost_profile_id=cost_profile_id)[family]
        cash = INITIAL_CAPITAL
        peak = INITIAL_CAPITAL
        max_drawdown = 0.0
        trades = []
        entries = []
        rejection_counts = Counter()
        cancellation_counts = Counter()
        exit_counts = Counter()
        signal_count = 0
        position = None
        entry_context = None
        pending_signal = None
        pending_exit = None
        unresolved = []
        path_completed = True
        halt_reason = None
        mark_count = 0

        def record_exit(timestamp, decision):
            nonlocal cash, position, entry_context, pending_exit
            proceeds = decision.net_proceeds
            net_pnl = proceeds - entry_context["cash_required"]
            risk = entry_context["planned_monetary_risk"]
            trade = {
                "asset": asset,
                "family_id": family,
                "cost_profile_id": cost_profile_id,
                "signal_timestamp": entry_context["signal_timestamp"],
                "entry_timestamp": entry_context["entry_timestamp"],
                "exit_timestamp": timestamp.isoformat(),
                "slice_id": _slice_id(entry_context["entry_timestamp"]),
                "units": position.units,
                "entry_fill_price": position.entry_fill_price,
                "exit_fill_price": decision.fill_price,
                "exit_reason": decision.reason,
                "planned_monetary_risk": risk,
                "net_pnl": net_pnl,
                "net_r_multiple": net_pnl / risk,
                "modeled_cost_drag": (
                    (position.entry_fill_price - entry_context["raw_open_price"]) * position.units
                    + position.entry_commission
                    + (decision.market_reference_price - decision.fill_price) * position.units
                    + decision.commission
                ),
            }
            cash += proceeds
            trades.append(trade)
            exit_counts[decision.reason] += 1
            position = None
            entry_context = None
            pending_exit = None

        for segment_number, segment in enumerate(segments, start=1):
            signals = self.signal_engine_factory().generate(family, segment)
            pending_signal = None
            for timestamp, market_row in segment.iterrows():
                signal_row = signals.loc[timestamp]
                if position is not None:
                    decision = adapter.evaluate_open(position, market_row["Open"], pending_exit)
                    if decision.status == "SYNTHETIC_EXIT":
                        record_exit(timestamp, decision)

                if pending_signal is not None:
                    expected = pending_signal.name + pd.Timedelta(days=1)
                    if timestamp != expected:
                        cancellation_counts["FOLLOWING_OPEN_MISSING_OR_GAP"] += 1
                    elif position is not None:
                        cancellation_counts["ROUTE_POSITION_ALREADY_OPEN"] += 1
                    else:
                        plan = adapter.plan_entry(
                            pending_signal,
                            asset=asset,
                            execution_timestamp=timestamp,
                            next_open_price=market_row["Open"],
                            equity=cash,
                            available_cash=cash,
                            current_open_risk_amount=0.0,
                            current_asset_notional=0.0,
                            open_crypto_positions=0,
                        )
                        if plan.approved:
                            cash -= plan.cash_required
                            position = adapter.position_from_plan(plan)
                            entry_context = {
                                "signal_timestamp": plan.signal_timestamp,
                                "entry_timestamp": plan.execution_timestamp,
                                "raw_open_price": plan.raw_open_price,
                                "cash_required": plan.cash_required,
                                "planned_monetary_risk": plan.planned_monetary_risk,
                            }
                            entries.append(plan.as_dict())
                        else:
                            rejection_counts[plan.reason] += 1
                    pending_signal = None

                if position is not None:
                    decision = adapter.evaluate_intrabar(position, market_row["High"], market_row["Low"])
                    if decision.status == "SYNTHETIC_EXIT":
                        record_exit(timestamp, decision)

                if position is not None:
                    schedule = adapter.complete_bar(position, signal_row)
                    position = schedule.updated_position
                    pending_exit = schedule.pending_exit_reason

                if signal_row[ACTION_INTENT_COLUMN] == ENTER_NEXT_OPEN:
                    signal_count += 1
                    if position is not None or pending_signal is not None:
                        cancellation_counts["ROUTE_POSITION_ALREADY_OPEN"] += 1
                    else:
                        pending_signal = signal_row.copy(deep=True)

                marked = cash if position is None else cash + self._mark_value(position, market_row["Close"], adapter)
                peak = max(peak, marked)
                max_drawdown = max(max_drawdown, 0.0 if peak <= 0.0 else (peak - marked) / peak)
                mark_count += 1

            if pending_signal is not None:
                reason = "FOLLOWING_OPEN_OUTSIDE_DEVELOPMENT_PARTITION" if segment_number == len(segments) else "FOLLOWING_OPEN_MISSING_OR_GAP"
                cancellation_counts[reason] += 1
                pending_signal = None
            if position is not None:
                terminal = segment_number == len(segments)
                unresolved.append(
                    {
                        "asset": asset,
                        "family_id": family,
                        "cost_profile_id": cost_profile_id,
                        "entry_timestamp": position.entry_timestamp.isoformat(),
                        "segment_number": segment_number,
                        "resolution": "OPEN_POSITION_UNRESOLVED",
                        "boundary": "DEVELOPMENT_END" if terminal else "KNOWN_GAP",
                    }
                )
                halt_reason = "OPEN_POSITION_AT_DEVELOPMENT_END" if terminal else "OPEN_POSITION_AT_KNOWN_GAP"
                path_completed = terminal
                break

        profit_factor, infinite_profit_factor = _profit_factor(trades)
        r_values = [trade["net_r_multiple"] for trade in trades]
        net_profit = sum(trade["net_pnl"] for trade in trades)
        largest_profit = max((trade["net_pnl"] for trade in trades), default=0.0)
        largest_share = 1.0 if net_profit <= 0.0 else max(0.0, largest_profit) / net_profit
        slices = []
        for slice_id, start, end in DEVELOPMENT_SLICES:
            selected = [trade for trade in trades if trade["slice_id"] == slice_id]
            slice_pnl = sum(trade["net_pnl"] for trade in selected)
            slices.append(
                {
                    "slice_id": slice_id,
                    "start_utc": start,
                    "end_exclusive_utc": end,
                    "closed_trade_count": len(selected),
                    "net_pnl": slice_pnl,
                    "net_expectancy_r": (sum(trade["net_r_multiple"] for trade in selected) / len(selected) if selected else 0.0),
                    "counts_as_nonnegative": bool(selected) and slice_pnl >= 0.0,
                }
            )
        return {
            "status": (
                "KRAKEN_AI_V2_ROUTE_COMPLETED_FLAT"
                if not unresolved
                else (
                    "KRAKEN_AI_V2_ROUTE_COMPLETED_WITH_UNRESOLVED_TERMINAL_POSITION"
                    if path_completed
                    else "KRAKEN_AI_V2_ROUTE_INCONCLUSIVE_OPEN_POSITION_AT_GAP"
                )
            ),
            "path_completed": path_completed,
            "halt_reason": halt_reason,
            "cost_profile_id": cost_profile_id,
            "initial_capital": INITIAL_CAPITAL,
            "realized_cash": cash,
            "realized_net_pnl": net_profit,
            "terminal_marked_equity": cash if position is None else cash + self._mark_value(position, segment.iloc[-1]["Close"], adapter),
            "maximum_marked_drawdown_fraction": max_drawdown,
            "equity_mark_count": mark_count,
            "signal_count": signal_count,
            "approved_entry_count": len(entries),
            "rejected_entry_count": sum(rejection_counts.values()),
            "entry_rejection_reason_counts": dict(sorted(rejection_counts.items())),
            "canceled_entry_intent_count": sum(cancellation_counts.values()),
            "entry_cancellation_reason_counts": dict(sorted(cancellation_counts.items())),
            "closed_trade_count": len(trades),
            "winning_trade_count": sum(trade["net_pnl"] > 0.0 for trade in trades),
            "losing_trade_count": sum(trade["net_pnl"] < 0.0 for trade in trades),
            "net_expectancy_r": sum(r_values) / len(r_values) if r_values else 0.0,
            "profit_factor": profit_factor,
            "profit_factor_is_infinite": infinite_profit_factor,
            "largest_trade_net_profit_share": largest_share,
            "slices_with_trade": sum(item["closed_trade_count"] > 0 for item in slices),
            "nonnegative_slices": sum(item["counts_as_nonnegative"] for item in slices),
            "slice_results": slices,
            "exit_reason_counts": dict(sorted(exit_counts.items())),
            "total_modeled_cost_drag": sum(trade["modeled_cost_drag"] for trade in trades),
            "entry_ledger": entries,
            "closed_trade_ledger": trades,
            "unresolved_position_count": len(unresolved),
            "unresolved_positions": unresolved,
            "synthetic_terminal_force_close_executed": False,
            "real_orders_submitted": False,
        }

    def execute_development(self, frames):
        if tuple(frames) != ASSET_ORDER:
            raise ValueError("Round 1 Development frame asset order mismatch.")
        segments_by_asset = {}
        segment_rows = {}
        for asset in ASSET_ORDER:
            index_segments = REFERENCE_PARTITION_CONTRACT.materialize_segments(asset, "DEVELOPMENT", frames[asset].index)
            segments_by_asset[asset] = tuple(frames[asset].loc[index].copy(deep=True) for index in index_segments)
            segment_rows[asset] = [len(item) for item in index_segments]
        route_results = []
        for asset in ASSET_ORDER:
            for family in FAMILY_ORDER:
                profiles = {
                    cost_profile_id: self._simulate_profile(asset, family, segments_by_asset[asset], cost_profile_id)
                    for cost_profile_id in COST_PROFILE_ORDER
                }
                gate = evaluate_route_interest(
                    profiles[BASELINE_COST_PROFILE_ID], profiles[STRESS_COST_PROFILE_ID]
                )
                route_results.append(
                    {
                        "route_id": f"{asset}|{family}",
                        "asset": asset,
                        "family_id": family,
                        "profiles": profiles,
                        "interest_gate": gate,
                    }
                )
        round_interest = summarize_round_interest(route_results)
        return {
            "status": round_interest["status"],
            "development_rows": {asset: len(frames[asset]) for asset in ASSET_ORDER},
            "continuous_segment_rows": segment_rows,
            "route_order": list(ROUTE_ORDER),
            "route_results": route_results,
            "round_interest": round_interest,
            "dataset_opened": True,
            "development_data_opened": True,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "development_run_authorized": True,
            "development_run_executed": True,
            "performance_evaluation_executed": True,
            "parameter_sweep_executed": False,
            "automatic_ranking_generated": False,
            "automatic_strategy_selection": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "real_orders_submitted": False,
            "live_execution_authorized": False,
        }

    @staticmethod
    def _external_paths(dataset_path, evidence_root):
        project_root = Path(__file__).resolve().parents[1]
        dataset = Path(dataset_path).resolve()
        evidence = Path(evidence_root).resolve()
        if dataset == project_root or dataset.is_relative_to(project_root):
            raise ValueError("Round 1 dataset must remain outside the repository.")
        if evidence == project_root or evidence.is_relative_to(project_root):
            raise ValueError("Round 1 evidence must remain outside the repository.")
        if dataset == evidence or evidence.is_relative_to(dataset) or dataset.is_relative_to(evidence):
            raise ValueError("Round 1 dataset and evidence must not overlap.")
        return dataset, evidence

    @staticmethod
    def _assert_one_shot(evidence_root):
        final = evidence_root / EVIDENCE_DIRECTORY_NAME
        staging = evidence_root / STAGING_DIRECTORY_NAME
        if final.exists():
            raise FileExistsError("Round 1 discovery evidence already exists; refusing repeat.")
        if staging.exists():
            raise FileExistsError("Incomplete Round 1 discovery staging evidence exists.")
        return final, staging

    def run(self, dataset_path, evidence_root, authorization_phrase):
        if authorization_phrase != AUTHORIZATION_PHRASE:
            raise PermissionError("Exact Round 1 discovery authorization phrase is required.")
        dataset_path, evidence_root = self._external_paths(dataset_path, evidence_root)
        final, staging = self._assert_one_shot(evidence_root)
        locked = self.dataset_reader.read(dataset_path)
        if locked.manifest_sha256 != DATASET_MANIFEST_SHA256:
            raise ValueError("Locked Round 1 Development manifest identity mismatch.")
        if locked.calibration_rows_parsed or locked.evaluation_rows_parsed:
            raise ValueError("Locked Round 1 reader exposed nondevelopment OHLCV.")
        execution = self.execute_development({asset: locked.frame(asset) for asset in ASSET_ORDER})
        payload = {
            "schema_version": SCHEMA_VERSION,
            "discovery_runner_protocol_id": DISCOVERY_RUNNER_PROTOCOL_ID,
            "discovery_run_id": DISCOVERY_RUN_ID,
            "round_1_protocol_id": ROUND_1_PROTOCOL_ID,
            "round_1_configuration_sha256": ROUND_1_CONFIGURATION_LOCK.sha256,
            "dataset_id": locked.dataset_id,
            "dataset_manifest_sha256": locked.manifest_sha256,
            "source_mode": locked.source_mode,
            "partition_protocol_id": PARTITION_PROTOCOL_ID,
            "partition_plan_sha256": REFERENCE_PARTITION_CONTRACT.plan_sha256(),
            "configuration": discovery_runner_configuration(),
            "asset_file_sha256": locked.asset_file_sha256,
            "full_observed_rows": locked.full_observed_rows,
            "opaque_non_development_rows": locked.opaque_non_development_rows,
            "full_asset_files_hashed_as_opaque_bytes": True,
            "calibration_rows_parsed": 0,
            "evaluation_rows_parsed": 0,
            **execution,
        }
        report_bytes = canonical_json_bytes(payload)
        digest = hashlib.sha256(report_bytes).hexdigest()
        evidence_root.mkdir(parents=True, exist_ok=True)
        staging.mkdir(exist_ok=False)
        (staging / REPORT_FILENAME).write_bytes(report_bytes)
        (staging / REPORT_SHA256_FILENAME).write_text(f"{digest}  {REPORT_FILENAME}\n", encoding="ascii")
        staging.rename(final)
        locked_evidence = KrakenAIDrivenV2Round1DiscoveryEvidenceLock().lock(final)
        return RecordedRound1DiscoveryEvidence(
            locked_evidence.report_path,
            locked_evidence.checksum_path,
            locked_evidence.report_sha256,
            execution["status"],
            execution["round_interest"]["eligible_route_count"],
            execution["round_interest"]["eligible_asset_count"],
        )


def runner_declaration():
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "KRAKEN_AI_V2_ROUND_1_DISCOVERY_RUNNER_IMPLEMENTED_NO_RUN_AUTHORIZATION",
        "discovery_runner_protocol_id": DISCOVERY_RUNNER_PROTOCOL_ID,
        "discovery_run_id": DISCOVERY_RUN_ID,
        "round_1_configuration_sha256": ROUND_1_CONFIGURATION_LOCK.sha256,
        "route_count": len(ROUTE_ORDER),
        "route_order": list(ROUTE_ORDER),
        "cost_profile_ids": list(COST_PROFILE_ORDER),
        "configuration": discovery_runner_configuration(),
        "development_only_reader_reused": True,
        "independent_evidence_lock_implemented": True,
        "one_shot_atomic_evidence_implemented": True,
        "absolute_route_gates_implemented": True,
        "round_interest_gate_implemented": True,
        "discovery_runner_implemented": True,
        "dataset_opened": False,
        "development_data_opened": False,
        "calibration_data_opened": False,
        "evaluation_data_opened": False,
        "development_run_authorized": False,
        "development_run_executed": False,
        "performance_evaluation_executed": False,
        "parameter_sweep_executed": False,
        "automatic_ranking_generated": False,
        "automatic_strategy_selection": False,
        "candidate_v2_authorized": False,
        "bounded_forward_paper_authorized": False,
        "cloud_execution_authorized": False,
        "real_orders_submitted": False,
        "live_execution_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Execute Kraken AI-driven v2 Round 1 Development discovery once.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--authorization-phrase", required=True)
    args = parser.parse_args(argv)
    result = KrakenAIDrivenV2Round1DiscoveryRunner().run(args.dataset, args.evidence_root, args.authorization_phrase)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
