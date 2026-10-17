"""Starting weights as torch.nn.init draws them: a uniform range set by how many inputs and
outputs the layer has, and by a gain for the nonlinearity after it."""

import math


def calculate_gain(nonlinearity, param=None):
    """The gain for nonlinearity, as torch.nn.init.calculate_gain gives it: the factor a
    layer's starting range is multiplied by to keep the size of the signal through it."""
    raise NotImplementedError


def fans(shape):
    """The inputs and the outputs of a layer whose weight has shape (outputs, inputs)."""
    outputs, inputs = shape
    return inputs, outputs


def xavier_uniform(shape, rng, gain=1.0):
    """A weight of shape drawn from U(-a, a), with a = gain * sqrt(6 / (fan_in + fan_out)),
    as torch.nn.init.xavier_uniform_ draws it."""
    raise NotImplementedError


def kaiming_uniform(shape, rng, a=0.0, mode="fan_in", nonlinearity="leaky_relu"):
    """A weight of shape drawn from U(-bound, bound), with bound = gain * sqrt(3 / fan) and
    fan the layer's inputs or its outputs, as torch.nn.init.kaiming_uniform_ draws it."""
    raise NotImplementedError
