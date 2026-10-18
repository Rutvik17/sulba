"""The office's network: a weight and a bias for each linear layer, with a ReLU after
each but the last, trained on the mean cross-entropy of its batches."""

import numpy as np

WIDTHS = (64, 64, 32, 10)


def network(rng, widths=WIDTHS):
    """A weight and a bias for each linear layer, drawn as torch.nn.Linear draws them."""
    params = []
    for inputs, outputs in zip(widths, widths[1:]):
        bound = 1 / np.sqrt(inputs)
        params.append(rng.uniform(-bound, bound, size=(outputs, inputs)))
        params.append(rng.uniform(-bound, bound, size=outputs))
    return params


def forward(params, X):
    """Each layer's input, each ReLU's input, and the logits."""
    inputs, before = [X], []
    for number in range(0, len(params), 2):
        out = inputs[-1] @ params[number].T + params[number + 1]
        if number + 2 == len(params):
            return inputs, before, out
        before.append(out)
        inputs.append(np.maximum(out, 0.0))


def loss_and_grads(params, X, digits):
    """The batch's mean cross-entropy, and its gradient with respect to each parameter."""
    inputs, before, logits = forward(params, X)
    shifted = logits - logits.max(axis=1, keepdims=True)
    log_sums = np.log(np.exp(shifted).sum(axis=1))
    loss = np.mean(log_sums - shifted[np.arange(len(digits)), digits])
    d = np.exp(shifted - log_sums[:, None])
    d[np.arange(len(digits)), digits] -= 1
    d /= len(digits)
    grads = [None] * len(params)
    for number in range(len(params) - 2, -1, -2):
        grads[number] = d.T @ inputs[number // 2]
        grads[number + 1] = d.sum(axis=0)
        if number:
            d = (d @ params[number]) * (before[number // 2 - 1] > 0)
    return loss, grads


def start_loss(params, X, digits):
    """The network's loss on X before any step, and the log of its number of classes,
    which the loss should be near."""
    raise NotImplementedError


def learn_by_heart(params, X, digits, steps=300, lr=0.5, loss_and_grads=loss_and_grads):
    """The loss before each of steps steps of SGD on the one batch, taken by a copy of the
    network, which leaves params as they were."""
    raise NotImplementedError


def first_below(losses, below=0.01):
    """The number of the first step whose loss is below below, counting from 1, or None."""
    raise NotImplementedError
