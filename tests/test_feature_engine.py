import os
import sys

import pandas as pd

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from feature_engine import generate_features


def test_generate_features():
    data = pd.DataFrame({
        "Open": [99, 100, 101],
        "High": [101, 102, 103],
        "Low": [98, 99, 100],
        "Close": [100, 101, 102],
        "Volume": [1000, 1100, 1200],
    })

    result = generate_features(data)

    assert isinstance(result, pd.DataFrame)

    expected_columns = {
        "EMA_20",
        "EMA_50",
        "RETURN_1",
        "VOLATILITY_20",
        "RSI_14",
        "VOLUME_MA_20",
    }

    assert expected_columns.issubset(result.columns)
