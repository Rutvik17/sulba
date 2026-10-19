A reading app writes short stories for young children on the family's own phone or tablet, with a small language model of its own, so no story it writes leaves the device. Like GPT-2, the model reads a story as tokens, each a vector, and in each layer it works out every token's next vector from the vectors of the tokens up to it. It does that by attention, which this lab builds.

Each token makes a query `$q$`, a key `$k$` and a value `$v$`, all vectors. A query's score for a key is their dot product, divided by `$\sqrt{d}$`, where `$d$` is the size of a query or a key. A softmax over the keys turns a query's scores into weights that add up to 1, and its output is the weighted sum of the values. For all the queries at once:

```math
\text{attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^\top}{\sqrt{d}}\right) V
```

A language model predicts each token from the ones before it, so a token mustn't see the tokens after it. A causal mask hides from each query every key after its own position: its score becomes `$-\infty$`, so its weight is 0.

In `attention.py`, write attention without `F.scaled_dot_product_attention` or `nn.MultiheadAttention`:

- `causal_mask(length)`, a `(length, length)` tensor of booleans, `True` where the query in row `$i$` may see the key in column `$j$`: where `$j \le i$`.
- `attention(q, k, v, mask=None)`, which gives the output and the weights. `q` has shape `(..., L, d)`, `k` has `(..., S, d)` and `v` has `(..., S, d_v)`, with the same leading dimensions, such as a batch and heads, or none. `mask`, if given, is booleans that broadcast to `(..., L, S)`, `True` where a query may see a key, as `F.scaled_dot_product_attention` takes a mask of booleans. Each query sees at least one key.

```
causal_mask(length) -> (length, length) booleans
attention(q, k, v, mask=None) -> output (..., L, d_v), weights (..., L, S)
```

The tests compare yours with `F.scaled_dot_product_attention`, its outputs and its gradients, in float64.
