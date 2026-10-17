"""The office's reader: a network trained on the training digits."""

import numpy as np

from layers import Network, ReLU, cross_entropy, linear_layer


def train(pixels, digits, rng):
    """A network trained on pixels, a row of counts for each digit, and the digits they
    show, with rng for all that's random. Returns read, which gives the digit it reads
    for each row of a batch of pixels."""
    raise NotImplementedError
