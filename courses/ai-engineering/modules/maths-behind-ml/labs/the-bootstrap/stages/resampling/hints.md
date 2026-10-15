`values[rows]`, with `rows` from `resample`, gives an array with a row for each resample, and `statistic(..., axis=-1)` works out each row's value.

---

`np.std(distribution, ddof=1)` puts `n - 1` in the divisor.
