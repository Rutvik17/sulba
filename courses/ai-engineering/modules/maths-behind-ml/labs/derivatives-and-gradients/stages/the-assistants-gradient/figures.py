import numpy as np

PATH = "data/breast-cancer.csv"
HIDDEN, L2, SCALE = 4, 0.1, 1000


def parts(params, Z, y):
    """The forward pass's pieces: the hidden layer's inputs and outputs, and the loss's slope
    along each score."""
    W1, b1, w2, b2 = params
    pre = Z @ W1 + b1
    hidden = np.tanh(pre)
    ds = (np.exp(-np.logaddexp(0, -(hidden @ w2 + b2))) - y) / len(y)
    return pre, hidden, ds


def relative_error(a, b):
    """The length of a - b as a share of the longer of a and b, as stage 2 defines it."""
    return np.linalg.norm(a - b) / max(np.linalg.norm(a), np.linalg.norm(b))


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    X, y = table[table[:, 0] == 0, 2:], table[table[:, 0] == 0, 1]
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    rng = np.random.default_rng(1)
    d = X.shape[1]
    W1, b1, w2, b2 = (
        rng.normal(0, 0.5, (d, HIDDEN)),
        rng.normal(0, 0.5, HIDDEN),
        rng.normal(0, 0.5, HIDDEN),
        float(rng.normal(0, 0.5)),
    )
    pre, hidden, ds = parts((W1, b1, w2, b2), Z, y)

    # Each problem on its own, with the rest of the code right.
    right_hidden = np.outer(ds, w2) * (1 - hidden**2)
    wrong_hidden = np.outer(ds, w2) * (1 - hidden)
    right_layer = np.concatenate(
        [np.ravel(Z.T @ right_hidden), right_hidden.sum(axis=0)]
    )
    wrong_layer = np.concatenate(
        [np.ravel(Z.T @ wrong_hidden), wrong_hidden.sum(axis=0)]
    )
    decayed = Z.T @ right_hidden + L2 * W1

    confident = SCALE * (hidden @ w2 + b2)
    overflow = np.log(np.finfo(np.float64).max)
    big_loss = np.mean(np.logaddexp(0, confident) - y * confident)
    return {
        "tanh_off": f"{relative_error(wrong_layer, right_layer):.2f}",
        "l2": f"{L2:g}",
        "decay_share": f"{np.linalg.norm(L2 * W1) / np.linalg.norm(decayed):.0%}",
        "w2_off": f"{relative_error(pre.T @ ds, hidden.T @ ds):.2f}",
        "overflow": f"{overflow:.2f}",
        "scale": f"{SCALE:,}",
        "above": str(int(np.sum(confident > overflow))),
        "records": str(len(y)),
        "max_score": f"{confident.max():,.0f}",
        "big_loss": f"{big_loss:.1f}",
    }
