`X_train.mean(axis=0)` and `X_train.std(axis=0)` give one number per column. Use them for both sets.

---

With `error = predict(X, w, b) - y`, the derivative with respect to `w` is `2 * X.T @ error / len(y)`, and with respect to `b` it is `2 * np.mean(error)`.

---

Start with `w = np.zeros(X.shape[1])` and `b = float(np.mean(y))`. Then loop `steps` times: get the gradient, step against it, and append `mse(y, predict(X, w, b))` to the losses.
