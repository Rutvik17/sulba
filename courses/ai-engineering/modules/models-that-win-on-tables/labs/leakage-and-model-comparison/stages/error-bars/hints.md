`np.var(differences, ddof=1)` is `$s^2$`, with `$n - 1$` in its divisor.

---

`t.ppf((1 + confidence) / 2, len(differences) - 1)` is the quantile for the interval's high end. The low end lies as far below the mean.
