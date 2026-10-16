import csv
from collections import Counter

import regex
import tiktoken

# GPT-2's pattern, as in bpe.py.
PATTERN = (
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
# The merges the explanation follows from the start of training.
FIRST = 20


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


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


def named(pair):
    """A pair of tokens in words, such as a space and S."""
    return " and ".join(
        "a space" if token == b" " else token.decode() for token in pair
    )


def figures():
    titles = [row["title"] for row in read("data/titles.csv") if row["set"] == "train"]
    vocabulary = read("data/vocabulary.csv")
    ranks = {bytes.fromhex(row["token"]): int(row["rank"]) for row in vocabulary}
    counts = Counter(
        piece for title in titles for piece in regex.findall(PATTERN, title)
    )
    # The first merges as train makes them, with each pair's count and the pairs tied with it.
    pieces = {piece: [bytes([byte]) for byte in piece.encode()] for piece in counts}
    made = []
    for _ in range(FIRST):
        pairs = Counter()
        for piece, tokens in pieces.items():
            for pair in zip(tokens, tokens[1:]):
                pairs[pair] += counts[piece]
        best = max(pairs, key=pairs.__getitem__)
        tied = [pair for pair, count in pairs.items() if count == pairs[best]]
        made.append((best, pairs[best], tied))
        for piece, tokens in pieces.items():
            pieces[piece] = merge(tokens, *best)
    first = {pair[0] + pair[1]: 256 + i for i, (pair, _, _) in enumerate(made)}
    assert first == {
        token: rank for token, rank in ranks.items() if 256 <= rank < 256 + FIRST
    }
    # The first merge that tied, which the explanation describes: two pairs, the one seen
    # first merged first and the other next.
    at, (pair, count, tied) = next(
        (i, step) for i, step in enumerate(made) if len(step[2]) > 1
    )
    assert len(tied) == 2 and tied[0] == pair and made[at + 1][0] == tied[1]
    shop = tiktoken.Encoding(
        "shop", pat_str=PATTERN, mergeable_ranks=ranks, special_tokens={}
    )
    size = sum(len(title.encode()) for title in titles)
    tokens = sum(len(shop.encode_ordinary(title)) for title in titles)
    longest = sorted(ranks, key=len, reverse=True)[:2]
    assert len(longest[0]) == len(longest[1]) and all(
        t.startswith(b" ") for t in longest
    )
    return {
        "titles": f"{len(titles):,}",
        "merges": f"{len(ranks) - 256:,}",
        "size": f"{len(ranks):,}",
        "pieces": f"{sum(counts.values()):,}",
        "distinct": f"{len(counts):,}",
        "first_merges": ", ".join(named(pair) for pair, _, _ in made[:4]),
        "first_count": f"{made[0][1]:,}",
        "tie_at": ["first", "second", "third", "fourth", "fifth", "sixth"][at],
        "tie_first": named(tied[0]),
        "tie_second": named(tied[1]),
        "tie_count": f"{count:,}",
        "bytes": f"{size:,}",
        "tokens": f"{tokens:,}",
        "per_token": f"{size / tokens:.2f}",
        "longest": " and ".join(token.decode().strip() for token in longest),
        "longest_bytes": str(len(longest[0])),
    }
