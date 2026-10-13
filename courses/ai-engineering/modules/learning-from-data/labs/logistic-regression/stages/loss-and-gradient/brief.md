Add the loss and its gradient to `model.py`.

`log_loss` is the mean cross-entropy of the labels `y` and the probabilities `p`. Clip `p` to `[1e-15, 1 - 1e-15]` first, so a sure, wrong prediction costs a large but finite amount.

`gradient` returns the derivatives of `log_loss(y, predict_proba(X, w, b)) + l2 / 2 * (w @ w)` with respect to `w` and `b`, as a pair `(dw, db)`. The `l2` term keeps the weights small.

```
log_loss(y, p) -> float
gradient(X, y, w, b, l2=0.0) -> (dw, db)
```
