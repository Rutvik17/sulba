Make the batch with `stories[0].new_zeros(len(stories), longest, width)`, which takes the stories' dtype, and copy each story into its row. With padding before it, a story starts at `longest - len(story)`.

---

`present[:, None, None, :]` has shape `(batch, 1, 1, longest)`: each story's tokens as keys, the same for every query. `.expand(-1, 1, longest, -1)` gives it a row for each query without copying, and `&` with `causal_mask(longest)` broadcasts the causal mask over the batch.

---

`mask.any(dim=-1, keepdim=True)` is `False` for a query that sees no key. `weights.masked_fill(~mask.any(dim=-1, keepdim=True), 0.0)` sets those rows' weights to 0, `nan` included, and the output `weights @ v` follows.

---

`rows[own]`, with `own` a row of booleans, keeps the rows where it's `True`, in order.
