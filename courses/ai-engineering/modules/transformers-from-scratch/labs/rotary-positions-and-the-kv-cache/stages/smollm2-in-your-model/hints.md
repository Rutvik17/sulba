`F.rms_norm(x, (width,), weight, eps)` is PyTorch's own, but write `rms_norm` from its formula: `x.pow(2).mean(dim=-1, keepdim=True)` is the mean square.

---

After the projections, `view` the keys and values as (batch, length, kv_heads, 64) and move the heads before the length. Then `k.repeat_interleave(heads // kv_heads, dim=1)` gives each query head its key head, in order. `repeat` would give the wrong ones.

---

Make `embed_tokens`, `layers` and `norm` as `nn.Embedding`, `nn.ModuleList` and `RMSNorm`, and the names match the file's once its `model.` prefix is taken off. Then `load_state_dict` copies every weight and refuses any name that differs.
