Keep each row's squared distance to its nearest centre so far in an array: start it from the first centre, draw the next with `rng.choice(len(Z), p=nearest / nearest.sum())`, and update it with `np.minimum`.

---

`best_of` passes the same `rng` to every `plus_plus` call, so each start draws on from where the one before stopped. Compare inertias with a strict `<` to keep the first of equal ones.

---

With `members = labels[:, np.newaxis] == np.arange(labels.max() + 1)`, `cdist(Z, Z) @ members` sums each row's distances to the rows of each group. A row's own group holds one row fewer to average over: the row itself, at distance 0.
