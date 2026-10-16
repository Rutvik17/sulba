import csv
from collections import Counter

import tiktoken

# GPT-2's pattern, as in bpe.py.
PATTERN = (
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def figures():
    vocabulary = read("data/vocabulary.csv")
    ranks = {bytes.fromhex(row["token"]): int(row["rank"]) for row in vocabulary}
    shop = tiktoken.Encoding(
        "shop", pat_str=PATTERN, mergeable_ranks=ranks, special_tokens={}
    )
    japanese = [row["title"] for row in read("data/titles.csv") if row["shop"] == "jp"]
    # Each place a Japanese title's tokens could be cut, and those inside a character, where
    # the bytes before the cut end with part of one.
    cuts = inside = 0
    for title in japanese:
        tokens = shop.encode_ordinary(title)
        for end in range(1, len(tokens)):
            cuts += 1
            inside += shop.decode(tokens[:end]).endswith("\ufffd")
    # The commonest character in the Japanese titles, its bytes and its tokens.
    others = Counter(c for title in japanese for c in title if ord(c) > 127)
    character = others.most_common(1)[0][0]
    data = character.encode()
    return {
        "japanese": f"{len(japanese):,}",
        "cuts": f"{cuts:,}",
        "inside": f"{inside:,}",
        "inside_share": f"{inside / cuts:.0%}",
        "character": character,
        "character_bytes": " ".join(f"{byte:02X}" for byte in data),
        "character_length": str(len(data)),
        "character_tokens": str(len(shop.encode_ordinary(character))),
    }
