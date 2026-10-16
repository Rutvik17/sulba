import numpy as np
import pandas as pd
from scipy import special

# Qwen2.5-1.5B-Instruct's generation settings, from generation_config.json at the
# revision of 25 September 2024: temperature, top-k, top-p and the repetition penalty.
TEMPERATURE, TOP_K, TOP_P, PENALTY = 0.7, 20, 0.8, 1.1
# A temperature well above the model's, with top-p at 1.
HOT = 2.0


def warp(logits, temperature, top_p):
    """The probabilities after temperature and top-p, with every one of the logits
    kept by top-k."""
    probabilities = special.softmax(np.asarray(logits) / temperature)
    order = np.argsort(-probabilities, kind="stable")
    above = np.cumsum(probabilities[order]) - probabilities[order]
    probabilities[order[1:][above[1:] >= top_p]] = 0.0
    return probabilities / probabilities.sum()


def figures():
    pairs = pd.read_csv("data/logits.csv", keep_default_na=False)
    top = sum(column.startswith("logit_") for column in pairs.columns)
    assert top == TOP_K
    tokens = pairs[[f"token_{i}" for i in range(1, top + 1)]].to_numpy()
    logits = pairs[[f"logit_{i}" for i in range(1, top + 1)]].to_numpy(dtype=float)
    answers = np.isin(tokens, ["Yes", "No"])
    qwen = np.array([warp(values, TEMPERATURE, TOP_P) for values in logits])
    kept = (qwen > 0).sum(axis=1)
    # At the model's settings, top-p keeps Yes, No or both, and no other token.
    assert not (qwen > 0)[~answers].any() and kept.max() == 2
    second = np.sort(qwen[kept == 2], axis=1)[:, -2]
    hot = np.array([warp(values, HOT, 1.0) for values in logits])
    return {
        "temperature": str(TEMPERATURE),
        "top_k": str(TOP_K),
        "top_p": str(TOP_P),
        "penalty": str(PENALTY),
        "top": str(top),
        "pairs": f"{len(pairs):,}",
        "single": str((kept == 1).sum()),
        "double": str((kept == 2).sum()),
        "second_mean": f"{100 * second.mean():.1f}%",
        "second_max": f"{100 * second.max():.1f}%",
        "hot": str(HOT),
        "hot_other": f"{100 * hot[~answers].sum() / len(pairs):.1f}%",
    }
