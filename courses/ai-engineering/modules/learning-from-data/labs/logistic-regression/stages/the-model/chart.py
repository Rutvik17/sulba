import numpy as np

from model import sigmoid

# x from -8 to 8 in steps of 0.1, so X[80] is 0.
X = np.linspace(-8, 8, 161)


def chart(w, b):
    yours = np.asarray(sigmoid(w * X + b), dtype=float)
    cross = -b / w
    return {
        "x": {"min": -8, "max": 8, "step": 2, "label": "x"},
        "y": {"min": 0, "max": 1, "step": 0.25, "label": "probability"},
        "lines": [
            {
                "style": "faint",
                "label": "w = 1, b = 0",
                "x": X,
                "y": 1 / (1 + np.exp(-X)),
            },
            {"style": "main", "label": "Your sigmoid", "x": X, "y": yours},
        ],
        "points": [{"x": cross, "y": 0.5}] if -8 <= cross <= 8 else [],
        "readouts": [
            {"label": "Probability at x = 0", "value": f"{yours[80]:.4f}"},
            {"label": "Crosses 0.5 at x", "value": f"{cross:.2f}"},
            {"label": "Slope at the crossing", "value": f"{w / 4:.4f}"},
        ],
        "description": (
            f"Your sigmoid with w = {w:g} and b = {b:g}, crossing 0.5 at x = {cross:.2f}."
        ),
    }
