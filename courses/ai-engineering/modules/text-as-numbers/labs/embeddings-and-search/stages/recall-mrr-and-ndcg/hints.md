`relevant[ranked[:k]]` holds, for each of the first `k` products, whether it's relevant. `np.flatnonzero` gives the positions of the true ones, counting from 0.

---

`1 / np.log2(np.arange(2, k + 2))` holds the first `k` discounts. The best DCG takes the `k` largest gains, `np.sort(gains)[::-1][:k]`.
