Print what the model was sent with `model.requests[-1].body["input"]` after a search, and compare it with the model card's prefixes.

---

`np.linalg.norm(cut(vectors), axis=1)` gives each cut vector's length. What length does the model card's shortening end with?

---

`sorted(["p1", "p2", "p10"])` is `["p1", "p10", "p2"]`. Which row of `self.codes` holds the vector of `p10`?

---

`np.argsort([0.2, 0.9, 0.5])` is `[0, 2, 1]`: it sorts from the lowest.
