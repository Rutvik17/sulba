Start each query's running values at `$m = -\infty$`, `$\ell = 0$` and `$o = 0$`, with shapes `(..., L, 1)`, `(..., L, 1)` and `(..., L, d_v)` so they broadcast against a tile's scores `(..., L, tile)`.

---

For a tile with scores `$s$`, the new largest score is `$m' = \max(m, \max s)$`. Then `$\ell \leftarrow \ell \, e^{m - m'} + \sum e^{s - m'}$` and `$o \leftarrow o \, e^{m - m'} + e^{s - m'} V_\text{tile}$`.

---

With `causal`, a key at position `$j$` is hidden from the query at `$i$` when `$j > i$`: `torch.arange(start, end) > torch.arange(L).unsqueeze(-1)` gives that for a tile's keys. A query whose keys so far are all hidden still has `$m' = -\infty$`, and `$-\infty - (-\infty)$` is `nan`. Subtract 0 instead for those queries: their exponentials are all 0 either way.
