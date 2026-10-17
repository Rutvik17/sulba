Put the layers together. `Network` holds a list of layers. Its forward pass runs a batch through them in order. Its backward pass takes the loss's gradient with respect to the logits and runs it back through the layers in reverse, each layer's backward pass handing its result to the layer before, and returns the gradient with respect to the inputs. `step(lr)` then moves every linear layer's weight and bias down its gradient, with `$\eta$` the learning rate, `lr`:

```math
W \leftarrow W - \eta \, \frac{\partial L}{\partial W}, \qquad b \leftarrow b - \eta \, \frac{\partial L}{\partial b}
```

`linear_layer(inputs, outputs, rng)` starts a linear layer as PyTorch's `nn.Linear` starts one: every weight and bias drawn uniformly from `$-1/\sqrt{\text{inputs}}$` to `$1/\sqrt{\text{inputs}}$` with `rng.uniform`, the weight first.

```
Network(layers)
network.forward(X) -> logits
network.backward(dlogits) -> dX
network.step(lr)
linear_layer(inputs, outputs, rng) -> Linear
```

The tests compare the logits, the loss and every gradient with PyTorch's for two networks saved in `references/networks.json`, one with a hidden layer and one with two. The chart trains the office's network with your layers.
