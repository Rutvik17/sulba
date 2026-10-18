The NumPy reader's network has a hidden layer of {% $fig.hidden %} units with ReLU, and an output layer with a logit for each of the {% $fig.classes %} digits. Its backward passes were yours, layer by layer. In PyTorch, autograd works them out: a tensor made with `requires_grad=True` records each operation done with it, and `backward()` on a result runs those operations' backward passes in reverse, as your engine did in the last module.

In `network.py`, write:

- `parameters(start)`, the network's weights and biases from `start`, a dict of NumPy arrays named `w1`, `b1`, `w2` and `b2`, each weight with a row for each output, as tensors that autograd follows. Copy them, so that training can't change the arrays.
- `logits(params, X)`, the logits for a batch `X`: the hidden layer's ReLU, then the output layer.
- `gradients(params, X, digits)`, the mean cross-entropy's gradient with respect to each parameter, as a dict by name, leaving each parameter's `.grad` as it was.
- `step(params, X, digits, lr)`, one step of gradient descent on the batch, made in place, which returns the loss before the step as a float.

```
parameters(start) -> params
logits(params, X) -> logits
gradients(params, X, digits) -> {name: gradient}
step(params, X, digits, lr) -> loss
```

The tests start the network as the NumPy reader starts it, and compare every logit, gradient and step with the NumPy reader's.
