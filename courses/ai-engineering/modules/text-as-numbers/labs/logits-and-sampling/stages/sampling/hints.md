`np.cumsum(probabilities)` gives the running totals. `rng.choice` divides them by the last one, so that they end at exactly 1 however the probabilities were rounded.

---

`np.searchsorted(totals, u, side="right")` gives the index of the first total greater than `u`.
