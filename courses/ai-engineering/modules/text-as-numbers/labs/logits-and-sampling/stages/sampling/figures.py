import numpy as np
import pandas as pd
from scipy import special

# The model's temperature and top-p, with top-k keeping all the logits the file has,
# and the seed of the generator both runs draw from.
TEMPERATURE, TOP_P, SEED = 0.7, 0.8, 0


def warp(logits):
    """The probabilities at the model's settings."""
    probabilities = special.softmax(np.asarray(logits) / TEMPERATURE)
    order = np.argsort(-probabilities, kind="stable")
    above = np.cumsum(probabilities[order]) - probabilities[order]
    probabilities[order[1:][above[1:] >= TOP_P]] = 0.0
    return probabilities / probabilities.sum()


def figures():
    pairs = pd.read_csv("data/logits.csv", keep_default_na=False)
    top = sum(column.startswith("logit_") for column in pairs.columns)
    logits = pairs[[f"logit_{i}" for i in range(1, top + 1)]].to_numpy(dtype=float)
    probabilities = np.array([warp(values) for values in logits])
    rng = np.random.default_rng(SEED)
    runs = [[rng.choice(top, p=p) for p in probabilities] for _ in range(2)]
    changed = sum(first != second for first, second in zip(*runs, strict=True))
    return {
        "pairs": f"{len(pairs):,}",
        "single": str(((probabilities > 0).sum(axis=1) == 1).sum()),
        "expected": f"{(1 - (probabilities**2).sum(axis=1)).sum():.1f}",
        "seed": str(SEED),
        "changed": str(changed),
    }
