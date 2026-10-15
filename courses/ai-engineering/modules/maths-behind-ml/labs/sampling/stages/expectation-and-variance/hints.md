`np.var(values)` divides by the number of values, as `$\sigma^2$` does. Divide it by `size`, then multiply by `(n - size) / (n - 1)`.

---

`rng.choice(n, size, replace=False)` draws `size` different row numbers. Take the mean of `values` over them, `repeats` times, and return the means as one array.
