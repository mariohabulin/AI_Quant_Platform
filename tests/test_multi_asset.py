import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from multi_asset import MultiAssetValidationPolicy, MultiAssetValidator
from validation_pipeline import ValidationPolicy


class RepeatedTradeEngine:
    strategy_name = "RepeatedTrade"
    def run(self, data):
        result = data.copy(); result["Signal"] = 0
        for position in range(0, len(result) - 1, 2):
            result.iloc[position, result.columns.get_loc("Signal")] = 1
            result.iloc[position + 1, result.columns.get_loc("Signal")] = -1
        return result


def market_data(rows=80, slope=1.0):
    index = pd.date_range("2024-01-01", periods=rows, freq="D")
    prices = [100 + slope * i for i in range(rows)]
    return pd.DataFrame({"Open": prices, "High": [p+1 for p in prices], "Low": [p-1 for p in prices], "Close": prices, "Volume": [1000]*rows}, index=index)


def fake_result(status):
    return {"classification": {"status": status}}


def test_policy_validates_broad_cross_asset_evidence():
    assets = {f"A{i}": fake_result(ValidationPolicy.VALIDATED) for i in range(5)}
    result = MultiAssetValidationPolicy().classify(assets)
    assert result["status"] == "VALIDATED"
    assert result["rates"]["validated"] == 1.0


def test_policy_marks_mixed_evidence_conditional():
    assets = {"A": fake_result("VALIDATED"), "B": fake_result("CONDITIONAL"), "C": fake_result("REJECTED")}
    assert MultiAssetValidationPolicy().classify(assets)["status"] == "CONDITIONAL"


def test_policy_rejects_when_majority_of_assets_are_rejected():
    assets = {"A": fake_result("REJECTED"), "B": fake_result("REJECTED"), "C": fake_result("VALIDATED")}
    assert MultiAssetValidationPolicy().classify(assets)["status"] == "REJECTED"


def test_policy_validates_threshold_boundary():
    assets = {"A": fake_result("VALIDATED"), "B": fake_result("VALIDATED"), "C": fake_result("VALIDATED"), "D": fake_result("CONDITIONAL"), "E": fake_result("REJECTED")}
    result = MultiAssetValidationPolicy(2, 0.60, 0.20).classify(assets)
    assert result["status"] == "VALIDATED"


def test_policy_rejects_invalid_configuration():
    with pytest.raises(ValueError): MultiAssetValidationPolicy(min_assets=1)
    with pytest.raises(TypeError): MultiAssetValidationPolicy(min_validated_asset_rate="0.6")
    with pytest.raises(ValueError): MultiAssetValidationPolicy(max_rejected_asset_rate=1.1)


def test_validator_requires_mapping():
    validator = MultiAssetValidator(RepeatedTradeEngine(), 20, 12, simulations=100)
    with pytest.raises(TypeError): validator.run([])


def test_validator_requires_multiple_assets():
    validator = MultiAssetValidator(RepeatedTradeEngine(), 20, 12, simulations=100)
    with pytest.raises(ValueError, match="at least 2 assets"):
        validator.run({"ONE": market_data()})


def test_validator_rejects_invalid_asset_name_and_data():
    validator = MultiAssetValidator(RepeatedTradeEngine(), 20, 12, simulations=100)
    with pytest.raises(ValueError): validator.run({"": market_data(), "B": market_data()})
    with pytest.raises(TypeError): validator.run({"A": market_data(), "B": [1, 2]})


def test_validator_returns_per_asset_results_and_summary():
    validator = MultiAssetValidator(RepeatedTradeEngine(), 20, 12, step_size=12, simulations=100, random_seed=7)
    result = validator.run({"BBB": market_data(slope=0.8), "AAA": market_data(slope=1.0)})
    assert result["asset_count"] == 2
    assert list(result["assets"]) == ["AAA", "BBB"]
    assert set(result["summary"]) == {"mean_oos_strategy_return", "mean_oos_excess_return", "positive_oos_excess_asset_rate", "mean_walk_forward_positive_excess_rate"}
    assert result["classification"]["status"] in {"VALIDATED", "CONDITIONAL", "REJECTED"}


def test_validator_preserves_strategy_name():
    result = MultiAssetValidator(RepeatedTradeEngine(), 20, 12, simulations=100).run({"A": market_data(), "B": market_data(90, 0.5)})
    assert result["strategy"] == "RepeatedTrade"


def test_validator_is_reproducible():
    kwargs = dict(train_size=20, test_size=12, step_size=12, simulations=100, random_seed=99)
    assets = {"A": market_data(), "B": market_data(slope=0.7)}
    first = MultiAssetValidator(RepeatedTradeEngine(), **kwargs).run(assets)
    second = MultiAssetValidator(RepeatedTradeEngine(), **kwargs).run(assets)
    assert first == second


def test_validator_propagates_execution_costs_to_every_asset():
    result = MultiAssetValidator(RepeatedTradeEngine(), 20, 12, commission_rate=0.001, slippage_rate=0.001, spread_rate=0.002, simulations=100).run({"A": market_data(), "B": market_data(slope=0.6)})
    for asset in result["assets"].values():
        assert asset["out_of_sample"]["out_of_sample"]["trade_history"][0]["total_costs"] > 0


def test_validator_does_not_mutate_input_frames():
    assets = {"A": market_data(), "B": market_data(slope=0.6)}
    originals = {k: v.copy(deep=True) for k, v in assets.items()}
    MultiAssetValidator(RepeatedTradeEngine(), 20, 12, simulations=100).run(assets)
    for name in assets:
        pd.testing.assert_frame_equal(assets[name], originals[name])


def test_validator_propagates_next_bar_open_to_every_asset():
    result = MultiAssetValidator(
        RepeatedTradeEngine(),
        20,
        12,
        simulations=100,
        execution_timing="next_bar_open",
    ).run({"A": market_data(), "B": market_data(slope=0.6)})

    for asset in result["assets"].values():
        assert asset["out_of_sample"]["out_of_sample"][
            "execution_timing"
        ] == "next_bar_open"
        assert asset["walk_forward"]["windows"][0]["test"][
            "execution_timing"
        ] == "next_bar_open"
