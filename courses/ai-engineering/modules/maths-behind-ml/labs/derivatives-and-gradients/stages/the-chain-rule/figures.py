import numpy as np

PATH = "data/breast-cancer.csv"
HIDDEN = 4
# The network's gradient by the chain rule stays this close to central differences.
BOUND = 1e-8


def loss(params, Z, y):
    W1, b1, w2, b2 = params
    s = np.tanh(Z @ W1 + b1) @ w2 + b2
    return float(np.mean(np.logaddexp(0, s) - y * s))


def gradient(params, Z, y):
    W1, b1, w2, b2 = params
    hidden = np.tanh(Z @ W1 + b1)
    s = hidden @ w2 + b2
    ds = (np.exp(-np.logaddexp(0, -s)) - y) / len(y)
    dpre = np.outer(ds, w2) * (1 - hidden**2)
    return [Z.T @ dpre, dpre.sum(axis=0), hidden.T @ ds, float(ds.sum())]


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    rng = np.random.default_rng(0)
    d = X.shape[1]
    params = [
        rng.normal(0, 0.5, (d, HIDDEN)),
        rng.normal(0, 0.5, HIDDEN),
        rng.normal(0, 0.5, HIDDEN),
        float(rng.normal(0, 0.5)),
    ]
    sizes = [int(np.size(part)) for part in params]
    theta = np.concatenate([np.ravel(part) for part in params])

    def at(t):
        parts, start = [], 0
        for part, size in zip(params, sizes, strict=True):
            parts.append(t[start : start + size].reshape(np.shape(part)))
            start += size
        parts[-1] = float(parts[-1])
        return loss(parts, Z, y)

    numerical = np.zeros(len(theta))
    for i in range(len(theta)):
        step = np.zeros(len(theta))
        step[i] = 1e-6
        numerical[i] = (at(theta + step) - at(theta - step)) / 2e-6
    exact = np.concatenate([np.ravel(part) for part in gradient(params, Z, y)])
    error = np.linalg.norm(exact - numerical) / np.linalg.norm(exact)
    assert error < BOUND
    return {
        "records": str(len(y)),
        "measurements": str(d),
        "hidden": str(HIDDEN),
        "parameters": str(len(theta)),
        "evaluations": str(2 * len(theta)),
        "loss": f"{loss(params, Z, y):.3f}",
        "length": f"{np.linalg.norm(exact):.3f}",
        "bound": f"{-np.log10(BOUND):.0f}",
    }
