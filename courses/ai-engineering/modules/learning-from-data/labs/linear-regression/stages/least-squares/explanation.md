Add a column of ones to the training measurements and the bias becomes one more weight. The forecasts are then `$A\theta$`, and the mean squared error is lowest where its gradient is zero, which gives a system of linear equations, the normal equations:

```math
A^\top A \, \theta = A^\top y
```

| Symbol | Meaning |
| --- | --- |
| `$A$` | The training measurements, one row per hour, with a column of ones |
| `$\theta$` | The weights, then the bias |
| `$y$` | The training outputs |

On paper, `$\theta = (A^\top A)^{-1} A^\top y$` solves them. In floating point, that formula loses precision. A matrix's condition number measures how much it can magnify small rounding errors in a solution, and forming `$A^\top A$` squares it: on the training hours, `$A$`'s condition number is about {% $fig.cond_a %}, and `$A^\top A$`'s about {% $fig.cond_ata %}. `np.linalg.lstsq` works from `$A$` itself, with a singular value decomposition, so it keeps the digits the inverse would lose. When one column repeats another, `$A^\top A$` has no inverse at all, and many `$\theta$` give the same least error. `lstsq` still returns one: the shortest.

Your model's weights:

| Measurement | Weight | Per |
| --- | --- | --- |
| Temperature | {% $fig.w_temperature %} MW | °C |
| Exhaust vacuum | {% $fig.w_vacuum %} MW | cm Hg |
| Air pressure | {% $fig.w_pressure %} MW | millibar |
| Relative humidity | {% $fig.w_humidity %} MW | percentage point |

A weight reads with the other measurements held where they are: one degree warmer, and the forecast falls by {% $fig.w_temperature_size %} MW. The bias, {% $fig.bias %} MW, is the forecast for an hour with every measurement at zero, which no hour comes near, so it doesn't mean much on its own.

On the test hours, the model's RMSE is {% $fig.rmse %} MW, against {% $fig.rmse_mean %} MW for forecasting the mean.
