The help desk's best search, `reranked`, has four parts it could do without: the reranker, BM25, the vectors, and showing each text once. Taking one away at a time shows what each adds, if the difference it makes is more than chance. Two searches measured on the same questions are compared question by question: a question both answer, or both miss, says nothing about which is better.

In `compare.py`, write, for two searches' values of one measure, one value a question, in the same order:

- `randomization_test(a, b, repeats, rng)`: the two-sided p-value of the difference between `a`'s mean and `b`'s. If the two searches were the same, each question's two values could as well have come the other way round. Draw `rng.integers(0, 2, size=(repeats, len(a)))`, swap each question's two values where the draw is 1, and count the resamples whose difference is at least as far from 0 as the observed one. The p-value is that count plus 1 over `repeats` plus 1: the observed difference counts as one of the resamples.
- `bootstrap_interval(a, b, confidence, repeats, rng)`: the percentile interval of the difference. Draw `rng.integers(0, len(a), size=(repeats, len(a)))`, each row a resample of the questions, the same rows for both searches, and take the quantiles of the resamples' differences that leave `(1 - confidence) / 2` of them on each side, as `np.quantile` gives them.

The tests compare your intervals with SciPy's `bootstrap`, which draws the same resamples, and your p-values with SciPy's exact `permutation_test`, which tries every way of swapping.

```
randomization_test(a, b, repeats, rng) -> float
bootstrap_interval(a, b, confidence, repeats, rng) -> (low, high)
```
