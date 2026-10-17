The network needs two more pieces. Between its linear layers goes a ReLU, which keeps each value above 0 and sets the rest to 0: without it, two linear layers in a row would be one linear layer. The last linear layer gives the logits, {% $fig.classes %} numbers for each digit, one for each digit it could be, and the loss compares them with the digit its writer meant.

Write `ReLU`, a layer with no weights. Its forward pass gives `$\max(x, 0)$` for each value. Its backward pass passes each value of the gradient back where the input was above 0, and 0 where it wasn't. At exactly 0, where `$\max(x, 0)$` has no derivative, PyTorch passes 0 back, and so should yours.

Write `cross_entropy(logits, labels)`. It gives the loss, the mean over the batch of each digit's cross-entropy, and the loss's gradient with respect to the logits. A digit's cross-entropy is minus the log of the probability the softmax gives its label:

```math
\ell_i = -\log \frac{e^{z_{i y_i}}}{\sum_j e^{z_{ij}}} = \log \sum_j e^{z_{ij}} - z_{i y_i}
```

`np.exp` overflows once a logit passes {% $fig.overflow %}, so take each row's largest logit `$m$` out first: `$\log \sum_j e^{z_j} = m + \log \sum_j e^{z_j - m}$`, where no term is above 1.

```
ReLU()
relu.forward(X) -> Y
relu.backward(dY) -> dX
cross_entropy(logits, labels) -> (loss, dlogits)
```

The tests compare them with PyTorch's `torch.relu` and `torch.nn.functional.cross_entropy` on cases saved in `references/activations.json`, among them logits in the thousands.
