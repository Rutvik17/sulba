`P_train.mean(axis=0)` and `P_train.std(axis=0)` give one mean and one standard deviation per column. Subtract the means from both sets and divide both by the standard deviations.

---

Add a column of ones to `P`, so the bias becomes one more weight, and solve with `np.linalg.lstsq(A, y, rcond=None)`. Its first result holds the weights, then the bias.

---

In `errors`, make the features of both sets with `features`, standardize them together, fit on the training set, then score each set with `rmse`.
