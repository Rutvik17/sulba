"""The office's reader, trained in PyTorch."""

import numpy as np
import torch

from digits import scaled
from network import logits, parameters, step


def train(pixels, digits, rng):
    """The NumPy reader's network trained on pixels, a row of counts for each digit, and the
    digits they show, step for step as the NumPy reader trained it, with rng for all that's
    random. Returns read, which gives the digit it reads for each row of a batch of pixels."""
    raise NotImplementedError
