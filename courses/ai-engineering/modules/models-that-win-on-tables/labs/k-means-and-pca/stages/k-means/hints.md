`Z[:, np.newaxis, :] - centres[np.newaxis, :, :]` holds every row's difference from every centre. Square it, sum over the last axis, and `argmin` over the centres gives the first of equal distances.

---

`Z[labels == group].mean(axis=0)` is one group's new centre. Build the new centres in a new array, so that the ones `k_means` was given stay as they were.

---

Keep each round's labels, and stop when `np.array_equal` says the next round's are the same.
