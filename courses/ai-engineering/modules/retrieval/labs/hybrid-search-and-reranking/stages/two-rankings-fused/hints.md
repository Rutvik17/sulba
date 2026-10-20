`vectors @ question` gives every row's dot product at once, in whole numbers when both are int64. `np.argsort(-scores, kind="stable")` puts the highest first and keeps tied rows in their order.

---

A ranking lists rows in order, so the row at position `i` has rank `i + 1`. `total[ranking] += 1 / (k + np.arange(1, len(ranking) + 1))` adds each row's share in one step, into an array of zeros with a place for every row.

---

`relevant_rows.isdisjoint(ranking[:k].tolist())` is `False` when a relevant row is among the first `k`.
