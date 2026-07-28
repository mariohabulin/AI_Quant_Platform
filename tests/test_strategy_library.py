from src.strategy_library import StrategyLibrary
from src.strategies.ema_strategy import EMAStrategy


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
 