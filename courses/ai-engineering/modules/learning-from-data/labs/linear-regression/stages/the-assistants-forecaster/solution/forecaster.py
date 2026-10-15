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
