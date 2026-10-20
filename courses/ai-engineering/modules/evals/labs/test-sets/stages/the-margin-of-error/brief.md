The share of the test replies that pass every check is a mean of 1s and 0s over {% $fig.test %} questions. Other questions, asked about the same pages by other people, would give another share. A margin of error says how far the test set's share could be from the share over every question the help desk will be asked, at a stated confidence.

In `margin.py`, write:

- `standard_error(scores)`: the standard error of the mean of `n` scores drawn independently, from their variance with `n - 1` below, `m` being their mean.
- `clustered_standard_error(scores, clusters)`: the standard error of their mean when the scores come in clusters, here each page's questions, and only the clusters are drawn independently. Sum each cluster's differences from the mean, and count `G`, the clusters.
- `margin(standard_error, confidence)`: how far the interval at `confidence` reaches each side of the mean, by the normal distribution: the standard error times the `z` that leaves `(1 - confidence) / 2` of it above.

```math
\begin{aligned}
\mathrm{SE} &= \sqrt{\frac{1}{n(n-1)} \sum_{i} (s_i - m)^2} \\
\mathrm{SE}_{\text{clustered}} &= \frac{1}{n} \sqrt{\frac{G}{G-1} \sum_{g} \Bigl( \sum_{i \in g} (s_i - m) \Bigr)^2}
\end{aligned}
```

`scores` is a NumPy array, and `clusters` gives each score's cluster, in the same order. The tests compare your standard errors and intervals with statsmodels'.

```
standard_error(scores) -> float
clustered_standard_error(scores, clusters) -> float
margin(standard_error, confidence) -> float
```
