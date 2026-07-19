from strategies.ema_strategy import generate_signals as ema_strategy


STRATEGIES = {
    "EMA": ema_strategy,
}


def get_strategy(name):

    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}")

    return STRATEGIES[name]


def list_strategies():

    return list(STRATEGIES.keys())