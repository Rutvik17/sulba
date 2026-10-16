"""Labels query and product pairs with the judge's answers, drawn as the model draws
them at its own settings."""

import numpy as np

# Qwen2.5-1.5B-Instruct's sampling settings, and the seed that gives every run the
# same labels.
TEMPERATURE, TOP_K, TOP_P = 0.7, 20, 0.8
SEED = 0


def warp(logits, temperature=TEMPERATURE, top_k=TOP_K, top_p=TOP_P):
    """The probabilities the model draws a pair's first token from."""
    logits = np.asarray(logits, dtype=float)
    kept = logits >= np.sort(logits)[-top_k]
    weights = np.where(kept, np.exp(logits - logits.max()), 0.0)
    probabilities = weights / weights.sum()
    probabilities = probabilities / temperature
    probabilities /= probabilities.sum()
    if top_p < 1:
        order = np.argsort(-probabilities)
        total = np.cumsum(probabilities[order])
        probabilities[order[1:][total[1:] > top_p]] = 0.0
        probabilities /= probabilities.sum()
    return probabilities


def sample(probabilities, rng):
    """The index of a token drawn with these probabilities."""
    return int(rng.choice(np.flatnonzero(probabilities)))


def label(tokens, logits, temperature=TEMPERATURE, top_k=TOP_K, top_p=TOP_P):
    """The first token of the judge's answer for each pair."""
    labels = []
    for row, values in zip(tokens, logits, strict=True):
        rng = np.random.default_rng(SEED)
        labels.append(row[sample(warp(values, temperature, top_k, top_p), rng)])
    return labels
