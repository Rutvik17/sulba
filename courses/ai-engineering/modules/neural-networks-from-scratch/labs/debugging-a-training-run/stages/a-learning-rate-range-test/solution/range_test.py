"""A learning-rate range test: one short run with the learning rate rising at every step."""

import numpy as np

from network import loss_and_grads


def range_test(
    params, batches, lr_min, lr_max, beta=0.98, stop=4.0, loss_and_grads=loss_and_grads
):
    """A step of SGD on each batch, taken by a copy of the network, at learning rates rising
    geometrically from lr_min to lr_max: the learning rates and the smoothed loss before
    each step, up to the step where the smoothed loss passes stop times its lowest."""
    params = [param.copy() for param in params]
    lrs = np.geomspace(lr_min, lr_max, len(batches))
    average, smoothed = 0.0, []
    for step, (lr, (X, digits)) in enumerate(zip(lrs, batches, strict=True), start=1):
        loss, grads = loss_and_grads(params, X, digits)
        average = beta * average + (1 - beta) * loss
        smoothed.append(average / (1 - beta**step))
        if not np.isfinite(smoothed[-1]) or smoothed[-1] > stop * min(smoothed):
            break
        for param, grad in zip(params, grads, strict=True):
            param -= lr * grad
    return lrs[: len(smoothed)], np.array(smoothed)


def lowest(lrs, smoothed):
    """The learning rate at the lowest smoothed loss."""
    return lrs[int(np.argmin(smoothed))]
