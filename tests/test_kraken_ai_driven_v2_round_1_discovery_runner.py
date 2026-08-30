import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_development_runner import LockedDevelopmentDataset
from kraken_ai_driven_v2_hybrid_discovery_round_1 import ROUND_1_HYPOTHESES
from kraken_ai_driven_v2_partition import ASSET_ORDER, DATASET_ID, DATASET_MANIFEST_SHA256
from kraken_ai_driven_v2_round_1_causal_signals import (
    ACTION_INTENT_COLUMN,
    ENTER_NEXT_OPEN,
    FAMILY_COLUMN,
    FEATURES_AVAILABLE_COLUMN,
    HYPOTHESIS_COLUMN,
    INTENT_NONE,
    SETUP_LOW_COLUMN,
    SETUP_TIMESTAMP_COLUMN,
    SIGNAL_ATR_COLUMN,
    SIGNAL_CONDITION_COLUMN,
    STATE_AFTER_COLUMN,
    STATE_FLAT,
    TARGET_ANCHOR_COLUMN,
    TRANSITION_COLUMN,
)
from kraken_ai_driven_v2_round_1_family_execution import (
    BASELINE_COST_PROFILE_ID,
    PRIOR_CLOSE_LOW_10_COLUMN,
)
from kraken_ai_driven_v2_round_1_discovery_runner import (
    AUTHORIZATION_PHRASE,
    COST_PROFILE_ORDER,
    EVIDENCE_DIRECTORY_NAME,
    REPORT_FILENAME,
    REPORT_SHA256_FILENAME,
    ROUTE_ORDER,
    KrakenAIDrivenV2Round1DiscoveryEvidenceLock,
    KrakenAIDrivenV2Round1DiscoveryRunner,
    discovery_runner_configuration,
    evaluate_route_interest,
    runner_declaration,
    summarize_round_interest,
)


def _profile(**changes):
    result = {
        "closed_trade_count": 8,
        "slices_with_trade": 3,
        "nonnegative_slices": 3,
        "net_expectancy_r": 0.2,
        "profit_factor": 1.4,
        "profit_factor_is_infinite": False,
        "maximum_marked_drawdown_fraction": 0.08,
        "largest_trade_net_profit_share": 0.3,
        "unresolved_position_count": 0,
    }
    result.update(changes)
    return result


def test_configuration_freezes_twelve_routes_and_no_execution_authorization():
    declaration = runner_declaration()
    configuration = discovery_runner_configuration()

    assert len(ROUTE_ORDER) == 12
    assert declaration["route_order"] == list(ROUTE_ORDER)
    assert declaration["cost_profile_ids"] == list(COST_PROFILE_ORDER)
    assert declaration["discovery_runner_implemented"] is True
    assert declaration["development_run_authorized"] is False
    assert declaration["dataset_opened"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert configuration["trade_slice_attribution"] == "ENTRY_TIMESTAMP"
    assert configuration["slice_boundary_state_reset"] is False
    assert configuration["gap_feature_signal_position_reset"] is True
    assert configuration["performance_comparison_policy"] == "ABSOLUTE_GATES_NO_LEADERBOARD"


@pytest.mark.parametrize(
    "profile_name,change",
    [
        ("baseline", {"closed_trade_count": 7}),
        ("stress", {"slices_with_trade": 2}),
        ("baseline", {"nonnegative_slices": 2}),
        ("baseline", {"net_expectancy_r": 0.099}),
        ("stress", {"net_expectancy_r": -0.001}),
        ("baseline", {"profit_factor": 1.19}),
        ("stress", {"profit_factor": 0.99}),
        ("baseline", {"maximum_marked_drawdown_fraction": 0.121}),
        ("stress", {"maximum_marked_drawdown_fraction": 0.181}),
        ("stress", {"largest_trade_net_profit_share": 0.401}),
        ("baseline", {"unresolved_position_count": 1}),
    ],
)
def test_each_frozen_route_gate_fails_closed(profile_name, change):
    baseline = _profile()
    stress = _profile(net_expectancy_r=0.1, profit_factor=1.1, maximum_marked_drawdown_fraction=0.1)
    (baseline if profile_name == "baseline" else stress).update(change)

    result = evaluate_route_interest(baseline, stress)

    assert result["eligible"] is False
    assert result["action"] == "HOLD_CASH"


def test_infinite_profit_factor_with_positive_profit_can_pass_absolute_gate():
    baseline = _profile(profit_factor=None, profit_factor_is_infinite=True)
    stress = _profile(profit_factor=None, profit_factor_is_infinite=True, net_expectancy_r=0.1)

    assert evaluate_route_interest(baseline, stress)["eligible"] is True


def test_no_trade_profit_factor_is_zero_for_gate_and_fails_closed():
    baseline = _profile(profit_factor=None, profit_factor_is_infinite=False)
    stress = _profile(profit_factor=None, profit_factor_is_infinite=False)

    result = evaluate_route_interest(baseline, stress)

    assert result["eligible"] is False
    assert result["checks"]["minimum_baseline_profit_factor"] is False


def test_round_gate_requires_two_assets_and_never_selects_winner():
    def route(route_id, asset, eligible):
        return {"route_id": route_id, "asset": asset, "interest_gate": {"eligible": eligible}}

    failed = summarize_round_interest([
        route("BTC-USD|A", "BTC-USD", True),
        route("BTC-USD|B", "BTC-USD", True),
    ])
    passed = summarize_round_interest([
        route("BTC-USD|A", "BTC-USD", True),
        route("ETH-USD|A", "ETH-USD", True),
    ])

    assert failed["round_interest_gate_passed"] is False
    assert failed["status"].endswith("NO_INTEREST_HOLD_CASH")
    assert passed["round_interest_gate_passed"] is True
    assert passed["automatic_ranking_generated"] is False
    assert passed["automatic_strategy_selection"] is False


def test_multiple_passing_families_for_one_asset_require_separate_review():
    routes = [
        {"route_id": "BTC-USD|A", "asset": "BTC-USD", "interest_gate": {"eligible": True}},
        {"route_id": "BTC-USD|B", "asset": "BTC-USD", "interest_gate": {"eligible": True}},
        {"route_id": "ETH-USD|A", "asset": "ETH-USD", "interest_gate": {"eligible": True}},
    ]

    result = summarize_round_interest(routes)

    assert result["round_interest_gate_passed"] is True
    assert result["next_action"] == "SEPARATE_PORTFOLIO_REVIEW_REQUIRED"
    assert result["same_asset_multiple_eligible_routes"] == {
        "BTC-USD": ["BTC-USD|A", "BTC-USD|B"]
    }


class _CapitulationSignalEngine:
    def generate(self, family, frame):
        result = frame.copy(deep=True)
        hypothesis = next(item for item in ROUND_1_HYPOTHESES if item["family_id"] == family)
        for column, value in (
            (FAMILY_COLUMN, family),
            (HYPOTHESIS_COLUMN, hypothesis["hypothesis_id"]),
            (FEATURES_AVAILABLE_COLUMN, False),
            (SIGNAL_CONDITION_COLUMN, False),
            (STATE_AFTER_COLUMN, STATE_FLAT),
            (TRANSITION_COLUMN, "FLAT_WAIT"),
            (ACTION_INTENT_COLUMN, INTENT_NONE),
            (SETUP_TIMESTAMP_COLUMN, frame.index[0]),
            (SETUP_LOW_COLUMN, 90.0),
            (SIGNAL_ATR_COLUMN, 4.0),
            (TARGET_ANCHOR_COLUMN, 150.0),
            (PRIOR_CLOSE_LOW_10_COLUMN, 80.0),
        ):
            result[column] = value
        first = result.index[0]
        result.loc[first, FEATURES_AVAILABLE_COLUMN] = True
        result.loc[first, SIGNAL_CONDITION_COLUMN] = True
        result.loc[first, TRANSITION_COLUMN] = "CAPITULATION_CONFIRMATION"
        result.loc[first, ACTION_INTENT_COLUMN] = ENTER_NEXT_OPEN
        result.loc[first, SETUP_TIMESTAMP_COLUMN] = first - pd.Timedelta(days=1)
        return result


def test_profile_executes_following_open_and_entry_bar_target_without_force_close():
    index = pd.date_range("2019-01-02", periods=2, freq="D", tz="UTC")
    frame = pd.DataFrame(
        {
            "Open": [100.0, 100.0],
            "High": [102.0, 200.0],
            "Low": [98.0, 99.0],
            "Close": [100.0, 150.0],
            "Volume": [1000.0, 1000.0],
        },
        index=index,
    )
    runner = KrakenAIDrivenV2Round1DiscoveryRunner(signal_engine_factory=_CapitulationSignalEngine)

    result = runner._simulate_profile(
        "BTC-USD", "CAPITULATION_RECOVERY", (frame,), BASELINE_COST_PROFILE_ID
    )

    assert result["signal_count"] == 1
    assert result["approved_entry_count"] == 1
    assert result["closed_trade_count"] == 1
    assert result["closed_trade_ledger"][0]["entry_timestamp"] == index[1].isoformat()
    assert result["closed_trade_ledger"][0]["exit_timestamp"] == index[1].isoformat()
    assert result["unresolved_position_count"] == 0
    assert result["synthetic_terminal_force_close_executed"] is False


def test_open_position_at_gap_halts_profile_without_synthetic_exit():
    first_index = pd.date_range("2019-01-02", periods=2, freq="D", tz="UTC")
    second_index = pd.date_range("2019-01-05", periods=2, freq="D", tz="UTC")
    segments = tuple(
        pd.DataFrame(
            {
                "Open": [100.0, 100.0],
                "High": [101.0, 101.0],
                "Low": [99.0, 99.0],
                "Close": [100.0, 100.0],
                "Volume": [1000.0, 1000.0],
            },
            index=index,
        )
        for index in (first_index, second_index)
    )
    runner = KrakenAIDrivenV2Round1DiscoveryRunner(signal_engine_factory=_CapitulationSignalEngine)

    result = runner._simulate_profile(
        "BTC-USD", "CAPITULATION_RECOVERY", segments, BASELINE_COST_PROFILE_ID
    )

    assert result["path_completed"] is False
    assert result["status"].endswith("INCONCLUSIVE_OPEN_POSITION_AT_GAP")
    assert result["unresolved_position_count"] == 1
    assert result["unresolved_positions"][0]["boundary"] == "KNOWN_GAP"
    assert result["closed_trade_count"] == 0
    assert result["synthetic_terminal_force_close_executed"] is False


class _FailIfRead:
    def __init__(self):
        self.called = False

    def read(self, _):
        self.called = True
        raise AssertionError("reader must remain closed")


def test_wrong_authorization_fails_before_dataset_or_evidence_access(tmp_path):
    reader = _FailIfRead()
    runner = KrakenAIDrivenV2Round1DiscoveryRunner(dataset_reader=reader)

    with pytest.raises(PermissionError, match="Exact Round 1 discovery"):
        runner.run(tmp_path / "dataset", tmp_path / "evidence", "WRONG")

    assert reader.called is False
    assert not (tmp_path / "evidence").exists()


def _synthetic_execution():
    routes = []
    for route_id in ROUTE_ORDER:
        asset, family = route_id.split("|")
        routes.append(
            {
                "route_id": route_id,
                "asset": asset,
                "family_id": family,
                "profiles": {},
                "interest_gate": {"eligible": False, "action": "HOLD_CASH", "checks": {}},
            }
        )
    round_interest = summarize_round_interest(routes)
    return {
        "status": round_interest["status"],
        "development_rows": {asset: 0 for asset in ASSET_ORDER},
        "continuous_segment_rows": {asset: [] for asset in ASSET_ORDER},
        "route_order": list(ROUTE_ORDER),
        "route_results": routes,
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


class _LockedReader:
    def read(self, _):
        empty = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        return LockedDevelopmentDataset(
            dataset_id=DATASET_ID,
            manifest_sha256=DATASET_MANIFEST_SHA256,
            source_mode="OFFICIAL_OHLCVT_ARCHIVES_ONLY",
            development_frames={asset: empty for asset in ASSET_ORDER},
            asset_file_sha256={asset: "a" * 64 for asset in ASSET_ORDER},
            full_observed_rows={asset: 0 for asset in ASSET_ORDER},
            opaque_non_development_rows={asset: 0 for asset in ASSET_ORDER},
            calibration_rows_parsed=0,
            evaluation_rows_parsed=0,
        )


class _EvidenceRunner(KrakenAIDrivenV2Round1DiscoveryRunner):
    def execute_development(self, frames):
        assert tuple(frames) == ASSET_ORDER
        return _synthetic_execution()


def test_exact_authorization_records_canonical_one_shot_evidence(tmp_path):
    dataset = tmp_path / "dataset"
    evidence = tmp_path / "evidence"
    dataset.mkdir()
    runner = _EvidenceRunner(dataset_reader=_LockedReader())

    recorded = runner.run(dataset, evidence, AUTHORIZATION_PHRASE)
    final = evidence / EVIDENCE_DIRECTORY_NAME
    locked = KrakenAIDrivenV2Round1DiscoveryEvidenceLock().lock(final)

    assert recorded.report_sha256 == locked.report_sha256
    assert hashlib.sha256((final / REPORT_FILENAME).read_bytes()).hexdigest() == recorded.report_sha256
    assert (final / REPORT_SHA256_FILENAME).exists()
    assert locked.report["calibration_rows_parsed"] == 0
    assert locked.report["evaluation_rows_parsed"] == 0
    assert locked.report["automatic_ranking_generated"] is False
    with pytest.raises(FileExistsError, match="already exists"):
        runner.run(dataset, evidence, AUTHORIZATION_PHRASE)
