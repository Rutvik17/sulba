import math

import numpy as np

from model import gradient, log_loss, predict_proba

LOW, HIGH = -2, 10
WEIGHTS = np.linspace(LOW, HIGH, 121)
# The tangent runs this far either side of the weight.
REACH = 1.5
# The learning rate of the step a readout shows.
RATE = 0.5


def worst_radius():
    """The training set's worst radius, scaled to mean 0 and standard deviation 1,
    as a one-column matrix, and the labels."""
    with open("data/breast-cancer.csv") as file:
        columns = file.readline().strip().split(",")[2:]
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    train = table[table[:, 0] == 0]
    x = train[:, 2 + columns.index("worst_radius")]
    return ((x - x.mean()) / x.std())[:, None], train[:, 1]


def top_of(largest, ticks=4):
    """The axis's top and step: a round number of steps of 1, 2, 2.5 or 5 times a
    power of ten, the fewest that reach largest in about four."""
    raw = largest / ticks
    power = 10 ** math.floor(math.log10(raw))
    step = next(f * power for f in (1, 2, 2.5, 5, 10) if raw <= f * power)
    return round(math.ceil(largest / step - 1e-9) * step, 10), round(step, 10)


def chart(w):
    X, y = worst_radius()
    curve = [float(log_loss(y, predict_proba(X, np.array([v]), 0.0))) for v in WEIGHTS]
    loss = float(log_loss(y, predict_proba(X, np.array([w]), 0.0)))
    dw = float(np.ravel(gradient(X, y, np.array([w]), 0.0)[0])[0])
    ends = [max(LOW, w - REACH), min(HIGH, w + REACH)]
    finite = [value for value in curve if math.isfinite(value)]
    top, step = top_of(max(finite)) if finite else (1, 0.25)
    return {
        "x": {"min": LOW, "max": HIGH, "step": 2, "label": "w"},
        "y": {"min": 0, "max": top, "step": step, "label": "log loss"},
        "lines": [
            {"style": "base", "label": "Your log_loss", "x": WEIGHTS, "y": curve},
            {
                "style": "main",
                "label": "Your gradient",
                "x": ends,
                "y": [loss + dw * (x - w) for x in ends],
            },
        ],
        "points": [{"x": w, "y": loss}],
        "readouts": [
            {"label": f"Log loss at w = {w:.1f}, b = 0", "value": f"{loss:.4f}"},
            {"label": f"Gradient at w = {w:.1f}", "value": f"{dw:.4f}"},
            {
                "label": f"w after one step at rate {RATE:g}",
                "value": f"{w - RATE * dw:.3f}",
            },
        ],
        "description": (
            f"Your log loss on scaled worst radius alone, for w from {LOW} to {HIGH} and "
            f"b = 0. At w = {w:.1f} it is {loss:.4f}, with a gradient of {dw:.4f}."
        ),
    }
