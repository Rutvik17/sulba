`theta ** (-torch.arange(0, dim, 2, dtype=torch.float64) / dim)` gives every pair's angle at once.

---

`positions[..., None] * frequencies(dim, theta)` gives each row's angles, (..., length, dim // 2). Their cosines and sines turn both halves of the row.

---

With `first` and `second` the two halves of the last dimension, the turned row is `first * cos - second * sin` followed by `second * cos + first * sin`.
