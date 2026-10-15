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
        # The outputs the plant has reached, to keep forecasts realistic.
        self.lowest, self.highest = y.min(), y.max()
        return self

    def forecast(self, weather):
        """The output in MW for each hour of a weather forecast: a dict of each
        measurement by name, for one hour or for many."""
        columns = [weather[name] for name in sorted(weather)]
        X = np.array(columns, dtype=float).T
        # Skip hours the weather service has no forecast for.
        X = X[~np.isnan(X).any(axis=1)]
        return np.clip(self.model.predict(X), self.lowest, self.highest)
