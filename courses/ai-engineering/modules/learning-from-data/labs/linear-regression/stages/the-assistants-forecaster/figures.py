import numpy as np
from sklearn.linear_model import LinearRegression

COLUMNS = ["temperature", "vacuum", "pressure", "humidity"]


def figures():
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    X, y = table[:, 2:], table[:, 1]
    X_train, y_train, X_test = X[~test], y[~test], X[test]
    model = LinearRegression().fit(X_train, y_train)
    yours = model.predict(X_test)
    # The measurements in alphabetical order, as sorted(weather) gives them.
    misordered = model.predict(
        X_test[:, [COLUMNS.index(name) for name in sorted(COLUMNS)]]
    )
    cold = model.predict(
        np.array([[-5.0, 40.0, 1015.0, 70.0], [-10.0, 40.0, 1015.0, 70.0]])
    )
    return {
        "misordered_low": f"{np.floor(misordered.min()):.0f}",
        "misordered_high": f"{np.ceil(misordered.max()):.0f}",
        "yours_low": f"{np.floor(yours.min()):.0f}",
        "yours_high": f"{np.ceil(yours.max()):.0f}",
        "lowest": f"{y_train.min():.2f}",
        "highest": f"{y_train.max():.2f}",
        "cold_1": f"{cold[0]:.1f}",
        "cold_2": f"{cold[1]:.1f}",
    }
