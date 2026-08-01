import pytest

from src.strategy_library import StrategyLibrary
from src.strategies.ema_strategy import EMAStrategy


class StrategyWithoutRequiredFeatures:
    name = "strategy_without_required_features"

    def generate_signals(self, data):
        return data





def test_register_strategy():
    library = StrategyLibrary()
    strategy = EMAStrategy()

    library.register(strategy)

    assert strategy.name in library._strategies

def test_get_strategy():
    library = StrategyLibrary()

    strategy = EMAStrategy()

    library.register(strategy)

    result = library.get(strategy.name)

    assert result is strategy

def test_strategy_exists():
    library = StrategyLibrary()
    strategy = EMAStrategy()

    library.register(strategy)

    assert library.exists(strategy.name) is True

def test_list_strategies():
    library = StrategyLibrary()

    strategy = EMAStrategy()

    library.register(strategy)

    assert library.list() == [strategy.name]

def test_strategy_count():
    library = StrategyLibrary()

    assert library.count() == 0

    strategy = EMAStrategy()
    library.register(strategy)

    assert library.count() == 1

import pytest

def test_duplicate_strategy_registration():
    library = StrategyLibrary()

    strategy = EMAStrategy()

    library.register(strategy)

    with pytest.raises(ValueError):
        library.register(strategy)

def test_get_unknown_strategy():
    library = StrategyLibrary()

    with pytest.raises(ValueError):
        library.get("UnknownStrategy")

def test_strategy_without_required_features_cannot_be_registered():
    library = StrategyLibrary()
    strategy = StrategyWithoutRequiredFeatures()

    with pytest.raises(
        ValueError,
        match="Strategy must have a 'required_features' attribute.",
    ):
        library.register(strategy) 

class StrategyWithNonCallableGenerateSignals:
    name = "non_callable_strategy"
    required_features = []
    generate_signals = "not a method"


def test_strategy_generate_signals_must_be_callable():
    library = StrategyLibrary()
    strategy = StrategyWithNonCallableGenerateSignals()

    with pytest.raises(
        ValueError,
        match=r"Strategy must implement 'generate_signals\(\)'.",
    ):
        library.register(strategy)