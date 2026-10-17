The derivative of `$\log \sum_j e^{z_j}$` with respect to `$z_k$` is `$e^{z_k} / \sum_j e^{z_j}$`, the softmax probability `$p_k$`. So a digit's cross-entropy has the gradient

```math
\frac{\partial \ell_i}{\partial z_{ik}} = p_{ik} - [k = y_i]
```

its probabilities, less 1 at its label. Each row adds up to 0, since the probabilities add up to 1: raising every logit by the same amount can't change the loss. The loss is the mean over the batch, so each row is divided by the number of digits, `$n$`. The gradient then doesn't grow with the batch, and a learning rate means the same at any batch size.

When every logit is the same, every digit has probability `$1/\fig{classes}$` and the loss is `$\log \fig{classes} = \fig{log_ten}$`. With small starting weights the logits are nearly equal, so a network's first loss is close to that, and a first loss far above it is a sign its weights started too large.

Taking the largest logit out leaves every term of the sum at 1 or below, and one of them at exactly 1, so the sum is between 1 and the number of digits, and its log can't overflow or reach `$-\infty$`. In the tests' confident case, with logits as large as {% $fig.largest %}, the loss is {% $fig.confident_loss %}, as PyTorch gives it. Without the shift, `np.exp` of those logits overflows to infinity, and the softmax's probabilities come out as `nan`.

ReLU's derivative is 1 above 0 and 0 below, and at 0 itself there is none. PyTorch takes it as 0 there, and so do the tests.
