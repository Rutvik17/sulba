Gradient descent starts from zero weights and repeats one step: move every weight and the bias a little against its derivative.

```math
w \leftarrow w - \eta \, \frac{\partial J}{\partial w}, \qquad b \leftarrow b - \eta \, \frac{\partial J}{\partial b}
```

| Symbol | Meaning |
| --- | --- |
| `$\eta$` | The learning rate, `lr` |
| `$\leftarrow$` | Replace the value on the left with the one on the right |

The learning rate sets the size of each step. Too small, and training needs many steps. Too large, and a step jumps past the minimum, so the loss goes up instead of down. On this lab's data, standardized, with `$\lambda = 1/\fig{n_train}$`:

| Learning rate | Steps to match scikit-learn within 0.0001 | Loss falls at every step |
| --- | --- | --- |
| 0.5 | {% $fig.steps_0_5 %} | {% $fig.falls_0_5 %} |
| 1 | {% $fig.steps_1 %} | {% $fig.falls_1 %} |
| 2 | {% $fig.steps_2 %} | {% $fig.falls_2 %} |
| 4 | {% $fig.steps_4 %} | {% $fig.falls_4 %} |
| 8 | {% $fig.steps_8 %} | {% $fig.falls_8 %} |
| 16 | {% $fig.steps_16 %} | {% $fig.falls_16 %} |
| 32 | {% $fig.steps_32 %} | {% $fig.falls_32 %} |

The features have very different scales. In the training set, mean area averages {% $fig.area_mean %} and mean smoothness {% $fig.smoothness_mean %}. A learning rate small enough for the weight on area is far too small for the weight on smoothness, so the columns are standardized first: each one has its mean subtracted and is divided by its standard deviation.

```math
x' = \frac{x - \mu}{\sigma}
```

| Symbol | Meaning |
| --- | --- |
| `$x$` | A value in one column |
| `$\mu$` | The column's mean over the training set |
| `$\sigma$` | The column's standard deviation over the training set |
| `$x'$` | The value standardized |

Worked example, the mean area of the first training sample:

```math
x' = \frac{\fig{area_x} - \fig{area_mu}}{\fig{area_sigma}} = \fig{area_scaled}
```

The test set is scaled with the training set's `$\mu$` and `$\sigma$`. A model meets new samples after it is trained, often one at a time, so their own mean and standard deviation aren't known.

scikit-learn's `LogisticRegression()` minimizes the mean loss plus a penalty set by `C`, which is 1 by default. Neither it nor `J` penalizes the bias.

```math
\frac{1}{n} \sum_{i=1}^{n} \ell(y_i, p_i) + \frac{1}{2Cn} \lVert w \rVert^2
```

That is `$J$` with `$\lambda = 1/(Cn) = 1/\fig{n_train}$`, so both have the same minimum. scikit-learn stops once its improvements get small, and by default that is before the minimum: on this test set, its probabilities are up to {% $fig.default_gap %} from the ones it gives with `tol=1e-12`. That model labels {% $fig.correct %} of the {% $fig.n_test %} test samples correctly.
