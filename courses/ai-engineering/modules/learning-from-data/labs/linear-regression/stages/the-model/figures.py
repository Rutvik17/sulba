import numpy as np


def figures():
    table = np.loadtxt("data/power-plant.csv", delimiter=",", skiprows=1)
    test = table[:, 0] == 1
    y_train, y_test = table[~test, 1], table[test, 1]
    mean = round(float(y_train.mean()), 2)
    found = {
        "n_train": f"{len(y_train):,}",
        "n_test": f"{len(y_test):,}",
        "n_features": str(table.shape[1] - 2),
        "mean": f"{mean:.2f}",
        "rmse_mean": f"{np.sqrt(np.mean((y_test - y_train.mean()) ** 2)):.1f}",
    }
    # The worked example: the first three test hours, forecast at the mean as the prose
    # shows it, to two decimal places.
    squares = []
    for hour, y in enumerate(y_test[:3], start=1):
        miss = round(float(y) - mean, 2)
        squares.append(round(miss**2, 2))
        found[f"y_{hour}"] = f"{y:.2f}"
        found[f"miss_{hour}"] = f"{miss:.2f}"
        found[f"square_{hour}"] = f"{squares[-1]:.2f}"
    found["mse_3"] = f"{sum(squares) / 3:.2f}"
    return found
