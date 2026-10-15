import numpy as np
from scipy.spatial.distance import cdist

PATH = "data/breast-cancer.csv"
# Two samples GAP apart in one measurement, at FAR and FURTHER from 0.
FAR, FURTHER, GAP = 100_000_000, 1_000_000_000, 3
# Two samples whose squared distance rounding takes below 0.
LOW, HIGH = 100_000_000.75, 100_000_001.5
# The fast distances between the clinic's standardized samples stay this close to cdist's.
BOUND = 1e-13


def squared(a, b):
    """The squared distances from the rows of a to the rows of b, from dot products."""
    return np.sum(a**2, axis=1)[:, None] + np.sum(b**2, axis=1)[None, :] - 2 * (a @ b.T)


def one(a, b):
    """The squared distance between two samples of one measurement, from dot products."""
    return float(
        squared(np.array([[a]], dtype=float), np.array([[b]], dtype=float))[0, 0]
    )


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    A, B = (table[new, 2:] - mean) / std, (X - mean) / std
    m, n, d = len(A), len(B), X.shape[1]
    exact = cdist(A, B)
    fast = np.sqrt(np.maximum(squared(A, B), 0))
    assert np.max(np.abs(fast - exact) / exact) < BOUND
    far, further, below = (
        one(FAR, FAR + GAP),
        one(FURTHER, FURTHER + GAP),
        one(LOW, HIGH),
    )
    # Near 10^16 a float64 holds only even whole numbers, so the odd square is rounded.
    assert np.spacing(float(FAR) ** 2) == 2 and (FAR + GAP) ** 2 % 2 == 1
    return {
        "new": str(m),
        "records": str(n),
        "measurements": str(d),
        "multiplications": f"{m * n * d:,}",
        "pairs": f"{m * n:,}",
        "result_mb": f"{m * n * 8 / 1e6:.1f}",
        "broadcast_mb": f"{m * n * d * 8 / 1e6:.1f}",
        "digits": str(np.finfo(np.float64).precision),
        "gap": str(GAP),
        "gap_squared": str(GAP**2),
        "far": f"{FAR:,}",
        "far_plus": f"{FAR + GAP:,}",
        "far_plus_squared": f"{(FAR + GAP) ** 2:,}",
        "spacing": f"{np.spacing(float(FAR) ** 2):.0f}",
        "stored": f"{int(np.square(np.float64(FAR + GAP))):,}",
        "far_squared": f"{far:.0f}",
        "far_distance": f"{np.sqrt(far):.2f}",
        "further": f"{FURTHER:,}",
        "further_distance": f"{np.sqrt(max(further, 0)):.0f}",
        "low": f"{LOW:,}",
        "high": f"{HIGH:,}",
        "below": f"{below:.0f}",
        "true_below": f"{(HIGH - LOW) ** 2:g}",
        "bound": f"{-np.log10(BOUND):.0f}",
    }
