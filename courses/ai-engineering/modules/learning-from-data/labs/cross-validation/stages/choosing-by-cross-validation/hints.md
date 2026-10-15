`folds(mixes, 5, seed)[:1]` is a list holding the first fold's pair.

---

`fold_errors(...)` returns one row per fold, so `.mean(axis=0)` gives each penalty's mean RMSE over the folds, and `np.argmin` the position of the lowest.

---

Keep the best `(degree, penalty, rmse)` so far as you go through the degrees, and replace it only when a degree's lowest mean RMSE is lower.
