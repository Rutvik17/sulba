import numpy as np

from engine import Value

XS = np.linspace(0.5, 3, 51)
# The values each axis spans for each power, and the step between its ticks.
AXES = {-1: (-4, 2, 1), 0.5: (0, 2, 0.5), 2: (0, 9, 1), 3: (0, 27, 3)}


def chart(power):
    values, slopes = [], []
    for x in XS:
        a = Value(x)
        out = a**power
        out.backward()
        values.append(out.data)
        slopes.append(a.grad)
    low, high, step = AXES[power]
    one = Value(1.0)
    (one**power).backward()
    return {
        "x": {"min": 0.5, "max": 3, "step": 0.5, "label": "a"},
        "y": {"min": low, "max": high, "step": step, "label": "value"},
        "lines": [
            {"style": "base", "label": "a to the power p", "x": XS, "y": values},
            {
                "style": "dashed",
                "label": "p times a to the power p − 1",
                "x": XS,
                "y": power * XS ** (power - 1),
            },
            {
                "style": "main",
                "label": "Its slope from your engine",
                "x": XS,
                "y": slopes,
            },
        ],
        "points": [],
        "readouts": [{"label": "Slope at a = 1", "value": f"{one.grad:g}"}],
        "description": f"a to the power {power} and its slope from your engine",
    }
