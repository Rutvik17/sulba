The office's deep reader, the network you trained in NumPy in the last module, with {% $fig.hidden %} hidden layers of {% $fig.width %} units and batch normalization, is moving to PyTorch, and so is the code that trains it. Its layers come first, as modules from `torch.nn`. In `reader.py`, write:

- `Scale(train)`, a module that scales pixels as the office does, by `train`, the training digits' pixels as a `float64` tensor: less each pixel's mean over them, divided by its spread over them, the spread over `$n$` that NumPy's `std` gives, with a spread of 0 taken as 1. It keeps the mean and the spread as buffers named `mean` and `spread`.
- `Block(inputs, outputs)`, a hidden layer: `linear`, an `nn.Linear` without a bias, then `norm`, an `nn.BatchNorm1d`, then a ReLU.
- `Reader(train, hidden=8, width=32)`, the reader: `scale`, a `Scale` of `train`, then `blocks`, its `hidden` blocks of `width` units in order, then `output`, a linear layer with a logit for each digit.

Its parameters, its scaling and its running estimates are `float64`, as the office's numbers are. The names are the ones the office's checkpoints use: a reader's `state_dict()` holds `scale.mean`, `blocks.0.linear.weight`, `blocks.0.norm.running_mean` and the rest.

```
Scale(train)(pixels) -> scaled pixels
Block(inputs, outputs)(X) -> the layer's outputs
Reader(train, hidden=8, width=32)(pixels) -> logits
```
