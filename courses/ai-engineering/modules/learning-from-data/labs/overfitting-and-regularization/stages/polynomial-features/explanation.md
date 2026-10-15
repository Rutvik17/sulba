Polynomial features make a model with one weight per measurement into a polynomial in the measurements. For two measurements to degree 2:

```math
\hat{y} = w_1 x_1 + w_2 x_2 + w_3 x_1^2 + w_4 x_1 x_2 + w_5 x_2^2 + b
```

| Symbol | Meaning |
| --- | --- |
| `$x_1, x_2$` | Two of a test's measurements |
| `$w_1, \dots, w_5$` | One weight per feature |
| `$b$` | The bias |
| `$\hat{y}$` | The predicted strength, in MPa |

The model is still linear in its weights, so it is fit as before, by least squares on a table that has more columns. What changes is the shape it can take. With `$w_3 x_1^2$`, the effect of `$x_1$` can grow or shrink as `$x_1$` grows, and with `$w_4 x_1 x_2$`, the effect of one measurement can depend on the other.

Worked example, the first test's water and age, `$x_1 = \fig{water}$` and `$x_2 = \fig{age}$`:

```math
\begin{bmatrix} x_1 & x_2 & x_1^2 & x_1 x_2 & x_2^2 \end{bmatrix} = \fig{example}
```

The number of features grows fast. From `$n$` measurements, the products of up to `$d$` of them number

```math
\binom{n + d}{d} - 1
```

| Symbol | Meaning |
| --- | --- |
| `$n$` | The number of measurements |
| `$d$` | The degree |
| `$\binom{n + d}{d}$` | The number of ways to choose `$d$` things from `$n + d$` |

The 1 taken away is the product of none of them, a column of ones, which the bias already covers.

| Degree | Features of the eight measurements |
| --- | --- |
| 1 | {% $fig.count_1 %} |
| 2 | {% $fig.count_2 %} |
| 3 | {% $fig.count_3 %} |
| 4 | {% $fig.count_4 %} |
