from data_loader import download_data
from backtest import run_backtest
from strategy_manager import get_strategy


def optimize():

    print("\nSearching for the best EMA combination...\n")

    # Učitaj podatke samo jednom
    df = download_data()

    # Dohvati strategiju preko Strategy Managera
    strategy = get_strategy("EMA")

    best_return = float("-inf")
    best_fast = None
    best_slow = None

    for fast in range(5, 21):

        for slow in range(25, 81):

            if fast >= slow:
                continue

            # Kreiraj signale za ovu kombinaciju
            test_df = strategy(
                df.copy(),
                fast_ema=fast,
                slow_ema=slow
            )

            # Pokreni backtest
            result = run_backtest(test_df)

            # Zapamti najbolji rezultat
            if result["return"] > best_return:

                best_return = result["return"]
                best_fast = fast
                best_slow = slow

    print("\n" + "=" * 40)
    print("BEST EMA COMBINATION")
    print("=" * 40)

    print(f"Fast EMA : {best_fast}")
    print(f"Slow EMA : {best_slow}")
    print(f"Return   : {best_return:.2f}%")

    return {
        "fast_ema": best_fast,
        "slow_ema": best_slow,
        "return": best_return,
    }


if __name__ == "__main__":
    optimize()