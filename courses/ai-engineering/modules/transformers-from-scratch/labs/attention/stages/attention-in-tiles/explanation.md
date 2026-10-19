The running values give the same answer as the whole softmax because rescaling is exact. After any number of tiles, `$\ell = \sum_j e^{s_j - m}$` and `$o = \sum_j e^{s_j - m} v_j$` over the keys seen so far, with `$m$` their largest score. A new tile with largest score `$m'$` multiplies the old terms by `$e^{m - m'}$`, which turns each `$e^{s_j - m}$` into `$e^{s_j - m'}$`, and adds the tile's own terms on the same footing. At the end, every key's term is relative to the overall largest score, and the ratio is the softmax's weighted sum:

```math
\frac{o}{\ell} = \frac{\sum_j e^{s_j - m} v_j}{\sum_j e^{s_j - m}} = \sum_j \text{softmax}(s)_j \, v_j
```

Since every exponential is taken after subtracting a score at least as large, none can overflow.

On GPT-2's size, {% $fig.gpt2_heads %} heads and {% $fig.gpt2_length %} tokens, attention that holds every score makes a tensor of {% $fig.full_most %} numbers, and the same attention in tiles of {% $fig.tile %} keys makes at most {% $fig.tiled_most %}. For SmolLM2-135M's longest story, tiles of {% $fig.tile %} keys bring a layer's scores from {% $fig.smol_full %} to {% $fig.smol_tiled %} in float32. The work is the same, every query against every key, but the memory grows with the story's length rather than its square.

FlashAttention goes further. It tiles the queries too, so a tile of queries, keys and values fits in a GPU's on-chip memory, and it works out a whole tile there in one kernel, so the scores never travel to the GPU's main memory at all. For training, it keeps the output and each query's `$m$` and `$\ell$`, and works out the scores again in the backward pass, instead of storing them.
