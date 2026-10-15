import numpy as np

from vectors import fast_distances

GAP = 3
# The first sample sits at 10 to each of these powers, the second GAP further.
POWERS = np.arange(0, 9.001, 0.25)


def chart():
    found = []
    for power in POWERS:
        start = float(round(10**power))
        pair = fast_distances(np.array([[start]]), np.array([[start + GAP]]))
        found.append(float(np.asarray(pair, dtype=float).reshape(-1)[0]))
    found = np.array(found)
    wrong = np.flatnonzero(~np.isclose(found, GAP, rtol=1e-12, atol=0))
    at8, at9 = found[np.isclose(POWERS, 8)][0], found[-1]
    if not len(wrong):
        held = f"It is {GAP} at every power"
    elif wrong[0] == 0:
        held = f"It is not {GAP} even at 1"
    else:
        held = f"It is {GAP} up to 10 to the power {POWERS[wrong[0] - 1]:g}"
    return {
        "x": {
            "min": 0,
            "max": 9,
            "step": 1,
            "label": "where the samples sit, as a power of 10",
        },
        "y": {"min": 0, "max": 4, "step": 1, "label": "distance between them"},
        "lines": [
            {
                "style": "dashed",
                "label": "Their distance",
                "x": [0, 9],
                "y": [GAP, GAP],
            },
            {"style": "main", "label": "Your fast distance", "x": POWERS, "y": found},
        ],
        "points": [],
        "readouts": [
            {"label": f"At {10**8:,}", "value": f"{at8:.2f}"},
            {"label": f"At {10**9:,}", "value": f"{at9:.2f}"},
        ],
        "description": (
            f"Your fast distance between two samples {GAP} apart in one measurement, the "
            f"first at 10 to the power on the x axis. {held}. At {10**8:,} it is "
            f"{at8:.2f}, and at {10**9:,} it is {at9:.2f}."
        ),
    }
