A `torch.autograd.Function` is a node of autograd's graph written by hand. Its `forward` runs without recording anything inside it, and its `backward` is what autograd calls when the backward pass reaches the node. `forward` saves what `backward` needs with `ctx.save_for_backward`, which also checks that nothing saved was changed in place before the backward pass reads it.

`backward` receives `grad`, the final loss's gradient with respect to the function's output, and by the chain rule multiplies it by the function's own gradient:

```math
\frac{\partial L}{\partial z_{ij}} = \frac{\partial L}{\partial \ell} \cdot \frac{1}{n} \left( \mathrm{softmax}(z_i)_j - [j = y_i] \right)
```

When the loss is the last thing computed, `grad` is 1, and a backward pass that forgets to multiply by it gives the right answer. Once anything scales the loss, a weight on it, a mean of several losses, or the factor mixed precision multiplies it by, it gives the wrong one. `backward` returns a gradient for each input of `forward`, and `None` for the digits, which are whole numbers and have no gradient.

`gradcheck` moves each input by a small step and compares how the output changes with what `backward` says. It works in `float64`, where the differences are accurate enough to tell a wrong gradient from rounding. For a batch of {% $fig.rows %} digits, {% $fig.classes %} logits each, it checks {% $fig.entries %} partial derivatives.

A function of your own is worth writing when its backward pass is cheaper or steadier than autograd's. Here, autograd would differentiate the log-sum-exp step by step, and the softmax less a one-hot row is one subtraction.
