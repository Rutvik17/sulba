`X_train.mean(axis=0)` and `X_train.std(axis=0)` give one number per column. Use them for both sets.

---

Start with `w = np.zeros(X.shape[1])` and `b = 0.0`, then loop `steps` times: get the gradient, then step against it.

---

After each step, append `log_loss(y, predict_proba(X, w, b)) + l2 / 2 * (w @ w)` to the losses.
