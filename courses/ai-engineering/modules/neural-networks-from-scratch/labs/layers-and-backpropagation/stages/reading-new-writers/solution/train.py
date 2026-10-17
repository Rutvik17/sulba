"""The office's reader: a network trained on the training digits."""

import numpy as np

from layers import Network, ReLU, cross_entropy, linear_layer

HIDDEN, EPOCHS, BATCH, LR = 32, 20, 64, 0.1
DIGITS = 10


def train(pixels, digits, rng):
    """A network trained on pixels, a row of counts for each digit, and the digits they
    show, with rng for all that's random. Returns read, which gives the digit it reads
    for each row of a batch of pixels."""
    mean = pixels.mean(axis=0)
    spread = pixels.std(axis=0)
    # A pixel that never varies in training would be divided by 0.
    spread = np.where(spread > 0, spread, 1.0)

    def scaled(batch):
        return (batch - mean) / spread

    X = scaled(pixels)
    network = Network(
        [
            linear_layer(X.shape[1], HIDDEN, rng),
            ReLU(),
            linear_layer(HIDDEN, DIGITS, rng),
        ]
    )
    for _ in range(EPOCHS):
        order = rng.permutation(len(digits))
        for start in range(0, len(order), BATCH):
            batch = order[start : start + BATCH]
            _, dlogits = cross_entropy(network.forward(X[batch]), digits[batch])
            network.backward(dlogits)
            network.step(LR)

    def read(batch):
        return network.forward(scaled(batch)).argmax(axis=1)

    return read
