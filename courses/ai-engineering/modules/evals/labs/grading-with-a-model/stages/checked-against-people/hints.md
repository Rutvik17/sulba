`labels == verdicts` gives an array of `True` and `False`, whose mean is the accuracy.

---

`ones[:, None] > zeros[None, :]` compares every reply labelled 1 with every reply labelled 0 at once.

---

`np.unique(scores)` gives each score once, lowest first, so the first that reaches the highest kappa is the lowest.
