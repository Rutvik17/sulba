import numpy as np

from model import mse, predict

T = np.linspace(0, 40, 81)


def chart(w, b):
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    train = table[table[:, 0] == 0]
    temperature, y = train[:, 2], train[:, 1]
    # The training hours' average output at each whole degree.
    degrees = np.round(temperature)
    steps = np.unique(degrees)
    averages = np.array([y[degrees == degree].mean() for degree in steps])

    line = np.asarray(predict(T[:, None], np.array([w]), b), dtype=float)
    error = mse(
        y, np.asarray(predict(temperature[:, None], np.array([w]), b), dtype=float)
    )
    return {
        "x": {"min": 0, "max": 40, "step": 5, "label": "temperature (°C)"},
        "y": {"min": 420, "max": 500, "step": 20, "label": "output (MW)"},
        "lines": [
            {
                "style": "base",
                "label": "Average output at each degree",
                "x": steps,
                "y": averages,
            },
            {"style": "main", "label": "Your line", "x": T, "y": line},
        ],
        "points": [],
        "readouts": [
            {"label": "Mean squared error", "value": f"{error:.1f}"},
            {"label": "RMSE", "value": f"{np.sqrt(error):.2f} MW"},
        ],
        "description": (
            f"Your line, output = {w:g} × temperature + {b:g}, against the training hours' "
            f"average output at each degree. Its RMSE on the training hours is "
            f"{np.sqrt(error):.2f} MW."
        ),
    }
