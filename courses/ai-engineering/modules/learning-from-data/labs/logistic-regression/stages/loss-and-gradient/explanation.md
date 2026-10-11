The loss measures how far the probabilities are from the labels. For one sample with label `$y$` and probability `$p$`, the cross-entropy is

```math
\ell(y, p) = -\bigl[\, y \ln p + (1 - y) \ln(1 - p) \,\bigr]
```

For a label of 1, only the first term is left, `$-\ln p$`. For a label of 0, only the second, `$-\ln(1 - p)$`. Each is 0 for a sure, right answer and grows without limit as a wrong answer becomes sure.

`log_loss` is the mean over the samples. `gradient` is the gradient of that mean with the l2 term added:

```math
J(w, b) = \frac{1}{n} \sum_{i=1}^{n} \ell(y_i, p_i) + \frac{\lambda}{2} \lVert w \rVert^2
```

| Symbol | Meaning |
| --- | --- |
| `$n$` | The number of samples |
| `$y_i$` | Sample `$i$`'s label, 0 or 1 |
| `$p_i$` | Its probability, from `predict_proba` |
| `$\lambda$` | The l2 strength, `l2` |
| `$\lVert w \rVert^2$` | The sum of the squared weights, `w @ w` |

Worked example, the loss of two samples with labels 1 and 0, each given a probability of 0.5:

```math
\begin{aligned}
L &= \frac{1}{2} \bigl[ \ell(1, 0.5) + \ell(0, 0.5) \bigr] \\
&= -\frac{1}{2} \bigl[ \ln 0.5 + \ln(1 - 0.5) \bigr] \\
&= \ln 2 = \fig{ln_2}
\end{aligned}
```

A sure, wrong answer, `$p = 0$` for a label of 1, would cost `$-\ln 0$`, which is infinite. Clipped to `$10^{-15}$`, it costs `$-\ln 10^{-15} = \fig{clipped_cost}$`.

For one sample, the chain rule runs from the loss through the probability to the score, `$z = w \cdot x + b$`:

```math
\frac{\partial \ell}{\partial p} = \frac{p - y}{p(1 - p)}, \qquad \frac{\partial p}{\partial z} = p(1 - p)
```

The sigmoid's slope, `$p(1 - p)$`, cancels the denominator, so `$\partial \ell / \partial z = p - y$`, the error. The score's derivative is `$x$` with respect to the weights and 1 with respect to the bias. Averaged over the samples, and with the l2 term's derivative `$\lambda w$` added:

```math
\begin{aligned}
\frac{\partial J}{\partial w} &= \frac{1}{n} X^{\mathsf{T}} (p - y) + \lambda w \\
\frac{\partial J}{\partial b} &= \frac{1}{n} \sum_{i=1}^{n} (p_i - y_i)
\end{aligned}
```

| Symbol | Meaning |
| --- | --- |
| `$X$` | The samples, one row each |
| `$X^{\mathsf{T}}$` | `$X$` transposed, `X.T`, one row per feature |
| `$p - y$` | The errors, one per sample |

Worked example, with two samples, two features and `$\lambda = 0$`:

```math
X = \fig{X}, \quad y = \fig{y}, \quad w = \fig{w}, \quad b = \fig{b}
```

Every score is 0, so every probability is `$\sigma(0) = \fig{sigma_0}$`:

```math
p - y = \fig{p} - \fig{y} = \fig{error}
```

```math
\begin{aligned}
\frac{\partial J}{\partial w} &= \frac{1}{\fig{n}} \fig{X_T} \fig{error} \\
&= \frac{1}{\fig{n}} \fig{products} \\
&= \fig{dw} \\
\frac{\partial J}{\partial b} &= \frac{1}{\fig{n}} (\fig{error_sum}) = \fig{db}
\end{aligned}
```

To check a gradient, compare it with central differences: move one weight by a small `$h$` each way and divide the change in `$J$` by `$2h$`.

```math
\frac{\partial J}{\partial w_j} \approx \frac{J(w + h e_j, b) - J(w - h e_j, b)}{2h}
```

Here `$e_j$` is 1 in place `$j$` and 0 everywhere else.
