`pd.Series(fit_yes).groupby(fit_values.to_numpy())` groups the answers by value: its `sum()` counts each value's yes, and its `count()` its calls. `values.map(shares)` looks each value up, and gives NaN for a value the fit calls never had.

---

Start `cross_fit` from `np.empty(len(values))`, and fill `encoded[held]` for each split from `values.iloc[fit]` and `said_yes[fit]`.
