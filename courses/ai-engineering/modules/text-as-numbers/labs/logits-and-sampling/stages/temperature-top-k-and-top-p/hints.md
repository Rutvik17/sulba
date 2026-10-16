For top-k, `np.sort(scaled)[-top_k]` is the `$k$`-th highest logit, and `scaled < kth` marks the logits to remove. Set them to `-np.inf`, and your `softmax` gives them 0.

---

For top-p, sort the probabilities from the likeliest down with `np.argsort(-probabilities)`. A token stays when the tokens ranked above it add up to less than `$p$`: the running total of the sorted probabilities, `np.cumsum`, minus each token's own probability gives that sum.
