A linear regression model forecasts each hour's output as a weighted sum of that hour's measurements, plus a bias:

```math
\hat{y} = w \cdot x + b
```

| Symbol | Meaning |
| --- | --- |
| `$x$` | One hour's {% $fig.n_features %} measurements |
| `$w$` | One weight per measurement |
| `$b$` | The bias |
| `$\hat{y}$` | The forecast output, in MW |

A weight is how much the forecast changes when its measurement rises by one unit and the others stay as they are.

The mean squared error scores the forecasts for many hours at once: each miss is squared, and the squares are averaged.

```math
\mathrm{MSE} = \frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2
```

| Symbol | Meaning |
| --- | --- |
| `$n$` | The number of hours |
| `$y_i$` | Hour `$i$`'s actual output |
| `$\hat{y}_i$` | Its forecast |

Squaring counts a miss in either direction against the model, and counts one large miss far more than several small ones. The square root of the MSE, the RMSE, is in megawatts, like the output.

The simplest forecast ignores the weather and gives every hour the training hours' mean output, {% $fig.mean %} MW. Worked example, on the first three test hours:

| Hour | Output | Forecast | Miss | Miss squared |
| --- | --- | --- | --- | --- |
| 1 | {% $fig.y_1 %} | {% $fig.mean %} | {% $fig.miss_1 %} | {% $fig.square_1 %} |
| 2 | {% $fig.y_2 %} | {% $fig.mean %} | {% $fig.miss_2 %} | {% $fig.square_2 %} |
| 3 | {% $fig.y_3 %} | {% $fig.mean %} | {% $fig.miss_3 %} | {% $fig.square_3 %} |

```math
\mathrm{MSE} = \frac{\fig{square_1} + \fig{square_2} + \fig{square_3}}{3} = \fig{mse_3}
```

Over all {% $fig.n_test %} test hours, the mean misses by an RMSE of {% $fig.rmse_mean %} MW. A model of the weather has to beat that.
