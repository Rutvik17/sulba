The app trains its model on many stories at a time, and it writes several stories at once, so attention runs on batches. A batch is one tensor, but stories have different lengths, so each shorter story is padded with zeros up to the longest. Training pads after each story. Writing pads before it, so that every story's last token, from which the next one is predicted, sits at the batch's last position.

Padding must change nothing: each story's tokens must get the same outputs in a batch as alone. A query must never see a key that is padding, and with padding before a story, a padded query sees no key at all. There every score is `$-\infty$`, and the softmax of those is `nan`. Since 0 times `nan` is `nan`, the next layer's weighted sums carry it into every token of the story.

In `attention.py`, write:

- `pad(stories, side="right")`, which takes a list of stories, each a tensor `(length, width)`, and gives one batch `(batch, longest, width)`, each story padded with zeros after it, or before it if `side` is `"left"`, and booleans `(batch, longest)`, `True` at each story's own tokens.
- `batch_mask(present, causal=True)`, which takes those booleans and gives a mask `(batch, 1, longest, longest)` for your `attention`, `True` where a query may see a key: where the key is one of its story's own tokens, and, if `causal`, no later than the query. The 1 lets every head share it.
- `unpad(batch, present)`, which gives each story's own rows of a batch `(batch, longest, width)`, as a list in order.

Then change `attention` so that a query that sees no key gets weights of 0 and an output of 0, as `F.scaled_dot_product_attention` gives.

```
pad(stories, side="right") -> batch (batch, longest, width), present (batch, longest)
batch_mask(present, causal=True) -> (batch, 1, longest, longest) booleans
unpad(batch, present) -> list of (length, width)
```

The tests run stories through two of your `MultiHeadAttention` layers, alone and in batches padded on either side.
