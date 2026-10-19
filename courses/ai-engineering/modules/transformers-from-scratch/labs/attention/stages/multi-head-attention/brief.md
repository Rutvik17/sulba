A single attention gives each token one mix of the tokens before it. The app's model, like GPT-2, runs several attentions side by side in each layer, its heads, so that each head can weigh the tokens before it in its own way. Each head attends with its own slice of the queries, keys and values, and an output layer reads the heads' outputs side by side.

In `attention.py`, write `MultiHeadAttention`, an `nn.Module`:

- `MultiHeadAttention(width, heads)` holds four `nn.Linear` layers from `width` to `width`: `query`, `key`, `value` and `out`. It raises `ValueError` if `heads` doesn't divide `width`.
- `forward(x, mask=None)` takes stories `x` of shape `(batch, length, width)`. It makes the queries, keys and values with their layers, splits each into `heads` slices of `width / heads`, the first slice for the first head, and runs your `attention` in every head at once, with `mask` as `attention` takes it. It puts the heads' outputs side by side again, in order, and gives the `out` layer's output, with each head's weights.
- `MultiHeadAttention.from_torch(mha)` makes one with the weights and biases of `mha`, an `nn.MultiheadAttention` made with `batch_first=True`. `mha.in_proj_weight` holds the query, key and value layers' weights one above the other, and `mha.in_proj_bias` their biases. Its output layer is `mha.out_proj`.

```
MultiHeadAttention(width, heads)
forward(x, mask=None) -> output (batch, length, width), weights (batch, heads, length, length)
MultiHeadAttention.from_torch(mha) -> MultiHeadAttention
```

The tests compare yours with `nn.MultiheadAttention` in float64. Its own mask means the opposite of yours: `True` where a query may not see a key.
