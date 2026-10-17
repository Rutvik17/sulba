import math

import numpy as np

# The office's deep network and its training, and what it must read of new writers' digits.
WIDTHS, BATCH, STEPS, LR, TARGET = (64,) + (32,) * 8 + (10,), 64, 200, 0.3, 0.9
# How many test digits the checks read alone, one at a time.
ALONE = 50
# PyTorch's defaults for BatchNorm1d and LayerNorm.
EPS, MOMENTUM = 1e-5, 0.1


class Linear:
    def __init__(self, weight, bias):
        self.weight, self.bias = weight, bias

    def forward(self, X, training):
        self.X = X
        return X @ self.weight.T + self.bias

    def backward(self, dY):
        self.grads = [dY.T @ self.X, dY.sum(axis=0)]
        return dY @ self.weight

    def params(self):
        return [self.weight, self.bias]


class ReLU:
    grads = []

    def forward(self, X, training):
        self.X = X
        return np.maximum(X, 0.0)

    def backward(self, dY):
        return dY * (self.X > 0)

    def params(self):
        return []


class Norm:
    """Batch normalization over axis 0, with running estimates, or layer normalization
    over axis -1."""

    def __init__(self, features, axis):
        self.axis = axis
        self.weight, self.bias = np.ones(features), np.zeros(features)
        self.running_mean, self.running_var = np.zeros(features), np.ones(features)

    def forward(self, X, training):
        if self.axis == -1 or training:
            mean = X.mean(axis=self.axis, keepdims=True)
            var = X.var(axis=self.axis, keepdims=True)
        else:
            mean, var = self.running_mean, self.running_var
        if self.axis == 0 and training:
            n, keep = len(X), 1 - MOMENTUM
            self.running_mean = keep * self.running_mean + MOMENTUM * mean[0]
            self.running_var = keep * self.running_var + MOMENTUM * var[0] * n / (n - 1)
        self.scale = 1 / np.sqrt(var + EPS)
        self.normalized = (X - mean) * self.scale
        return self.weight * self.normalized + self.bias

    def backward(self, dY):
        self.grads = [(dY * self.normalized).sum(axis=0), dY.sum(axis=0)]
        n = dY.shape[self.axis]
        dnormalized = dY * self.weight
        summed = dnormalized.sum(axis=self.axis, keepdims=True)
        along = (dnormalized * self.normalized).sum(axis=self.axis, keepdims=True)
        return self.scale / n * (n * dnormalized - summed - self.normalized * along)

    def params(self):
        return [self.weight, self.bias]


def network(rng, gain, axis):
    """The hidden layers' weights drawn from U(-a, a), with a = gain / sqrt(inputs), their
    biases at 0 and a normalization along axis after each, if any, then a last layer as
    torch.nn.Linear starts it."""
    layers = []
    for number, (inputs, outputs) in enumerate(zip(WIDTHS, WIDTHS[1:])):
        bound = 1 / math.sqrt(inputs)
        if number == len(WIDTHS) - 2:
            weight = rng.uniform(-bound, bound, size=(outputs, inputs))
            layers.append(Linear(weight, rng.uniform(-bound, bound, size=outputs)))
            return layers
        weight = rng.uniform(-gain * bound, gain * bound, size=(outputs, inputs))
        layers.append(Linear(weight, np.zeros(outputs)))
        if axis is not None:
            layers.append(Norm(outputs, axis))
        layers.append(ReLU())


def batches(rng, rows, steps):
    """steps batches of BATCH rows, in an order shuffled for each pass over them."""
    order = []
    while len(order) < steps * BATCH:
        order.extend(rng.permutation(rows))
    return [np.array(order[i * BATCH : (i + 1) * BATCH]) for i in range(steps)]


def logits(layers, X, training=False):
    for layer in layers:
        X = layer.forward(X, training)
    return X


def trained(office, gain, axis):
    """The office's network with a start and a normalization, after its training."""
    X, digits, sets = office
    rng = np.random.default_rng(0)
    layers = network(rng, gain, axis)
    for rows in batches(rng, np.flatnonzero(sets == 0), STEPS):
        out = logits(layers, X[rows], True)
        exps = np.exp(out - out.max(axis=1, keepdims=True))
        d = exps / exps.sum(axis=1, keepdims=True)
        d[np.arange(BATCH), digits[rows]] -= 1
        d /= BATCH
        for layer in reversed(layers):
            d = layer.backward(d)
        for layer in layers:
            for param, grad in zip(layer.params(), layer.grads, strict=True):
                param -= LR * grad
    return layers


def share(office, layers, part):
    X, digits, sets = office
    rows = sets == part
    return np.mean(logits(layers, X[rows]).argmax(axis=1) == digits[rows])


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    office = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]
    sets = office[2]
    # Kaiming's gain for a ReLU times sqrt(3), against nn.Linear's 1.
    kaiming = math.sqrt(2) * math.sqrt(3)
    # Without batch normalization, training at this learning rate is so unsteady that the
    # last digit of a sum changes how many digits it reads, so the prose says only that it
    # falls short.
    short = [trained(office, kaiming, axis) for axis in (None, -1)]
    assert max(share(office, layers, 1) for layers in short) < TARGET
    chosen = trained(office, 1.0, 0)
    return {
        "hidden": str(len(WIDTHS) - 2),
        "width": str(WIDTHS[1]),
        "steps": str(STEPS),
        "lr": f"{LR:g}",
        "batch": str(BATCH),
        "target": f"{TARGET:.0%}",
        "training": str(np.sum(sets == 0)),
        "validation": str(np.sum(sets == 1)),
        "test": str(np.sum(sets == 2)),
        "alone": str(ALONE),
        "batch_kaiming": f"{share(office, trained(office, kaiming, 0), 1):.1%}",
        "batch_default": f"{share(office, chosen, 1):.1%}",
        "chosen_test": f"{share(office, chosen, 2):.1%}",
        "ratio": f"{kaiming:.2f}",
        "factor": f"{kaiming**2:.0f}",
    }
