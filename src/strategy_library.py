class StrategyLibrary:
    """Central registry for all available trading strategies."""

    def __init__(self):
        self._strategies = {}

    def _validate_strategy(self, strategy):
        """Validate a strategy before registration."""
        if strategy is None:
            raise ValueError("Strategy cannot be None.")

        if not hasattr(strategy, "name"):
            raise ValueError("Strategy must have a 'name' attribute.")

        if not hasattr(strategy, "required_features"):
            raise ValueError(
                "Strategy must have a 'required_features' attribute."
            )

        if not callable(getattr(strategy, "generate_signals", None)):
            raise ValueError(
                "Strategy must implement 'generate_signals()'."
            )

    def register(self, strategy):
        """Register a new trading strategy."""

        self._validate_strategy(strategy)

        if strategy.name in self._strategies:
            raise ValueError(
                f"Strategy '{strategy.name}' is already registered."
            )

        self._strategies[strategy.name] = strategy

        

    def get(self, name):
        """Return a registered strategy by name."""

        if name not in self._strategies:
            raise ValueError(
                f"Strategy '{name}' is not registered."
            )

        return self._strategies[name]

    def exists(self, name):
        """Check whether a strategy is registered."""

        return name in self._strategies

    def list(self):
        """Return all registered strategy names."""

        return list(self._strategies.keys()) 

    def count(self):
        """Return the number of registered strategies."""

        return len(self._strategies)   

        