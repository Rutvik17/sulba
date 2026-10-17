Take each sample's statistics over its features with `axis=-1, keepdims=True`, so that they broadcast back over the sample: `X.mean(axis=-1, keepdims=True)` and `X.var(axis=-1, keepdims=True)`.

---

In the backward pass the weight's and the bias's gradients still sum over the batch, `axis=0`, since each feature's weight is used by every sample. The two sums inside the formula are over each sample's features, `axis=-1, keepdims=True`, with `n` the number of features.
