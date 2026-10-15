import numpy as np
from scipy.spatial.distance import cdist

from gradients import central_difference, forward_difference

# The steps tried, from 10 to the power -16 to 1 in half powers. They are written as
# decimals, which every runtime reads as the same numbers.
POWERS = np.arange(-16, 0.001, 0.5)
STEPS = np.array(
    [float(f"{m}e{e}") for e in range(-16, 0) for m in ("1", "3.1622776601683795")]
    + [1.0]
)


def chart():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    with open("data/breast-cancer.csv") as file:
        j = file.readline().strip().split(",")[2:].index("worst_texture")
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    records, sample = (X - mean) / std, (table[new, 2:][0] - mean) / std
    gap = sample - records[np.argmin(cdist(sample[None, :], records)[0])]
    rest = np.sum(np.delete(gap, j) ** 2)

    def distance(t):
        moved = gap[j] + t
        return float(np.sqrt(rest + moved * moved))

    exact = gap[j] / distance(0.0)
    forward = np.array(
        [abs(forward_difference(distance, 0.0, h) - exact) for h in STEPS]
    )
    central = np.array(
        [abs(central_difference(distance, 0.0, h) - exact) for h in STEPS]
    )
    with np.errstate(divide="ignore", invalid="ignore"):
        lines = [np.log10(forward), np.log10(central)]
    best = [(errors.min(), STEPS[np.argmin(errors)]) for errors in (forward, central)]
    return {
        "x": {"min": -16, "max": 0, "step": 2, "label": "step, as a power of 10"},
        "y": {"min": -12, "max": 0, "step": 2, "label": "error, as a power of 10"},
        "lines": [
            {
                "style": "base",
                "label": "Forward difference",
                "x": POWERS,
                "y": lines[0],
            },
            {
                "style": "main",
                "label": "Central difference",
                "x": POWERS,
                "y": lines[1],
            },
        ],
        "points": [],
        "readouts": [
            {
                "label": "Forward difference, smallest error",
                "value": f"{best[0][0]:.1e}",
            },
            {"label": "Forward difference, best step", "value": f"{best[0][1]:.1e}"},
            {
                "label": "Central difference, smallest error",
                "value": f"{best[1][0]:.1e}",
            },
            {"label": "Central difference, best step", "value": f"{best[1][1]:.1e}"},
        ],
        "description": (
            "How far your forward and central differences fall from the derivative of the "
            "distance to the nearest record, as worst texture changes, for steps from 10 to "
            f"the power -16 to 1. The forward difference comes closest, {best[0][0]:.1e}, at "
            f"a step of {best[0][1]:.1e}, and the central one, {best[1][0]:.1e}, at a step "
            f"of {best[1][1]:.1e}."
        ),
    }
