A logistic regression model gives each sample a score, a weighted sum of its features, then turns the score into a probability between 0 and 1 with the sigmoid, `$\sigma$`:

```math
p = \sigma(w \cdot x + b), \qquad \sigma(z) = \frac{1}{1 + e^{-z}}
```

| Symbol | Meaning |
| --- | --- |
| `$x$` | One sample's {% $fig.n_features %} measurements |
| `$w$` | One weight per measurement |
| `$b$` | The bias |
| `$z$` | The score, `$w \cdot x + b$` |
| `$p$` | The probability that the sample is malignant |

A large positive score gives a probability near 1, a large negative score gives one near 0, and a score of 0 gives exactly one half.

Worked example, for `$z = 2$`:

```math
\sigma(2) = \frac{1}{1 + e^{-2}} = \frac{1}{\fig{denominator}} = \fig{sigma_2}
```

For `$z = -1000$`, the formula needs `$e^{1000}$`, which is larger than the largest float, about `$\fig{float_max}$`. NumPy returns `inf` and warns. Multiplying the top and the bottom of the fraction by `$e^{z}$` gives the same number in another form:

```math
\frac{1}{1 + e^{-z}} = \frac{e^{z}}{e^{z} + 1}
```

For a negative `$z$`, `$e^{z}$` is between 0 and 1, so nothing overflows. Use the first form for scores of 0 or more, and the second for negative scores.
