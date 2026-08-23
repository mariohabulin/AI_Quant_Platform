import json
import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import strategy_family_screening as screening_module
from coinbase_research_dataset import (
    CoinbaseResearchDatasetBuilder,
    CoinbaseResearchDatasetContract,
)
from first_strategy_candidate import (
    BASELINE_COSTS,
    STRESSED_COSTS,
    first_candidate_configuration,
)
from strategy_family_screening import (
    DEVELOPMENT_MANIFEST_SHA256,
    SCREENING_ID,
    SCREENING_OUTCOMES,
    SCREENING_SPECS,
    STRATEGY_FAMILY_SCREENING_SCHEMA_VERSION,
    StrategyFamilyScreeningPreregistration,
    main,
    screening_configuration,
    screening_strategy_engines,
)

EXPECTED_STRATEGIES = (
    "adx",
    "atr",
    "bollinger",
    "donchian",
    "macd",
    "rsi",
    "stochastic",
    "supertrend",
)


def small_contract():
    return CoinbaseResearchDatasetContract(
        dataset_id="test-screening-native-6h-v1",
        products=("BTC-USD", "ETH-USD"),
        granularity_seconds=21600,
        start="2024-01-01T00:00:00Z",
        end="2024-01-02T00:00:00Z",
    )


def request_for(contract):
    rows = []
    for index, timestamp in enumerate(
        pd.date_range(
            contract.start_timestamp,
            contract.end_timestamp,
            freq="6h",
            inclusive="left",
        )
    ):
        open_price = 100.0 + index
        rows.append(
            [
                int(timestamp.timestamp()),
                open_price - 2.0,
                open_price + 2.0,
                open_price,
                open_price + 1.0,
                10.0 + index,
            ]
        )

    def request(_url, params, timeout):
        assert params["granularity"] == 21600
        assert timeout > 0.0
        return list(reversed(rows))

    return request


def build_dataset(tmp_path, contract=None):
    contract = contract or small_contract()
    result = CoinbaseResearchDatasetBuilder(
        contract=contract,
        request_fn=request_for(contract),
        request_pause_seconds=0.0,
        retry_backoff_seconds=0.0,
        sleep_fn=lambda _seconds: None,
    ).build(tmp_path)
    return contract, result


def test_screening_inventory_freezes_eight_non_ema_defaults():
    assert tuple(spec.strategy_name for spec in SCREENING_SPECS) == EXPECTED_STRATEGIES
    assert all(
        spec.research_status == "UNEVALUATED_RESEARCH_COMPONENT"
        for spec in SCREENING_SPECS
    )
    assert [dict(spec.default_parameters) for spec in SCREENING_SPECS] == [
        {"period": 14, "threshold": 25.0},
        {"period": 14, "multiplier": 1.0},
        {"period": 20, "standard_deviations": 2.0},
        {"period": 20},
        {"fast_period": 12, "slow_period": 26, "signal_period": 9},
        {"period": 14, "oversold": 30, "overbought": 70},
        {"k_period": 14, "d_period": 3, "oversold": 20.0, "overbought": 80.0},
        {"period": 10, "multiplier": 3.0},
    ]


def test_declaration_freezes_scope_without_authorizing_screening():
    declaration = StrategyFamilyScreeningPreregistration().declaration()

    assert declaration["schema_version"] == STRATEGY_FAMILY_SCREENING_SCHEMA_VERSION
    assert declaration["status"] == "STRATEGY_FAMILY_SCREENING_DATASET_LOCK_PENDING"
    assert declaration["screening_id"] == SCREENING_ID
    assert declaration["timeframe"] == "6h"
    assert declaration["assets"] == ["BTC-USD", "ETH-USD"]
    assert declaration["strategy_order"] == list(EXPECTED_STRATEGIES)
    assert declaration["strategy_count"] == 8
    assert declaration["dataset_role"] == "INSPECTED_DEVELOPMENT_ONLY"
    assert declaration["resolution_role"] == "FIXED_RESEARCH_WORKING_RESOLUTION_NOT_WINNER"
    assert declaration["required_manifest_sha256"] == DEVELOPMENT_MANIFEST_SHA256
    assert declaration["screening_executed"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["screening_authorized_before_dataset_lock"] is False
    assert declaration["automatic_ranking_authorized"] is False
    assert declaration["parameter_sweep_authorized"] is False
    assert declaration["strategy_combination_authorized"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["bounded_forward_paper_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_configuration_reuses_frozen_windows_timing_seed_and_costs():
    configuration = screening_configuration()

    assert configuration == first_candidate_configuration()
    assert configuration.train_size == 2880
    assert configuration.test_size == configuration.step_size == 720
    assert configuration.random_seed == 20260822
    assert configuration.execution_timing == "next_bar_open"
    assert configuration.terminal_position_policy == "force_close_at_final_close"
    assert configuration.baseline_costs == BASELINE_COSTS
    assert configuration.stressed_costs == STRESSED_COSTS


def test_interpretation_boundary_is_descriptive_and_has_no_winner_state():
    declaration = StrategyFamilyScreeningPreregistration().declaration()
    policy = declaration["interpretation_policy"]

    assert SCREENING_OUTCOMES == (
        "MECHANISM_RETAINS_INTEREST",
        "SCREEN_OUT",
        "INCONCLUSIVE",
    )
    assert policy["outcomes"] == list(SCREENING_OUTCOMES)
    assert policy["comparison_mode"] == "DESCRIPTIVE_MULTIPLE_COMPARISON_GUARD"
    assert policy["ranking"] == "PROHIBITED"
    assert policy["winner_selection"] == "PROHIBITED"
    assert policy["formal_validation_claim"] == "PROHIBITED"
    assert policy["future_candidate_requires_new_preregistration"] is True
    assert policy["future_candidate_requires_genuinely_unseen_data"] is True


def test_explicit_default_engines_match_frozen_names_and_parameters():
    engines = screening_strategy_engines()

    assert tuple(engines) == EXPECTED_STRATEGIES
    assert all(name == engine.strategy_name for name, engine in engines.items())
    assert engines["adx"].strategy.period == 14
    assert engines["adx"].strategy.threshold == pytest.approx(25.0)
    assert engines["atr"].strategy.multiplier == pytest.approx(1.0)
    assert engines["bollinger"].strategy.standard_deviations == pytest.approx(2.0)
    assert engines["donchian"].strategy.period == 20
    assert engines["macd"].strategy.signal_period == 9
    assert engines["rsi"].strategy.oversold == pytest.approx(30.0)
    assert engines["stochastic"].strategy.d_period == 3
    assert engines["supertrend"].strategy.multiplier == pytest.approx(3.0)


def test_production_manifest_identity_is_exactly_frozen():
    assert DEVELOPMENT_MANIFEST_SHA256 == (
        "6506dd2700b983a134a132890ef4c4ae6e84c0918ba65a5abff6ab2c204c4e7f"
    )


def test_lock_binds_all_engines_to_one_verified_development_dataset(tmp_path):
    contract, result = build_dataset(tmp_path)
    preregistration = StrategyFamilyScreeningPreregistration(
        contract=contract,
        required_manifest_sha256=result["manifest_sha256"],
    )

    locked = preregistration.lock(result["manifest_path"])

    assert locked.manifest_sha256 == result["manifest_sha256"]
    assert locked.contract == contract
    assert locked.configuration == screening_configuration()
    assert tuple(locked.strategy_engines) == EXPECTED_STRATEGIES
    assert set(locked.assets) == {"BTC-USD", "ETH-USD"}
    assert all(len(frame) == 4 for frame in locked.assets.values())


def test_lock_rejects_valid_but_non_frozen_manifest_identity(tmp_path):
    contract, result = build_dataset(tmp_path)
    preregistration = StrategyFamilyScreeningPreregistration(
        contract=contract,
        required_manifest_sha256="0" * 64,
    )

    with pytest.raises(ValueError, match="frozen screening manifest"):
        preregistration.lock(result["manifest_path"])


def test_lock_rejects_asset_tampering_before_any_screening(tmp_path):
    contract, result = build_dataset(tmp_path)
    evidence = result["assets"]["BTC-USD"]
    asset_path = tmp_path / evidence["file"]
    asset_path.write_bytes(asset_path.read_bytes().replace(b"100,102", b"101,102", 1))
    preregistration = StrategyFamilyScreeningPreregistration(
        contract=contract,
        required_manifest_sha256=result["manifest_sha256"],
    )

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        preregistration.lock(result["manifest_path"])


@pytest.mark.parametrize("value", [None, "bad", "0" * 63, "g" * 64])
def test_required_manifest_sha256_must_be_exact_lowercase_hex(value):
    with pytest.raises((TypeError, ValueError), match="manifest SHA-256"):
        StrategyFamilyScreeningPreregistration(
            contract=small_contract(),
            required_manifest_sha256=value,
        )


def test_declaration_cli_prints_pending_non_execution_boundary(capsys):
    assert main([]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "STRATEGY_FAMILY_SCREENING_DATASET_LOCK_PENDING"
    assert output["strategy_count"] == 8
    assert output["screening_executed"] is False
    assert output["candidate_v2_authorized"] is False


def test_lock_cli_validates_data_but_never_runs_screening(
    tmp_path, capsys, monkeypatch
):
    contract, result = build_dataset(tmp_path)
    preregistration = StrategyFamilyScreeningPreregistration(
        contract=contract,
        required_manifest_sha256=result["manifest_sha256"],
    )
    monkeypatch.setattr(
        screening_module,
        "StrategyFamilyScreeningPreregistration",
        lambda: preregistration,
    )

    assert main(["--manifest", str(result["manifest_path"])]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "STRATEGY_FAMILY_SCREENING_LOCKED"
    assert output["manifest_sha256"] == result["manifest_sha256"]
    assert output["asset_rows"] == {"BTC-USD": 4, "ETH-USD": 4}
    assert output["strategy_order"] == list(EXPECTED_STRATEGIES)
    assert output["screening_executed"] is False
    assert output["performance_evaluation_executed"] is False
    assert output["candidate_v2_authorized"] is False
    assert output["bounded_forward_paper_authorized"] is False
    assert output["live_execution_authorized"] is False
