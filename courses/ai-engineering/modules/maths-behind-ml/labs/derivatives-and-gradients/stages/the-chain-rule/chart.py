import numpy as np

from gradients import network_gradient, network_loss

HIDDEN = 4
# How far the weights move along the gradient, in units of its length.
STEPS = np.linspace(-1, 3, 41)


def chart():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    rng = np.random.default_rng(0)
    params = (
        rng.normal(0, 0.5, (X.shape[1], HIDDEN)),
        rng.normal(0, 0.5, HIDDEN),
        rng.normal(0, 0.5, HIDDEN),
        float(rng.normal(0, 0.5)),
    )
    shapes = [np.shape(part) for part in params]
    theta = np.concatenate([np.ravel(part) for part in params])
    gradient = np.concatenate(
        [
            np.ravel(np.asarray(part, dtype=float))
            for part in network_gradient(params, Z, y)
        ]
    )
    length = np.sqrt(np.sum(gradient**2))
    down = -gradient / length

    def loss(t):
        moved, parts, start = theta + t * down, [], 0
        for shape in shapes:
            size = int(np.prod(shape))
            parts.append(moved[start : start + size].reshape(shape))
            start += size
        parts[-1] = float(parts[-1])
        return network_loss(tuple(parts), Z, y)

    along = np.array([loss(t) for t in STEPS])
    slope = (loss(1e-6) - loss(-1e-6)) / 2e-6
    near = STEPS[STEPS <= 1.2]
    return {
        "x": {
            "min": -1,
            "max": 3,
            "step": 1,
            "label": "distance moved down your gradient",
        },
        "y": {"min": 0, "max": 1.2, "step": 0.2, "label": "mean log loss"},
        "lines": [
            {"style": "base", "label": "The loss", "x": STEPS, "y": along},
            {
                "style": "main",
                "label": "The slope your gradient gives",
                "x": near,
                "y": loss(0.0) - length * near,
            },
        ],
        "points": [{"x": 0, "y": loss(0.0)}],
        "readouts": [
            {"label": "Slope your gradient gives", "value": f"{-length:.3f}"},
            {"label": "Slope of the loss", "value": f"{slope:.3f}"},
        ],
        "description": (
            "The network's mean log loss as its weights move down your gradient, with the "
            f"straight line your gradient predicts. Your gradient gives a slope of "
            f"{-length:.3f}, and the loss's own slope there is {slope:.3f}."
        ),
    }
