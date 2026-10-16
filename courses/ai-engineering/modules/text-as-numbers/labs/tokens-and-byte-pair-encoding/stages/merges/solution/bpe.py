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
    counts = Counter(piece for text in texts for piece in regex.findall(PATTERN, text))
    pieces = {piece: [bytes([byte]) for byte in piece.encode()] for piece in counts}
    ranks = {bytes([byte]): byte for byte in range(256)}
    for _ in range(merges):
        pairs = Counter()
        for piece, tokens in pieces.items():
            for pair in zip(tokens, tokens[1:]):
                pairs[pair] += counts[piece]
        if not pairs:
            break
        first, second = max(pairs, key=pairs.__getitem__)
        ranks[first + second] = len(ranks)
        for piece, tokens in pieces.items():
            pieces[piece] = merge(tokens, first, second)
    return ranks


def merge(tokens, first, second):
    """tokens with each first followed by second joined into one token, from left to right."""
    joined, i = [], 0
    while i < len(tokens):
        if i + 1 < len(tokens) and tokens[i] == first and tokens[i + 1] == second:
            joined.append(first + second)
            i += 2
        else:
            joined.append(tokens[i])
            i += 1
    return joined
