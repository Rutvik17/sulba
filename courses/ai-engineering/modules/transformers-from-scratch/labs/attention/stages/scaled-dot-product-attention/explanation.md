The `$\sqrt{d}$` keeps the scores' spread from growing with the vectors' size. When the entries of a query and a key are independent, with mean 0 and variance 1, their dot product sums `$d$` products of variance 1, so its variance is `$d$`. GPT-2's heads are {% $fig.size %} wide, so their raw scores would spread with a standard deviation of {% $fig.root %}: on {% $fig.queries %} random queries against {% $fig.keys %} random keys, the scores' standard deviation is {% $fig.raw %} before the division and {% $fig.scaled %} after.

That spread decides how sharp the softmax is. Unscaled, a query's largest weight over the {% $fig.keys %} keys averages {% $fig.sharp %}, so most of its output comes from one key, and the softmax's gradient, which is small wherever a weight is close to 0 or 1, all but vanishes. Scaled, the largest weight averages {% $fig.soft %}, and every key gets a gradient.

A score of `$-\infty$` gives a weight of exactly 0, as `$e^{-\infty} = 0$`, and the remaining weights still add up to 1. A mask that zeroed weights after the softmax would leave each row adding up to less than 1.

`softmax` subtracts each row's largest score before it takes the exponentials, which changes no weight, since it divides the numerator and the denominator by the same `$e^{m}$`:

```math
\text{softmax}(x)_i = \frac{e^{x_i - m}}{\sum_j e^{x_j - m}}, \quad m = \max_j x_j
```

Without it, `torch.exp` overflows past a score of {% $fig.overflow64 %} in float64, and {% $fig.overflow32 %} in float32, and the weights become `inf` over `inf`, which is `nan`.

The weights hold a number for every query and key: `$L \times S$` for each head. That is the cost attention pays for letting every token read every token before it.
