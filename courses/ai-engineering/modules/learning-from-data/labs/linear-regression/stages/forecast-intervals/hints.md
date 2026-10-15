`np.abs` gives each miss's size, and `np.sort` puts the sizes in order, smallest first.

---

`np.ceil((n + 1) * coverage)` is the rank. The size at that rank is at index `rank - 1`.

---

`intervals` needs the forecasts once: `forecasts = forecaster.forecast(weather)`, then `forecasts - q` and `forecasts + q`.
