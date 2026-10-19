Pad with any token, such as `END`: `[END] * (longest - len(prompt)) + prompt`. Keep each row's padding in a tensor, `pads`, which the mask and the positions need.

---

With `start = len(cache)`, the step's places are `torch.arange(start, start + length)`. A row's positions are its places less its padding, and `rotate` takes them shaped (batch, 1, length), one row for every head.

---

A key at place `k` may be read by the query at place `p` of a row when `k >= pads[row]` and `k <= p`. Build that as a tensor (batch, length, keys) and give it to attention as `attn_mask[:, None]`.
