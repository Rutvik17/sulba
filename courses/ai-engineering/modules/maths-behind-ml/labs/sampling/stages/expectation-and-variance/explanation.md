Write the batch's values as `$Y_1, \ldots, Y_b$`, in the order they were drawn. On its own, each draw is equally likely to be any of the `$n$` records, so each has the records' mean `$\mu$` as its expectation and their variance `$\sigma^2$` as its variance. The expectation of a sum is the sum of the expectations, whether or not the terms depend on each other, so the batch's mean has expectation `$\mu$` for any batch size.

Variances add when the terms don't depend on each other, and draws without replacement do: a record drawn first can't be drawn again. By symmetry, every pair of draws has the same covariance `$c$`. Drawing all `$n$` records gives their total, which can't vary:

```math
\operatorname{Var}(Y_1 + \cdots + Y_n) = n\sigma^2 + n(n-1)c = 0
```

so `$c = -\sigma^2/(n-1)$`. For a batch of `$b$`,

```math
\begin{aligned}
\operatorname{Var}(Y_1 + \cdots + Y_b) &= b\sigma^2 + b(b-1)c \\
&= b\sigma^2 \cdot \frac{n-b}{n-1}
\end{aligned}
```

and dividing by `$b^2$` gives the variance of the batch's mean. Drawn with replacement, the draws don't depend on each other, `$c = 0$`, and the variance is `$\sigma^2/b$`. The factor `$\frac{n-b}{n-1}$`, the finite population correction, is 1 for a batch of one row, where the two ways of drawing are the same, and 0 for a batch of every record, whose mean is the mean of all the records.

The share malignant over the clinic's {% $fig.records %} records has `$\sigma = \fig{sigma}$`. A batch of {% $fig.size %} keeps `$\fig{kept}/\fig{less} = \fig{correction}$` of the variance it would have with replacement, and its share has a standard deviation of {% $fig.without %}, against {% $fig.with %} with replacement. The chart draws both for every batch size, with dots for the spread of your `simulated_means`, which follow the line drawn without replacement.

A standard deviation falls like `$1/\sqrt{b}$`, so a batch four times as large strays about half as far. From {% $fig.size %} rows to {% $fig.larger %}, the standard deviation falls from {% $fig.with %} to {% $fig.larger_with %} drawn with replacement, and from {% $fig.without %} to {% $fig.larger_without %} without, where the correction shrinks it further.

The same holds for a gradient. The loss is a mean over the records, so a batch's gradient is a mean of its records' gradients. Its expectation is the gradient over all the records, and each of its elements strays by the formula's standard deviation, with `$\sigma^2$` that element's variance over the records. A step along a batch's gradient follows the full gradient on average, with noise that shrinks only as the square root of the batch size grows.
