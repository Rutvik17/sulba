`np.max(logits, axis=-1, keepdims=True)` gives each row's largest logit in a shape that subtracts from every logit in its row. The log of a softmax is the shifted logits minus the log of the sum of their powers.

---

A pair's probability of Yes is `np.exp(pairs["yes"] - pairs["lse"])`, and `other` is what Yes and No leave.
