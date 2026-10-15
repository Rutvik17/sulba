`np.unique(mixes)` lists each mix number once. After the shuffle, the mix at position `i` goes to fold `i % k`: make a dictionary from mix number to fold, then look up each test's mix.

---

With one fold number per test, `np.flatnonzero(fold == i)` gives the row numbers in fold `i`, from lowest to highest, and `np.flatnonzero(fold != i)` the rest.

---

In `fold_errors`, take the mean and standard deviation of `P[fit]` only, and scale both `P[fit]` and `P[held]` with them. `ridge` returns one `(w, b)` per penalty, and the prediction is `Z @ w + b`.
