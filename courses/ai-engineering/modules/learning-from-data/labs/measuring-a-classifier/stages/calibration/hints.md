`np.linspace(0, 1, bins + 1)` gives the edges, and `np.searchsorted` on the edges between the first and the last gives each probability's bin, with a probability on an edge going to the bin below it.

---

`np.bincount(which, minlength=bins)` counts each bin's candidates, and with `weights=` it adds up their labels or their probabilities. Keep the bins whose count isn't 0.
