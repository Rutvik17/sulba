`X[sample]` and `said_yes[sample]` are the sample's rows, with each row as many times as the sample drew it.

---

The order of the draws matters: for each tree, first its sample, then its seed, both from the same `rng`.

---

`np.mean` of a list of arrays with `axis=0` averages them row by row.
