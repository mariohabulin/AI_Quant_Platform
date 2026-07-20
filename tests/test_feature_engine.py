import pandas as pd

from src.feature_engine import generate_features
from src.strategies.ema_strategy import generate_signals


data = pd.read_csv("data/AAPL.csv")

feature_data = generate_features(data)

result = generate_signals(feature_data)

print(result[["Date", "Close", "EMA_20", "EMA_50", "Signal"]].tail(20))

print("\nSignal counts:")
print(result["Signal"].value_counts())

print("\nDataset shape:")
print(result.shape)