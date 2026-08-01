import os
import sys
import pandas as pd

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from strategy_engine import StrategyEngine
from strategies.ema_strategy import EMAStrategy
from strategy_library import StrategyLibrary
def test_strategy_name():
    library = StrategyLibrary()

    strategy = EMAStrategy()
    library.register(strategy)

    engine = StrategyEngine(library, strategy.name)

    assert engine.strategy_name == "ema_crossover"

def test_run_returns_dataframe():
    data = pd.read_csv("data/AAPL.csv")

    library = StrategyLibrary()

    strategy = EMAStrategy()
    library.register(strategy)

    engine = StrategyEngine(library, strategy.name)

    result = engine.run(data)

    assert isinstance(result, pd.DataFrame)

def test_empty_dataframe_raises_error():
    library = StrategyLibrary()

    strategy = EMAStrategy()
    library.register(strategy)

    engine = StrategyEngine(library, strategy.name)

    empty_data = pd.DataFrame()

    try:
        engine.run(empty_data)
        assert False, "Expected ValueError was not raised."
    except ValueError:
        pass

def test_unknown_strategy_raises_error():
    library = StrategyLibrary()

    try:
        StrategyEngine(library, "unknown_strategy")
        assert False, "Expected ValueError was not raised."
    except ValueError:
        pass

class StrategyWithoutName:
    def generate_signals(self, data):
        return data
    


class StrategyWithoutGenerateSignals:
     name = "dummy_strategy"



class StrategyWithoutSignalColumn:
    name = "dummy_strategy"
    required_features = []


    def generate_signals(self, data):
        return pd.DataFrame({"Close": [100, 101, 102]})
    
def test_strategy_without_signal_column_raises_error():
    data = pd.read_csv("data/AAPL.csv")

    library = StrategyLibrary()

    strategy = StrategyWithoutSignalColumn()
    library.register(strategy)

    engine = StrategyEngine(library, strategy.name)

    try:
        engine.run(data)
        assert False, "Expected ValueError was not raised."
    except ValueError:
        pass

class StrategyWithInvalidSignals:
    name = "dummy_strategy"
    required_features = []

    def generate_signals(self, data):
        return pd.DataFrame({
            "Signal": [0, 1, 2]
        })
    
def test_invalid_signal_values_raise_error():
    data = pd.read_csv("data/AAPL.csv")

    library = StrategyLibrary()

    strategy = StrategyWithInvalidSignals()
    library.register(strategy)

    engine = StrategyEngine(library, strategy.name)

    try:
        engine.run(data)
        assert False, "Expected ValueError was not raised."
    except ValueError:
        pass

def test_non_dataframe_input_raises_error():
    library = StrategyLibrary()

    strategy = EMAStrategy()
    library.register(strategy)

    engine = StrategyEngine(library, strategy.name)

    try:
        engine.run([1, 2, 3])
        assert False, "Expected TypeError was not raised."
    except TypeError:
        pass

class StrategyReturningNonDataFrame:
    name = "dummy_strategy"
    required_features = []

    def generate_signals(self, data):
        return [0, 1, -1]
    
def test_non_dataframe_result_raises_error():
    data = pd.read_csv("data/AAPL.csv")

    library = StrategyLibrary()

    strategy = StrategyReturningNonDataFrame()
    library.register(strategy)

    engine = StrategyEngine(library, strategy.name)

    try:
        engine.run(data)
        assert False, "Expected TypeError was not raised."
    except TypeError:
        pass

if __name__ == "__main__": 
    test_strategy_name()
    print("✅ test_strategy_name PASSED")

    test_run_returns_dataframe()
    print("✅ test_run_returns_dataframe PASSED")

    test_empty_dataframe_raises_error()
    print("✅ test_empty_dataframe_raises_error PASSED")

    test_none_strategy_raises_error()
    print("✅ test_none_strategy_raises_error PASSED")

    test_strategy_without_name_raises_error()
    print("✅ test_strategy_without_name_raises_error PASSED")

    test_strategy_without_generate_signals_raises_error()
    print("✅ test_strategy_without_generate_signals_raises_error PASSED")

    test_strategy_without_signal_column_raises_error()
    print("✅ test_strategy_without_signal_column_raises_error PASSED")

    test_invalid_signal_values_raise_error()
    print("✅ test_invalid_signal_values_raise_error PASSED")

    test_non_dataframe_input_raises_error()
    print("✅ test_non_dataframe_input_raises_error PASSED")

    test_non_dataframe_result_raises_error()
    print("✅ test_non_dataframe_result_raises_error PASSED")

def test_run_uses_strategy_required_features(monkeypatch):
    data = pd.DataFrame(
        {
            "Close": [100, 101, 102],
        }
    )

    library = StrategyLibrary()

    strategy = EMAStrategy(
        fast_period=10,
        slow_period=30,
    )
    library.register(strategy)

    captured_required_features = None

    def fake_generate_features(data, required_features=None):
        nonlocal captured_required_features

        captured_required_features = required_features

        result = data.copy()
        result["EMA_10"] = [99, 100, 101]
        result["EMA_30"] = [101, 100, 99]

        return result

    monkeypatch.setattr(
        "strategy_engine.generate_features",
        fake_generate_features,
    )

    engine = StrategyEngine(library, strategy.name)

    engine.run(data)

    assert captured_required_features == strategy.required_features
  