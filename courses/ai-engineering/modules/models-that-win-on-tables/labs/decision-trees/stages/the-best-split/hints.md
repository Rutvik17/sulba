`np.argsort(column)` gives the order of the calls by the column's values. With `column` and `said_yes` both in that order, `np.cumsum` of the sorted `said_yes` counts the yes calls up to each position.

---

A threshold after position `i` of the sorted calls leaves `i + 1` calls on the left. `left = np.arange(1, n)` and `right = n - left` count both sides of every threshold at once, and `np.cumsum(labels)[:-1]` the yes calls on the left, so one call of `gini` gives every side's impurity.

---

Rule out the thresholds that can't be used: where `values[1:] > values[:-1]` is False, the threshold would fall between equal values, and where `left` or `right` is under `min_leaf`, a side is too small. `np.argmin` over the impurities that remain gives the first of any tied, the lowest threshold.
