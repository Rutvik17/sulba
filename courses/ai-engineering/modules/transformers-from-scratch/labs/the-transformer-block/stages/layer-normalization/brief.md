The app's model, like GPT-2, is a stack of blocks. Each block has two parts, attention and then a small network for each token on its own, the MLP, and each part reads the token vectors through a layer normalization of its own. A layer normalization rescales each token's vector to a mean of 0 and a variance of 1 across its numbers, then gives every number a learnt scale and shift. However large or small the vectors grew in the blocks before, each part reads them at a steady size.

For a vector `$x$` of `$n$` numbers, with a weight `$w$` and a bias `$b$` of `$n$` numbers each:

```math
\begin{aligned}
\mu &= \frac{1}{n} \sum_j x_j, \qquad \sigma^2 = \frac{1}{n} \sum_j (x_j - \mu)^2 \\
\text{LN}(x)_i &= \frac{x_i - \mu}{\sqrt{\sigma^2 + \epsilon}} \, w_i + b_i
\end{aligned}
```

In `block.py`, write layer normalization without `F.layer_norm` or `nn.LayerNorm`:

- `layer_norm(x, weight, bias, eps=1e-5)`, which normalizes `x` of any shape along its last dimension, as above.
- `LayerNorm(width, eps=1e-5)`, an `nn.Module` with two parameters of `width` numbers each, named as `nn.LayerNorm` names them: `weight`, starting at 1, and `bias`, starting at 0. Its `forward(x)` gives `layer_norm` of `x`.

```
layer_norm(x, weight, bias, eps=1e-5) -> the shape of x
LayerNorm(width, eps=1e-5)
```

The tests compare yours with `F.layer_norm`, its outputs and its gradients, in float64.
