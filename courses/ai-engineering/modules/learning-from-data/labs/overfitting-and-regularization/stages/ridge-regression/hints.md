The bias that minimizes the loss makes the mean prediction the mean strength: `b = y.mean() - P.mean(axis=0) @ w`. Put that in, and only the weights are left to find, from `P` and `y` with their means subtracted.

---

With `Pc = P - P.mean(axis=0)`, the weights solve `(Pc.T @ Pc + n * penalty * I) w = Pc.T @ (y - y.mean())`, where `n` is the number of rows and `I` is `np.eye` of the number of features. `np.linalg.solve` solves it.

---

In `choose`, make and standardize the features once per degree, then try every penalty on them, and keep the pair with the lowest validation RMSE.
