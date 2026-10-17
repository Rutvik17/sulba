A training run can go wrong for hours before its curves show why. Two checks before the first step find a broken network in seconds.

The first is the loss at the start. A network that hasn't learned anything gives every class about the same probability, `$1/K$` for `$K$` classes, so its mean cross-entropy starts near `$-\ln(1/K) = \ln K$`: {% $fig.guess %} for ten digits. A start far above that means the network is sure of answers it hasn't learned.

The second is one batch learned by heart. A network with working gradients and steps, and far more parameters than a small batch has digits, can drive the loss on that batch towards 0. One that can't has a bug.

`network.py` holds the office's network: `network(rng)` draws its parameters, a weight and a bias for each linear layer, as a list of arrays, and `loss_and_grads` gives a batch's mean cross-entropy and its gradient with respect to each. Write the checks:

```
start_loss(params, X, digits) -> (the loss before any step, ln K for the network's K classes)
learn_by_heart(params, X, digits, steps=300, lr=0.5, loss_and_grads=loss_and_grads) -> the loss before each step
first_below(losses, below=0.01) -> the first step whose loss is below below, counting from 1, or None
```

`learn_by_heart` takes its steps of SGD with a copy of the network, so that the check leaves the network as it was, and with whatever `loss_and_grads` it's given.
