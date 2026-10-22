`statistics.median` gives a list's median, the mean of the two middle values when there's an even number of them.

---

At position `at`, the values on either side are at `math.floor(at)` and the index after it, which for a single value is past the end: keep it at the last index.

---

Each value falls below the p-quantile with the chance p, so how many of n values fall below it is binomial. The low end leaves a chance of less than a that the quantile is below it, and the high end a chance of at most a that it's above.
