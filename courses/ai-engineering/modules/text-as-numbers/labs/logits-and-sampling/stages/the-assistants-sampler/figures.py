import numpy as np
import pandas as pd
from scipy import special

# The model's temperature and top-p, as in sampler.py, with top-k keeping all the
# logits the file has, and the seed sampler.py draws from.
TEMPERATURE, TOP_P, SEED = 0.7, 0.8, 0


def warp(logits, temperature, crossing_kept=True):
    """The probabilities after temperature and top-p, keeping the token that reaches
    p or, as the assistant's code does, dropping it."""
    probabilities = special.softmax(np.asarray(logits) / temperature)
    order = np.argsort(-probabilities, kind="stable")
    total = np.cumsum(probabilities[order])
    if crossing_kept:
        removed = total[1:] - probabilities[order][1:] >= TOP_P
    else:
        removed = total[1:] > TOP_P
    probabilities[order[1:][removed]] = 0.0
    return probabilities / probabilities.sum()


def changes(probabilities):
    """How many pairs two runs would label differently, on average."""
    return f"{(1 - (probabilities**2).sum(axis=1)).sum():.1f}"


def figures():
    pairs = pd.read_csv("data/logits.csv", keep_default_na=False)
    top = sum(column.startswith("logit_") for column in pairs.columns)
    logits = pairs[[f"logit_{i}" for i in range(1, top + 1)]].to_numpy(dtype=float)
    model = np.array([warp(values, TEMPERATURE) for values in logits])
    ignored = np.array([warp(values, 1.0) for values in logits])
    dropped = np.array(
        [warp(values, TEMPERATURE, crossing_kept=False) for values in logits]
    )
    both = (model > 0).sum(axis=1) == 2
    # The model keeps one or two tokens for each pair, at either temperature, and the
    # assistant's code one.
    assert (model > 0).sum(axis=1).max() == 2 and (ignored > 0).sum(axis=1).max() == 2
    assert ((dropped > 0).sum(axis=1) == 1).all()
    second = np.sort(model[both], axis=1)[:, -2]
    # Every pair drawing with the generator's first number takes the first token
    # whose running total passes it; the file lists each pair's tokens from the
    # likeliest down.
    u = np.random.default_rng(SEED).random()
    drawn = (np.cumsum(model, axis=1) > u).argmax(axis=1)
    return {
        "two": str(both.sum()),
        "t_two": str(((ignored > 0).sum(axis=1) >= 2).sum()),
        "changes": changes(model),
        "t_changes": changes(ignored),
        "second_mean": f"{100 * second.mean():.1f}%",
        "second_count": f"{second.sum():.1f}",
        "uniform_second": f"{both.sum() / 2:.1f}",
        "u": f"{u:.3f}",
        "always_second": str((drawn[both] != 0).sum()),
    }
