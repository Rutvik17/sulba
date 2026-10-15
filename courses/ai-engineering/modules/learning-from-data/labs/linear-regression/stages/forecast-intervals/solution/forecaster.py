"""Forecasts the plant's output for each hour from the weather, with scikit-learn."""

import numpy as np
from sklearn.linear_model import LinearRegression

# The weather measurements, in the order of the history's columns.
COLUMNS = ["temperature", "vacuum", "pressure", "humidity"]


class Forecaster:
    def fit(self, X, y):
        """Fits on the plant's history: a row of weather per hour, in COLUMNS order, and
        that hour's output in MW."""
        self.model = LinearRegression().fit(X, y)
        return self

    def forecast(self, weather):
        """The output in MW for each hour of a weather forecast: a dict of each
        measurement by name, for one hour or for many."""
        columns = [weather[name] for name in COLUMNS]
        X = np.column_stack(columns).astype(float)
        missing = np.isnan(X).any(axis=1)
        if missing.any():
            raise ValueError(f"No weather for hours {np.flatnonzero(missing).tolist()}")
        return self.model.predict(X)


def halfwidth(misses, coverage=0.9):
    """How far either side of a forecast its interval reaches, from the misses on n
    hours the model didn't fit: the ceil((n + 1) * coverage)-th smallest miss size, or
    inf when that is more than n."""
    sizes = np.sort(np.abs(np.asarray(misses, dtype=float)))
    rank = int(np.ceil((len(sizes) + 1) * coverage))
    return float(sizes[rank - 1]) if rank <= len(sizes) else float("inf")


def intervals(forecaster, weather, q):
    """The low and high ends of each hour's interval, as (low, high)."""
    forecasts = forecaster.forecast(weather)
    return forecasts - q, forecasts + q
