A good start keeps the signal's size at the first step, and training changes the weights from there. Batch normalization keeps it at every step: it normalizes each feature over the batch, so that every layer after it sees inputs of mean 0 and variance 1, then scales and shifts them by a weight `$\gamma$` and a bias `$\beta$` it learns. For a batch `$X$`, each feature `$x$` with mean `$\mu$` and variance `$\sigma^2$` over the batch:

```math
\hat{x} = \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}}, \qquad y = \gamma \hat{x} + \beta
```

In evaluation there may be one digit, or a batch of any mix, so `torch.nn.BatchNorm1d` keeps running estimates of each feature's mean and variance through training, and normalizes with those instead. Each training batch mixes its own in at the momentum, {% $fig.momentum %} unless it's given:

```math
\hat{\mu} \leftarrow (1 - m) \hat{\mu} + m \mu, \qquad \hat{\sigma}^2 \leftarrow (1 - m) \hat{\sigma}^2 + m \frac{n}{n - 1} \sigma^2
```

The variance that normalizes a training batch is the batch's own, over `$n$`, and the one mixed into the running estimate is unbiased, over `$n - 1$`. The estimates start at 0 and 1, `$\gamma$` at 1 and `$\beta$` at 0, and `$\epsilon$` is {% $fig.eps %}. The backward pass, given `$\partial L / \partial y$` for a batch of `$n$`, is:

```math
\frac{\partial L}{\partial \hat{x}} = \gamma \frac{\partial L}{\partial y}, \qquad \frac{\partial L}{\partial x} = \frac{1}{n \sqrt{\sigma^2 + \epsilon}} \left( n \frac{\partial L}{\partial \hat{x}} - \sum \frac{\partial L}{\partial \hat{x}} - \hat{x} \sum \frac{\partial L}{\partial \hat{x}} \hat{x} \right)
```

with each sum over the batch, `$\partial L / \partial \gamma = \sum \hat{x} \, \partial L / \partial y$` and `$\partial L / \partial \beta = \sum \partial L / \partial y$`.

```
BatchNorm1d(num_features, eps=1e-5, momentum=0.1)
layer.forward(X, training=True) -> Y, and layer.backward(dY) -> dX, after a forward in training
layer.weight, layer.bias, layer.running_mean, layer.running_var, layer.dweight, layer.dbias
```

The tests compare your layer with `torch.nn.BatchNorm1d` on {% $fig.cases %} recorded cases in `references/norms.json`, through {% $fig.batches %} training batches and then a batch in evaluation.
