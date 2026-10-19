`torch.ones(length, length, dtype=torch.bool).tril()` keeps the diagonal and everything below it.

---

`k.transpose(-2, -1)` swaps a key tensor's last two dimensions, whatever comes before them, so `q @ k.transpose(-2, -1)` gives every query's score for every key, `(..., L, S)`.

---

`scores.masked_fill(~mask, float("-inf"))` puts `$-\infty$` where the mask is `False`, broadcasting the mask as it goes. `scores.softmax(dim=-1)` then gives those keys a weight of exactly 0.

---

Leave the softmax to `softmax`, which subtracts each row's largest score before it takes the exponentials, so a large score can't overflow.
