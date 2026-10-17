"""Starting weights as torch.nn.init draws them: a uniform range set by how many inputs and
outputs the layer has, and by a gain for the nonlinearity after it."""

import math


def calculate_gain(nonlinearity, param=None):
    """The gain for nonlinearity, as torch.nn.init.calculate_gain gives it: the factor a
    layer's starting range is multiplied by to keep the size of the signal through it."""
    if nonlinearity in ("linear", "sigmoid"):
        return 1.0
    if nonlinearity == "tanh":
        return 5.0 / 3
    if nonlinearity == "relu":
        return math.sqrt(2.0)
    if nonlinearity == "leaky_relu":
        slope = 0.01 if param is None else param
        return math.sqrt(2.0 / (1 + slope**2))
    if nonlinearity == "selu":
        return 3.0 / 4
    raise ValueError(f"Unsupported nonlinearity {nonlinearity}")


def fans(shape):
    """The inputs and the outputs of a layer whose weight has shape (outputs, inputs)."""
    outputs, inputs = shape
    return inputs, outputs


def xavier_uniform(shape, rng, gain=1.0):
    """A weight of shape drawn from U(-a, a), with a = gain * sqrt(6 / (fan_in + fan_out)),
    as torch.nn.init.xavier_uniform_ draws it."""
    fan_in, fan_out = fans(shape)
    bound = gain * math.sqrt(6.0 / (fan_in + fan_out))
    return rng.uniform(-bound, bound, size=shape)


def kaiming_uniform(shape, rng, a=0.0, mode="fan_in", nonlinearity="leaky_relu"):
    """A weight of shape drawn from U(-bound, bound), with bound = gain * sqrt(3 / fan) and
    fan the layer's inputs or its outputs, as torch.nn.init.kaiming_uniform_ draws it."""
    fan_in, fan_out = fans(shape)
    fan = fan_in if mode == "fan_in" else fan_out
    bound = calculate_gain(nonlinearity, a) * math.sqrt(3.0 / fan)
    return rng.uniform(-bound, bound, size=shape)
