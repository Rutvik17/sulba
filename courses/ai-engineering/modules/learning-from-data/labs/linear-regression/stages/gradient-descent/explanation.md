The mean squared error's derivatives come from the chain rule. Each squared miss `$(\hat{y}_i - y_i)^2$` changes by `$2(\hat{y}_i - y_i)$` times the change in `$\hat{y}_i$`, and `$\hat{y}_i$` changes by `$x_i$` with the weights and by 1 with the bias:

```math
\frac{\partial\,\mathrm{MSE}}{\partial w} = \frac{2}{n} X^\top (\hat{y} - y), \qquad \frac{\partial\,\mathrm{MSE}}{\partial b} = \frac{2}{n} \sum_{i=1}^{n} (\hat{y}_i - y_i)
```

Gradient descent repeats one step: move every weight and the bias a little against its derivative.

```math
w \leftarrow w - \eta \, \frac{\partial\,\mathrm{MSE}}{\partial w}, \qquad b \leftarrow b - \eta \, \frac{\partial\,\mathrm{MSE}}{\partial b}
```

| Symbol | Meaning |
| --- | --- |
| `$\eta$` | The learning rate, `lr` |
| `$\leftarrow$` | Replace the value on the left with the one on the right |

The bias starts at the mean output, the best forecast with no weather at all, so training starts from the forecast stage 1 scored.

Unscaled, the measurements are hard to descend. The air pressure averages {% $fig.pressure_mean %} millibar but varies by only {% $fig.pressure_std %}, so the bias and the weight on pressure pull against each other, and the condition number of the training hours with their column of ones is about {% $fig.cond_raw %}. Standardized, every column has mean 0 and standard deviation 1, and the condition number falls to {% $fig.cond_scaled %}.

The mean squared error curves most steeply along one direction, by an amount `$\lambda_{\max}$`, its largest curvature. Along that direction, each step multiplies the distance left to the minimum by `$1 - \eta \lambda_{\max}$`. The distance shrinks only while that number is between −1 and 1, so a learning rate must stay below `$2/\lambda_{\max}$`. On the standardized training hours:

```math
\frac{2}{\lambda_{\max}} = \frac{2}{\fig{lambda_max}} = \fig{lr_max}
```

| Learning rate | Steps to match least squares within 0.01 MW | Loss falls at every step |
| --- | --- | --- |
| 0.01 | {% $fig.steps_0_01 %} | {% $fig.falls_0_01 %} |
| 0.03 | {% $fig.steps_0_03 %} | {% $fig.falls_0_03 %} |
| 0.1 | {% $fig.steps_0_1 %} | {% $fig.falls_0_1 %} |
| 0.2 | {% $fig.steps_0_2 %} | {% $fig.falls_0_2 %} |
| 0.3 | {% $fig.steps_0_3 %} | {% $fig.falls_0_3 %} |
| 0.4 | {% $fig.steps_0_4 %} | {% $fig.falls_0_4 %} |
| 0.42 | {% $fig.steps_0_42 %} | {% $fig.falls_0_42 %} |

Up to a point, a larger step means fewer of them. At 0.4, close to the limit, a step overshoots along the steepest direction and lands on the other side, so it takes longer than 0.3. Past the limit, the loss grows without end.
