A module holds three kinds of state. Its parameters are what an optimizer trains: `parameters()` lists them, and a backward pass gives each a gradient. Its buffers are state no gradient moves: the scaling's mean and spread, fixed by the training digits, each norm's running mean and variance, which training updates as it goes, and each norm's count of the batches it has seen, `num_batches_tracked`. And its mode, `training`, is set by `train()` and `eval()` on the module and on every module registered inside it.

`state_dict()` holds the parameters and the buffers, each under the path of attributes that leads to it. The reader's holds {% $fig.tensors %} tensors: {% $fig.parameter_tensors %} parameters, which hold {% $fig.parameters %} numbers, and {% $fig.buffers %} buffers. A reader built from any pixels and loaded from it reads as the one it came from, since the buffers bring the scaling and the running estimates with them. A mean kept as a plain attribute would stay out of the state, and a reader loaded from it would scale by whatever pixels built it.

Batch normalization reads the mode. In training, `norm` normalizes each feature by the batch's own mean and variance, and moves its running estimates `$\hat{x}$` toward the batch's `$x_t$`, a fraction `$m = \fig{momentum}$` of the way each batch:

```math
\hat{x} \leftarrow (1 - m)\,\hat{x} + m\,x_t
```

It normalizes by the batch's variance over `$n$`, but updates its running variance with the variance over `$n - 1$`. In evaluation, it normalizes by the running estimates instead and leaves them alone, so a digit reads alone as it does among others.

A bias before batch normalization would do nothing: the norm takes away each feature's mean over the batch, and the bias with it. The norm's own bias, `$\beta$`, shifts each feature instead, so each block's linear layer has none.
