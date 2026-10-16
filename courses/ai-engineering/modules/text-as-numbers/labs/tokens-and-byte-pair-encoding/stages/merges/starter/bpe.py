"""The shop's tokenizer: a byte-pair encoding learnt from its product titles."""

from collections import Counter

import regex

# GPT-2's pattern, which splits text into the pieces a byte-pair encoding merges within: a
# word with the space before it, a number, a run of punctuation marks, or spaces.
PATTERN = (
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)


def train(texts, merges):
    """The rank of each of the 256 bytes and of each token made by merges merges, learnt from
    texts."""
    raise NotImplementedError
