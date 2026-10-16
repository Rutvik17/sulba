"""The shop's judge: a small language model's answer to whether a product matches
a search, read from its logits."""

import numpy as np
import pandas as pd
from scipy.optimize import minimize

# The highest logits each pair keeps, from the highest down, in columns token_1 to
# token_20 and logit_1 to logit_20.
TOP = 20


def load_pairs(path="data/logits.csv"):
    """The pairs, and each one's tokens and logits as arrays, a row for each pair."""
    # keep_default_na=False reads every token as text, None among them.
    pairs = pd.read_csv(path, keep_default_na=False)
    tokens = pairs[[f"token_{i}" for i in range(1, TOP + 1)]].to_numpy()
    logits = pairs[[f"logit_{i}" for i in range(1, TOP + 1)]].to_numpy(dtype=float)
    return pairs, tokens, logits


def log_softmax(logits):
    """The log of each probability softmax gives the logits, along the last axis."""
    logits = np.asarray(logits, dtype=float)
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    return shifted - np.log(np.sum(np.exp(shifted), axis=-1, keepdims=True))


def softmax(logits):
    """The probabilities softmax gives the logits, along the last axis."""
    return np.exp(log_softmax(logits))


def shares(pairs):
    """Each pair's probability that its answer starts with Yes, with No, or with
    another token, as columns yes, no and other."""
    yes = np.exp(pairs["yes"] - pairs["lse"])
    no = np.exp(pairs["no"] - pairs["lse"])
    return pd.DataFrame({"yes": yes, "no": no, "other": 1 - yes - no})


def warp(logits, temperature=1.0, top_k=0, top_p=1.0):
    """The probabilities generation draws the next token from, after temperature,
    top-k and top-p, for one set of logits."""
    scaled = np.asarray(logits, dtype=float) / temperature
    if 0 < top_k < len(scaled):
        scaled[scaled < np.sort(scaled)[-top_k]] = -np.inf
    probabilities = softmax(scaled)
    if top_p < 1:
        order = np.argsort(-probabilities, kind="stable")
        # The probability of the tokens ranked above each one, from the likeliest down.
        above = np.cumsum(probabilities[order]) - probabilities[order]
        probabilities[order[1:][above[1:] >= top_p]] = 0.0
        probabilities /= probabilities.sum()
    return probabilities


def sample(probabilities, rng):
    """The index of a token drawn with these probabilities, as rng.choice draws it."""
    totals = np.cumsum(probabilities)
    return int(np.searchsorted(totals / totals[-1], rng.random(), side="right"))


def answers(tokens, logits, rng, temperature=1.0, top_k=0, top_p=1.0):
    """The first token of each pair's answer, drawn after warp, in order, from rng."""
    return [
        row[sample(warp(values, temperature, top_k, top_p), rng)]
        for row, values in zip(tokens, logits, strict=True)
    ]


def match_probability(pairs, temperature=1.0, shift=0.0):
    """Each pair's probability of an exact match, from its Yes and No logits."""
    yes = pairs["yes"].to_numpy() / temperature + shift
    no = pairs["no"].to_numpy() / temperature
    return softmax(np.column_stack([yes, no]))[:, 0]


def calibrate(pairs):
    """The temperature and shift that give match_probability the least log loss on the
    pairs' labels."""
    margin = (pairs["yes"] - pairs["no"]).to_numpy()
    exact = (pairs["label"] == "E").to_numpy()

    def log_loss(parameters):
        # In the slope, one over the temperature, the log loss is convex.
        slope, shift = parameters
        logs = log_softmax(
            np.column_stack([margin * slope + shift, np.zeros(len(margin))])
        )
        return -np.mean(np.where(exact, logs[:, 0], logs[:, 1]))

    slope, shift = minimize(log_loss, x0=[1.0, 0.0]).x
    return 1 / slope, shift
