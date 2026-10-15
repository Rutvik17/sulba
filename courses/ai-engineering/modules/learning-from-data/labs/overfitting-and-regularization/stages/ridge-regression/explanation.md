Ridge regression keeps least squares' fit to the training tests and adds a cost for large weights:

```math
J(w, b) = \frac{1}{n} \sum_{i=1}^{n} (y_i - p_i \cdot w - b)^2 + \lambda \lVert w \rVert^2
```

| Symbol | Meaning |
| --- | --- |
| `$n$` | The number of training tests |
| `$p_i$` | Test `$i$`'s features, standardized |
| `$y_i$` | Its measured strength |
| `$\lambda$` | The penalty |
| `$\lVert w \rVert^2$` | The sum of the squared weights, `w @ w` |

The derivative of `$J$` with respect to `$b$` is zero where `$b = \mu_y - \mu_p \cdot w$`: the bias makes the mean prediction the mean strength, whatever the weights. Putting that bias in leaves the weights, and setting their derivatives to zero gives

```math
\left( P_c^\top P_c + n \lambda I \right) w = P_c^\top (y - \mu_y)
```

| Symbol | Meaning |
| --- | --- |
| `$\mu_y$`, `$\mu_p$` | The mean strength, and each feature's mean, over the training tests |
| `$P_c$` | The features with each column's mean subtracted |
| `$I$` | The identity matrix, `np.eye` |

`$P_c^\top P_c$` alone has no inverse when the features outnumber what the tests can pin down, as at degree 4. With `$\lambda > 0$`, the matrix on the left always has one, so there is exactly one solution.

The penalty pulls every weight toward zero, so the model can no longer fit noise with large weights that cancel each other out. It counts every weight alike, which is why the features are standardized first: a feature on a large scale, such as the cement cubed, which reaches {% $fig.cement_cubed %}, has a tiny weight whatever its effect, and would barely be penalized.

Validation RMSE, in MPa, at each degree, with the penalty `$\lambda$` across the top:

| Degree | {% $fig.penalty_0 %} | {% $fig.penalty_1 %} | {% $fig.penalty_2 %} | {% $fig.penalty_3 %} | {% $fig.penalty_4 %} | {% $fig.penalty_5 %} | {% $fig.penalty_6 %} |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | {% $fig.val_1_0 %} | {% $fig.val_1_1 %} | {% $fig.val_1_2 %} | {% $fig.val_1_3 %} | {% $fig.val_1_4 %} | {% $fig.val_1_5 %} | {% $fig.val_1_6 %} |
| 2 | {% $fig.val_2_0 %} | {% $fig.val_2_1 %} | {% $fig.val_2_2 %} | {% $fig.val_2_3 %} | {% $fig.val_2_4 %} | {% $fig.val_2_5 %} | {% $fig.val_2_6 %} |
| 3 | {% $fig.val_3_0 %} | {% $fig.val_3_1 %} | {% $fig.val_3_2 %} | {% $fig.val_3_3 %} | {% $fig.val_3_4 %} | {% $fig.val_3_5 %} | {% $fig.val_3_6 %} |
| 4 | {% $fig.val_4_0 %} | {% $fig.val_4_1 %} | {% $fig.val_4_2 %} | {% $fig.val_4_3 %} | {% $fig.val_4_4 %} | {% $fig.val_4_5 %} | {% $fig.val_4_6 %} |

With no penalty, degree 2 is best, at {% $fig.val_2_0 %} MPa. With one, degree {% $fig.best_degree %} at λ = {% $fig.best_penalty %} does best, at {% $fig.best_val %} MPa: the extra flexibility helps once the penalty keeps it from fitting noise. Too large a penalty pulls the weights so far toward zero that every degree does worse again.

scikit-learn's `Ridge` minimizes the sum of the squared errors, not their mean, plus `alpha` times the squared weights, so its `alpha` is `$n\lambda$`: for the chosen model, `$\fig{n} \times \fig{best_penalty} = \fig{alpha}$`.
