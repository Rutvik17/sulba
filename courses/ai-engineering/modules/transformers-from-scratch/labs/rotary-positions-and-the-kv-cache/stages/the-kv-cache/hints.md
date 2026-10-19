Run each block's parts yourself: `input_layernorm`, then `q_proj`, `k_proj` and `v_proj`, the rotation, the cache, attention, `o_proj`, `post_attention_layernorm` and `mlp`. `layer.self_attn.heads` and `kv_heads` give the shapes.

---

With `start = len(cache)`, the new tokens' positions are `torch.arange(start, start + length)`. New token `i` may read keys up to `start + i`: `torch.ones(length, start + length, dtype=torch.bool).tril(start)` is that mask, for `attn_mask`.

---

`torch.cat` the cache's keys and the new ones along the length, store the result back in the cache, then repeat the heads for the query heads as in stage 2.
