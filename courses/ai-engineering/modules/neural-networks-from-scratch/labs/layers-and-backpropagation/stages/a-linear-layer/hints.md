`forward` keeps the batch on the layer, `self.X = X`, since the backward pass needs it, and returns `X @ self.weight.T + self.bias`. NumPy adds the bias to every row.

---

Write one output out: `$Y_{ij} = \sum_k X_{ik} W_{jk} + b_j$`. The weight `$W_{jk}$` reaches the loss through `$Y_{ij}$` for every sample `$i$`, each time multiplied by `$X_{ik}$`, so its gradient adds `$\frac{\partial L}{\partial Y_{ij}} X_{ik}$` over the samples.

---

As matrices, that sum is `dY.T @ self.X`, which has the weight's shape. The bias is added to every sample's outputs, so its gradient adds `dY` up over the samples: `np.sum(dY, axis=0)`.

---

An input `$X_{ik}$` feeds every output `$j$` through the weight `$W_{jk}$`, so its gradient is `$\sum_j \frac{\partial L}{\partial Y_{ij}} W_{jk}$`: `dY @ self.weight`.
