`x.view(batch, length, heads, width // heads)` gives each token's vector as `heads` slices in a row, without copying. `.transpose(1, 2)` then puts the heads before the positions, `(batch, heads, length, width / heads)`, which is the shape `attention` works on: every head's every query against its every key.

---

To put the heads side by side again, `.transpose(1, 2)` first, so that each position's heads are next to each other, then `.reshape(batch, length, width)`. `view` can't do it, since the transposed tensor isn't contiguous.

---

`mha.in_proj_weight.chunk(3)` gives the query's, key's and value's weights in that order, and `mha.in_proj_bias.chunk(3)` their biases. Copy them under `torch.no_grad()`, with `layer.weight.copy_(...)`, so your layers keep weights of their own.
