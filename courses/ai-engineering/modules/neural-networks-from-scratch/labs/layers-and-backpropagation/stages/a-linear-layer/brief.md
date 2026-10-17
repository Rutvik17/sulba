A records office scans the forms people fill in by hand and wants a network to read each handwritten digit, so its clerks check only the digits the network isn't sure of. Each digit is a grid of {% $fig.side %} by {% $fig.side %} counts from {% $fig.lowest %} to {% $fig.highest %}, {% $fig.pixels %} numbers in all. `data/digits.csv` holds {% $fig.digits %} of them, each with the digit its writer meant: {% $fig.training %} to train on, {% $fig.validation %} to choose settings with, and {% $fig.test %} from other people, to test with.

The network is built from layers. A layer's forward pass turns its inputs into outputs. Its backward pass takes the loss's gradient with respect to its outputs and gives the gradient with respect to its inputs, and with respect to its weights if it has any.

Write `Linear`, a layer with a weight and a bias, held as PyTorch's `nn.Linear` holds them: the weight has a row for each output and a column for each input, and the bias a value for each output. Its forward pass takes a batch, a row for each sample, and gives

```math
Y = X W^\top + b
```

Its backward pass takes `dY`, the loss's gradient with respect to `Y`. It keeps the gradients with respect to the weight and the bias in `dweight` and `dbias`, and returns the gradient with respect to `X`, for the layer before it.

```
Linear(weight, bias)
layer.forward(X) -> Y
layer.backward(dY) -> dX, setting layer.dweight and layer.dbias
```

The tests compare your layer with PyTorch's `torch.nn.functional.linear` on {% $fig.cases %} cases saved with their inputs in `references/linear.json`, from one sample with {% $fig.first_inputs %} inputs to a batch of {% $fig.last_samples %} digits.
