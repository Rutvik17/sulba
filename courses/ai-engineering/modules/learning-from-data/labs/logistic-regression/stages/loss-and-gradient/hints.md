`np.clip(p, 1e-15, 1 - 1e-15)` keeps `p` away from 0 and 1, so `np.log` never sees 0.

---

Both derivatives start from the errors `p - y`, where `p` is `predict_proba(X, w, b)`: `X.T @ (p - y) / n` for the weights, and their mean for the bias.

---

The l2 term, `l2 / 2 * (w @ w)`, adds `l2 * w` to the weights' derivative and nothing to the bias's.
