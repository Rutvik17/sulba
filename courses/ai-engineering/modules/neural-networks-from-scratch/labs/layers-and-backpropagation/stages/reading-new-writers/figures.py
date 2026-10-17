import numpy as np

# The checks' target and time limit, and the solution's network and training.
TARGET, LIMIT_S = 0.95, 2
HIDDEN, EPOCHS, BATCH, LR = 32, 20, 64, 0.1
DIGITS = 10


def trained(pixels, digits, rng):
    """The solution's reader, trained as it trains."""
    mean, spread = pixels.mean(axis=0), pixels.std(axis=0)
    spread = np.where(spread > 0, spread, 1.0)
    X = (pixels - mean) / spread
    layers = []
    for inputs, outputs in [(X.shape[1], HIDDEN), (HIDDEN, DIGITS)]:
        bound = 1 / np.sqrt(inputs)
        weight = rng.uniform(-bound, bound, size=(outputs, inputs))
        layers.append([weight, rng.uniform(-bound, bound, size=outputs)])

    def forward(batch):
        hidden = batch @ layers[0][0].T + layers[0][1]
        relu = np.where(hidden > 0, hidden, 0.0)
        return relu @ layers[1][0].T + layers[1][1], hidden, relu

    for _ in range(EPOCHS):
        order = rng.permutation(len(digits))
        for start in range(0, len(order), BATCH):
            rows = order[start : start + BATCH]
            z, hidden, relu = forward(X[rows])
            shifted = z - z.max(axis=1, keepdims=True)
            dz = np.exp(shifted) / np.exp(shifted).sum(axis=1, keepdims=True)
            dz[np.arange(len(rows)), digits[rows]] -= 1
            dz = dz / len(rows)
            dhidden = np.where(hidden > 0, dz @ layers[1][0], 0.0)
            gradients = [
                (dhidden.T @ X[rows], dhidden.sum(axis=0)),
                (dz.T @ relu, dz.sum(axis=0)),
            ]
            for layer, (dW, db) in zip(layers, gradients, strict=True):
                layer[0] = layer[0] - LR * dW
                layer[1] = layer[1] - LR * db
    return lambda batch: forward((batch - mean) / spread)[0].argmax(axis=1)


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, pixels = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:]
    read = trained(pixels[sets == 0], digits[sets == 0], np.random.default_rng(0))

    def share(rows):
        return np.mean(read(pixels[rows]) == digits[rows])

    constant = int(np.sum(pixels[sets == 0].std(axis=0) == 0))
    return {
        "target": f"{TARGET:.0%}",
        "limit": str(LIMIT_S),
        "training": f"{np.sum(sets == 0):,}",
        "validation": f"{np.sum(sets == 1):,}",
        "test": f"{np.sum(sets == 2):,}",
        "pixels": str(pixels.shape[1]),
        "constant": str(constant),
        "hidden": str(HIDDEN),
        "epochs": str(EPOCHS),
        "batch": str(BATCH),
        "lr": str(LR),
        "validation_share": f"{share(sets == 1):.1%}",
        "test_share": f"{share(sets == 2):.1%}",
    }
