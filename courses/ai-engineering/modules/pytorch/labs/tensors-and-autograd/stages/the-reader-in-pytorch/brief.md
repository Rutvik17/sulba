Ship the office's reader in PyTorch. `train(pixels, digits, rng)` trains the NumPy reader's network on the training digits, step for step as the NumPy reader trained it, with your `digits.py` and `network.py`. It returns `read`, a function that gives the digit it reads for each row of a batch of pixels.

The NumPy reader drew all that was random from `rng`, in this order. First the hidden layer's weight, then its bias, then the output layer's weight and bias, each value uniform between `$-1/\sqrt{m}$` and `$1/\sqrt{m}$` for a layer of `$m$` inputs, a weight's rows for its outputs. Then, for each of its {% $fig.epochs %} epochs, an order of the training digits from `rng.permutation`. It scaled the pixels by the training digits' means and spreads and, in each epoch's order, took a step of {% $fig.lr %} on each batch of {% $fig.batch %} digits, the last batch holding what was left. Its hidden layer has {% $fig.hidden %} units.

```
train(pixels, digits, rng) -> read
read(pixels) -> a tensor of digits
```

`pixels` and `digits` come as your `load` gives them. There are no hints. The tests are hidden: you see which pass, but not their inputs. Four more checks decide whether it ships.
