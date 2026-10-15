The loss is a chain of steps, and by the chain rule its derivative with respect to an early step is the product of the derivatives of every step after it. Working back from the loss `$L$`, with `$P = Z W_1 + b_1$` the hidden layer's inputs:

```math
\begin{aligned}
\frac{\partial L}{\partial s} &= \frac{\sigma(s) - y}{n} \\
\frac{\partial L}{\partial w_2} &= A^\top \frac{\partial L}{\partial s}, \qquad \frac{\partial L}{\partial b_2} = \sum_k \frac{\partial L}{\partial s_k} \\
\frac{\partial L}{\partial P} &= \left(\frac{\partial L}{\partial s} \, w_2^\top\right) \odot \left(1 - A^2\right) \\
\frac{\partial L}{\partial W_1} &= Z^\top \frac{\partial L}{\partial P}, \qquad \frac{\partial L}{\partial b_1} = \sum_k \left(\frac{\partial L}{\partial P}\right)_k
\end{aligned}
```

| Symbol | Meaning |
| --- | --- |
| `$A$` | The hidden layer's outputs, `$\tanh(P)$`, a row for each sample |
| `$\odot$` | Multiplication element by element |
| `$n$` | The number of samples, {% $fig.records %} |

Each line reuses the forward pass's `$A$` and the slope the line above it passed back. This is backpropagation: the whole gradient for a few times the cost of one forward pass, where the numerical gradient took {% $fig.evaluations %} forward passes, two for each of the {% $fig.parameters %} parameters. That is why numerical gradients check a gradient rather than train with one.

At the tests' random weights the loss is {% $fig.loss %}, and its gradient has a length of {% $fig.length %}. The chart moves the weights down your gradient. At first the loss falls with a slope equal to the gradient's length, since no direction is steeper, and the straight line your gradient predicts touches the loss there. Further out the loss curves away from that line: a gradient gives the slope only at the point where it was taken. Your gradient and central differences agree to within 1 part in `$10^{\fig{bound}}$`.
