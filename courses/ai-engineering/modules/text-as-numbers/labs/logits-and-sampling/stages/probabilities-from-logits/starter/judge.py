"""The shop's judge: a small language model's answer to whether a product matches
a search, read from its logits."""

import numpy as np
import pandas as pd

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
    raise NotImplementedError


def softmax(logits):
    """The probabilities softmax gives the logits, along the last axis."""
    raise NotImplementedError


def shares(pairs):
    """Each pair's probability that its answer starts with Yes, with No, or with
    another token, as columns yes, no and other."""
    raise NotImplementedError
