Each output of a linear layer is a weighted sum of one sample's inputs, plus a bias:

```math
Y_{ij} = \sum_k X_{ik} W_{jk} + b_j
```

A weight `$W_{jk}$` is used once for every sample, so by the chain rule its gradient adds up, over the batch, the gradient at each output it feeds times the input it multiplied. The bias is added to every sample, so it collects the gradient of its output from each of them. And an input feeds every output, so its gradient adds the outputs' gradients, each through its weight:

```math
\begin{aligned}
\frac{\partial L}{\partial W} &= \left(\frac{\partial L}{\partial Y}\right)^{\top} X \\
\frac{\partial L}{\partial b} &= \sum_i \left(\frac{\partial L}{\partial Y}\right)_i \\
\frac{\partial L}{\partial X} &= \frac{\partial L}{\partial Y} \, W
\end{aligned}
```

| Matrix | What it holds | Its shape |
| --- | --- | --- |
| `$X$` | The batch, a row for each sample | samples × inputs |
| `$W$` | The weight, a row for each output | outputs × inputs |
| `$\partial L / \partial Y$` | The loss's gradient at the outputs | samples × outputs |

The shapes check the formulas. A gradient has the shape of what it's the gradient of, and the only way to make outputs × inputs from the two matrices the backward pass holds, the gradient at the outputs and the batch, is `$(\partial L / \partial Y)^{\top} X$`. A weight held the other way, inputs × outputs, swaps the transposes. PyTorch holds a row for each output, so each row of `weight` is one unit's weights over the inputs.

The backward pass costs two matrix products, each the size of the forward pass's one. For a first layer of {% $fig.hidden %} units over the {% $fig.pixels %} pixels, a batch of {% $fig.batch %} digits takes {% $fig.multiplications %} multiplications forward and twice that backward. Training costs about three forward passes a batch, whatever the size of the network.
