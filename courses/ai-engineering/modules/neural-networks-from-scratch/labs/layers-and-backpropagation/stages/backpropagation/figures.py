import json

import numpy as np

# The office's network and its training, as the chart has them.
HIDDEN, BATCH, EPOCHS = 64, 64, 10
LR, FAST_LR, HIGH_LR = 0.1, 0.5, 2


def linear(X, weight, bias):
    return X @ weight.T + bias


def train(X, digits, train_rows, lr):
    """The network after training as the chart trains it: its layers, and each pass's
    training loss."""
    rng = np.random.default_rng(0)
    layers = []
    for inputs, outputs in [(X.shape[1], HIDDEN), (HIDDEN, int(digits.max()) + 1)]:
        bound = 1 / np.sqrt(inputs)
        weight = rng.uniform(-bound, bound, size=(outputs, inputs))
        layers.append([weight, rng.uniform(-bound, bound, size=outputs)])

    def logits(rows):
        hidden = linear(X[rows], *layers[0])
        return linear(np.where(hidden > 0, hidden, 0.0), *layers[1]), hidden

    def loss_and_gradient(rows):
        z, hidden = logits(rows)
        shifted = z - z.max(axis=1, keepdims=True)
        log_probs = shifted - np.log(np.exp(shifted).sum(axis=1, keepdims=True))
        n = len(rows)
        dz = np.exp(log_probs)
        dz[np.arange(n), digits[rows]] -= 1
        return -log_probs[np.arange(n), digits[rows]].mean(), dz / n, hidden

    losses = [loss_and_gradient(train_rows)[0]]
    for _ in range(EPOCHS):
        order = rng.permutation(train_rows)
        for start in range(0, len(order), BATCH):
            rows = order[start : start + BATCH]
            _, dz, hidden = loss_and_gradient(rows)
            relu = np.where(hidden > 0, hidden, 0.0)
            dW2, db2 = dz.T @ relu, dz.sum(axis=0)
            dhidden = np.where(hidden > 0, dz @ layers[1][0], 0.0)
            dW1, db1 = dhidden.T @ X[rows], dhidden.sum(axis=0)
            for layer, (dW, db) in zip(layers, [(dW1, db1), (dW2, db2)], strict=True):
                layer[0] = layer[0] - lr * dW
                layer[1] = layer[1] - lr * db
        losses.append(loss_and_gradient(train_rows)[0])
    return logits, losses


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, pixels = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:]
    X = pixels / pixels.max()
    train_rows, validation = np.flatnonzero(sets == 0), sets == 1
    cases = json.loads(open("references/networks.json").read())["networks"]
    classes = int(digits.max()) + 1

    def accuracy(logits):
        return np.mean(
            logits(np.flatnonzero(validation))[0].argmax(axis=1) == digits[validation]
        )

    logits, losses = train(X, digits, train_rows, LR)
    fast, _ = train(X, digits, train_rows, FAST_LR)
    high, high_losses = train(X, digits, train_rows, HIGH_LR)
    dead = int(np.sum(np.all(high(train_rows)[1] <= 0, axis=0)))
    return {
        "hidden": str(len(cases[0]["layers"][0]["bias"])),
        "samples": str(len(cases[0]["X"])),
        "pixels": str(X.shape[1]),
        "units": str(HIDDEN),
        "classes": str(classes),
        "parameters": f"{X.shape[1] * HIDDEN + HIDDEN + HIDDEN * classes + classes:,}",
        "batch": str(BATCH),
        "highest": f"{pixels.max():.0f}",
        "lr": str(LR),
        "epochs": str(EPOCHS),
        "first_loss": f"{losses[0]:.2f}",
        "last_loss": f"{losses[-1]:.2f}",
        "accuracy": f"{accuracy(logits):.1%}",
        "fast_lr": str(FAST_LR),
        "fast_accuracy": f"{accuracy(fast):.1%}",
        "high_lr": str(HIGH_LR),
        "dead": str(dead),
        "high_loss": f"{high_losses[-1]:.2f}",
        "chance": f"{np.log(classes):.2f}",
    }
