The app's stories are short, but the team wants its model to read whole books one day, and attention's weights grow with the square of a story's length. A model that reads up to {% $fig.context %} tokens in {% $fig.smol_heads %} heads, as Hugging Face's SmolLM2-135M does, would hold {% $fig.smol_heads %} times {% $fig.context %} squared scores for one story in each layer: {% $fig.smol_full %} in float32.

The scores needn't all exist at once. Each query can work through the keys a tile at a time, keeping three running values: its largest score so far `$m$`, the sum `$\ell$` of its scores' exponentials less `$m$`, and the sum `$o$` of the values weighted by those exponentials. When a tile brings a larger score `$m'$`, `$\ell$` and `$o$` are rescaled by `$e^{m - m'}$`, so that they stay on the new footing. After the last tile, the output is `$o / \ell$`, exactly the softmax's weighted sum. FlashAttention computes attention this way, in tiles that fit in a GPU's fastest memory.

In `tiles.py`, write `tiled_attention(q, k, v, causal=False, tile=128)`, which gives the output of scaled dot-product attention for `q` of shape `(..., L, d)`, `k` of `(..., S, d)` and `v` of `(..., S, d_v)`. It works through the keys and values in tiles of at most `tile` keys, and no operation may make more numbers than `tile` for each query, or more than the output holds. With `causal`, each query sees the keys up to its own position, and `L` equals `S`. Don't use PyTorch's own attention.

```
tiled_attention(q, k, v, causal=False, tile=128) -> (..., L, d_v)
```

Two tests run on every attempt. Then four checks run before the code ships.
