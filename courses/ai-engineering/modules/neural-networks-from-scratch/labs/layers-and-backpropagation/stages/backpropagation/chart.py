import numpy as np

from layers import Network, ReLU, cross_entropy, linear_layer

# The office's network, and how it trains: batches of this many digits, for this many
# passes over the training digits.
HIDDEN, BATCH, EPOCHS = 64, 64, 10


def chart(lr):
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, pixels = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:]
    X = pixels / pixels.max()
    train, validation = sets == 0, sets == 1
    rng = np.random.default_rng(0)
    network = Network(
        [
            linear_layer(X.shape[1], HIDDEN, rng),
            ReLU(),
            linear_layer(HIDDEN, int(digits.max()) + 1, rng),
        ]
    )

    def loss(rows):
        return cross_entropy(network.forward(X[rows]), digits[rows])[0]

    training, held = [loss(train)], [loss(validation)]
    for _ in range(EPOCHS):
        order = rng.permutation(np.flatnonzero(train))
        for start in range(0, len(order), BATCH):
            batch = order[start : start + BATCH]
            _, dlogits = cross_entropy(network.forward(X[batch]), digits[batch])
            network.backward(dlogits)
            network.step(lr)
        training.append(loss(train))
        held.append(loss(validation))
    read = np.mean(network.forward(X[validation]).argmax(axis=1) == digits[validation])
    hidden = network.layers[0].forward(X[train])
    dead = int(np.sum(np.all(hidden <= 0, axis=0)))
    passes = np.arange(EPOCHS + 1)
    return {
        "x": {
            "min": 0,
            "max": EPOCHS,
            "step": 2,
            "label": "passes over the training digits",
        },
        "y": {"min": 0, "max": 2.5, "step": 0.5, "label": "mean cross-entropy"},
        "lines": [
            {"style": "base", "label": "Validation loss", "x": passes, "y": held},
            {"style": "main", "label": "Training loss", "x": passes, "y": training},
        ],
        "points": [],
        "readouts": [
            {"label": "Validation digits read right", "value": f"{read:.1%}"},
            {"label": "Hidden units that pass nothing", "value": f"{dead} of {HIDDEN}"},
        ],
        "description": (
            f"The training and validation loss over {EPOCHS} passes at a learning rate"
            f" of {lr}"
        ),
    }
