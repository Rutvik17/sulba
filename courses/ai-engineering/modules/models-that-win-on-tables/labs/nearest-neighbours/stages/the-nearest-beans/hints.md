For one bean, `((train - bean) ** 2).sum(axis=1)` gives its squared distance to every training bean, which orders them as the distance does. `np.argsort(..., kind="stable")` keeps equal distances in the order of `train`.

---

`varieties[neighbours]` gives each bean's neighbours' varieties, nearest first. `np.unique(named, return_counts=True)` counts them, and the first of `named` among the varieties with the most votes is the nearest of the tied.
