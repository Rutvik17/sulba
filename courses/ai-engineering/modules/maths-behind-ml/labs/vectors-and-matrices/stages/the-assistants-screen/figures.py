import numpy as np
from scipy.spatial.distance import cdist

PATH = "data/breast-cancer.csv"
K = 5


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X, y = table[~new, 2:], table[~new, 1]
    mean, std = X.mean(axis=0), X.std(axis=0)
    Z, Zn, own = (X - mean) / std, (table[new, 2:] - mean) / std, table[new, 1]
    mu0, mu1 = Z[y == 0].mean(axis=0), Z[y == 1].mean(axis=0)
    w = mu1 - mu0
    u, mid = w / np.linalg.norm(w), (mu0 + mu1) / 2
    right = (Zn - mid) @ u

    # Each problem on its own, with the rest of the code right.
    unscaled = (Zn - mid) @ w
    from_mean = (Zn - Z.mean(axis=0)) @ u
    flips = (from_mean > 0) != (right > 0)
    # The records' mean lies toward the benign mean, so every flip goes from below 0 to above.
    assert np.all(from_mean[flips] > 0)
    D = cdist(Zn, Z)
    nearest = np.argsort(D, axis=1, kind="stable")[:, :K]
    by_dot = np.argsort(-(Zn @ Z.T), axis=1, kind="stable")[:, :K]
    shared = np.array(
        [len(set(a) & set(b)) for a, b in zip(by_dot, nearest, strict=True)]
    )
    first = D[0, nearest[0, 0]]
    return {
        "k": str(K),
        "new": str(len(Zn)),
        "benign": str(int((y == 0).sum())),
        "malignant": str(int((y == 1).sum())),
        "apart": f"{np.linalg.norm(w):.2f}",
        "low": f"{right.min():.2f}",
        "high": f"{right.max():.2f}",
        "wrong_low": f"{unscaled.min():.2f}",
        "wrong_high": f"{unscaled.max():.2f}",
        "shift": f"{(mid - Z.mean(axis=0)) @ u:.2f}",
        "flips": str(int(flips.sum())),
        "flips_benign": str(int(np.sum(flips & (own == 0)))),
        "flips_malignant": str(int(np.sum(flips & (own == 1)))),
        "nearest": f"{first:.2f}",
        "nearest_squared": f"{first**2:.2f}",
        "dot_mean": f"{np.take_along_axis(D, by_dot, axis=1).mean():.2f}",
        "near_mean": f"{np.take_along_axis(D, nearest, axis=1).mean():.2f}",
        "none": str(int(np.sum(shared == 0))),
        "dot_same": f"{np.mean(y[by_dot] == own[:, None]):.1%}",
        "near_same": f"{np.mean(y[nearest] == own[:, None]):.1%}",
    }
