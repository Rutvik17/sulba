"""The office's reader, trained in PyTorch."""

import numpy as np
import torch

from digits import scaled
from network import logits, parameters, step

HIDDEN, EPOCHS, BATCH, LR = 32, 20, 64, 0.1
DIGITS = 10


def train(pixels, digits, rng):
    """The NumPy reader's network trained on pixels, a row of counts for each digit, and the
    digits they show, step for step as the NumPy reader trained it, with rng for all that's
    random. Returns read, which gives the digit it reads for each row of a batch of pixels."""
    start = {}
    for layer, (inputs, outputs) in enumerate(
        [(pixels.shape[1], HIDDEN), (HIDDEN, DIGITS)], 1
    ):
        bound = 1 / np.sqrt(inputs)
        start[f"w{layer}"] = rng.uniform(-bound, bound, size=(outputs, inputs))
        start[f"b{layer}"] = rng.uniform(-bound, bound, size=outputs)
    params = parameters(start)
    X = scaled(pixels, pixels)
    for _ in range(EPOCHS):
        order = torch.from_numpy(rng.permutation(len(digits)))
        for begin in range(0, len(order), BATCH):
            rows = order[begin : begin + BATCH]
            step(params, X[rows], digits[rows], LR)

    def read(batch):
        with torch.no_grad():
            return logits(params, scaled(batch, pixels)).argmax(dim=1)

    return read
