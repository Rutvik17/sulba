Batch normalization depends on the batch: in training each digit's outputs depend on the other digits in it, and in evaluation on estimates training left behind. Layer normalization has neither. It normalizes each sample over its own features, the same in training and in evaluation, with a weight and a bias for each feature, as `torch.nn.LayerNorm` does over a sample's last axis. For a sample `$x$` of `$n$` features with mean `$\mu$` and variance `$\sigma^2$` over its features:

```math
\hat{x} = \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}}, \qquad y = \gamma \hat{x} + \beta
```

The variance is over `$n$`, as batch normalization's is in training, and there are no running estimates. The backward pass is batch normalization's with its sums taken over each sample's features instead of over the batch.

```
LayerNorm(normalized_shape, eps=1e-5)
layer.forward(X, training=True) -> Y, the same whatever training is
layer.backward(dY) -> dX, keeping layer.dweight and layer.dbias
```

The tests compare your layer with `torch.nn.LayerNorm` on {% $fig.cases %} recorded cases in `references/norms.json`, one with a sample whose features are all the same, whose variance is 0.
