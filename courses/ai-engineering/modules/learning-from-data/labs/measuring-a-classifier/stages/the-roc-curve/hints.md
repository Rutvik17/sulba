Sort the candidates by score, highest first, with `np.argsort(-scores)`. Running down the sorted list, `np.cumsum` of the labels counts the pulsars flagged so far, and `np.cumsum` of `1 - y` the other candidates.

---

A threshold flags everything down to the last candidate with its score. Where `ranked[i] != ranked[i + 1]`, position `i` is the last of its score; the final position always is. Divide the counts there by the totals, and put `0` in front of each rate and `np.inf` in front of the thresholds.

---

Each step of the curve adds a trapezoid: its width `fpr[i] - fpr[i - 1]` times its mean height `(tpr[i] + tpr[i - 1]) / 2`.
