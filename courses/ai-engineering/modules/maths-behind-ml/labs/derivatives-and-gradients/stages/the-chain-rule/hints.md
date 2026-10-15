`W1, b1, w2, b2 = params` unpacks the weights. The scores are `s = np.tanh(Z @ W1 + b1) @ w2 + b2`, and the loss is the mean of `np.logaddexp(0, s) - y * s`.

---

Run the forward pass again inside `network_gradient`, keeping `hidden = np.tanh(Z @ W1 + b1)` and the scores `s`. The probability is `$\sigma(s) = 1/(1 + e^{-s})$`, and `ds = (p - y) / len(y)` is the loss's slope along each score.

---

`dw2` is `hidden.T @ ds`, and `db2` is `ds.sum()`. Back in the hidden layer, `np.outer(ds, w2)` is the slope along each hidden output, and multiplying it by `1 - hidden**2` carries it back through tanh.

---

`dW1` is `Z.T @ dpre`, and `db1` adds `dpre` up over the samples: `dpre.sum(axis=0)`.
