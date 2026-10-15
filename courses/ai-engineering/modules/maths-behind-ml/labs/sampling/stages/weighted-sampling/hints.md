`np.cumsum(weights)` gives the running totals, and its last value is the total. `np.searchsorted(totals, u, side="right")` gives, for each `u`, the first row whose running total is above it.

---

`np.unique(labels, return_inverse=True, return_counts=True)` gives the number of records with each label, and for each record where its label sits among them, so `counts[inverse]` is the size of each record's class.

---

The probabilities are the weights over their total. `values[batch] / (n * probabilities[batch])` gives each row's value counted as the brief says.
