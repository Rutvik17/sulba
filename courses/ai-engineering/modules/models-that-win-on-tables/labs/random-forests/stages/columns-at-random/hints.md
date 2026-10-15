`np.array([tree.predict_proba(X)[:, 1] for tree in trees])` has a row for each tree, and `np.cumsum` down its rows adds up the first 1, 2, ... trees' shares.

---

Dividing the cumulative sums by `np.arange(1, len(trees) + 1)[:, None]` gives each row's mean over the first k trees, one row for each k.
