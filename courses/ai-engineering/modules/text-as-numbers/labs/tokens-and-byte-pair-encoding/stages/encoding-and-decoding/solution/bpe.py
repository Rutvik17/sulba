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


def load_vocabulary(path="data/vocabulary.csv"):
    """The shop's tokenizer: a dict from each token's bytes to its rank."""
    with open(path, encoding="utf-8") as file:
        rows = file.read().splitlines()[1:]
    return {
        bytes.fromhex(token): int(rank)
        for rank, token in (row.split(",") for row in rows)
    }


def encode(text, ranks):
    """text's tokens, as their ranks."""
    return [
        rank
        for piece in regex.findall(PATTERN, text)
        for rank in encode_piece(piece, ranks)
    ]


def encode_piece(piece, ranks):
    """A piece's tokens: its bytes, with the neighbouring pair whose token has the lowest rank
    merged until no pair makes a token."""
    tokens = [bytes([byte]) for byte in piece.encode()]
    while len(tokens) > 1:
        pairs = [
            (ranks.get(a + b), i) for i, (a, b) in enumerate(zip(tokens, tokens[1:]))
        ]
        known = [pair for pair in pairs if pair[0] is not None]
        if not known:
            break
        _, i = min(known)
        tokens[i : i + 2] = [tokens[i] + tokens[i + 1]]
    return [ranks[token] for token in tokens]


def decode(tokens, ranks):
    """The text the tokens stand for."""
    by_rank = {rank: token for token, rank in ranks.items()}
    return b"".join(by_rank[rank] for rank in tokens).decode(errors="replace")
