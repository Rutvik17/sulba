import json
import warnings

import numpy as np

# The office's network and its training, as stage 3's chart has them.
HIDDEN, BATCH, EPOCHS, LR = 64, 64, 10, 0.1
LAYERS = 3


def trained_accuracy(X, digits, train_rows, validation_rows, mistake=None):
    """The share of the validation digits read right after training as the chart trains,
    with the gradient left as the batch's sum, or added up from step to step."""
    rng = np.random.default_rng(0)
    layers = []
    for inputs, outputs in [(X.shape[1], HIDDEN), (HIDDEN, int(digits.max()) + 1)]:
        bound = 1 / np.sqrt(inputs)
        weight = rng.uniform(-bound, bound, size=(outputs, inputs))
        layers.append([weight, rng.uniform(-bound, bound, size=outputs)])
    sums = [[0.0, 0.0], [0.0, 0.0]]

    def forward(rows):
        hidden = X[rows] @ layers[0][0].T + layers[0][1]
        relu = np.where(hidden > 0, hidden, 0.0)
        return relu @ layers[1][0].T + layers[1][1], hidden, relu

    for _ in range(EPOCHS):
        order = rng.permutation(train_rows)
        for start in range(0, len(order), BATCH):
            rows = order[start : start + BATCH]
            z, hidden, relu = forward(rows)
            shifted = z - z.max(axis=1, keepdims=True)
            dz = np.exp(shifted) / np.exp(shifted).sum(axis=1, keepdims=True)
            dz[np.arange(len(rows)), digits[rows]] -= 1
            if mistake != "unaveraged":
                dz = dz / len(rows)
            dhidden = np.where(hidden > 0, dz @ layers[1][0], 0.0)
            gradients = [
                (dhidden.T @ X[rows], dhidden.sum(axis=0)),
                (dz.T @ relu, dz.sum(axis=0)),
            ]
            for number, (dW, db) in enumerate(gradients):
                if mistake == "accumulated":
                    sums[number] = [sums[number][0] + dW, sums[number][1] + db]
                    dW, db = sums[number]
                layers[number][0] = layers[number][0] - LR * dW
                layers[number][1] = layers[number][1] - LR * db
    logits = forward(validation_rows)[0]
    return np.mean(logits.argmax(axis=1) == digits[validation_rows])


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, pixels = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:]
    X = pixels / pixels.max()
    train_rows, validation_rows = np.flatnonzero(sets == 0), np.flatnonzero(sets == 1)
    confident = json.loads(open("references/activations.json").read())["cross_entropy"][
        -1
    ]
    logits = np.array(confident["logits"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exps = np.exp(logits)
        rows = np.arange(len(confident["labels"]))
        unshifted = np.mean(
            np.log(exps.sum(axis=1)) - logits[rows, confident["labels"]]
        )
        gradient = exps / exps.sum(axis=1)[:, None]
    # The assistant's softmax: an infinite loss and a gradient of nan.
    assert np.isinf(unshifted) and np.isnan(gradient).any()
    accuracy = trained_accuracy(X, digits, train_rows, validation_rows)
    return {
        "batch": str(BATCH),
        "lr": str(LR),
        "unaveraged": f"{trained_accuracy(X, digits, train_rows, validation_rows, 'unaveraged'):.1%}",
        "accuracy": f"{accuracy:.1%}",
        "overflow": f"{np.log(np.finfo(np.float64).max):.1f}",
        "largest": f"{np.max(np.abs(logits)):,.0f}",
        "confident_loss": f"{confident['loss']:.1f}",
        "layers": str(LAYERS),
        "classes": str(int(digits.max()) + 1),
        "units": str(HIDDEN),
        "accumulated": f"{trained_accuracy(X, digits, train_rows, validation_rows, 'accumulated'):.1%}",
    }
