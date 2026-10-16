import csv

import regex
import tiktoken

# GPT-2's pattern, as in bpe.py.
PATTERN = (
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
# The limit the explanation shortens every test title to.
LIMIT = 32


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def shorten(title, limit, count):
    """title cut to fit within limit tokens, as shorten in bpe.py cuts it."""
    pieces = regex.findall(PATTERN, title)
    kept, used = [], 0
    for piece in pieces:
        used += count(piece)
        if used > limit:
            break
        kept.append(piece)
    else:
        return title
    if kept:
        return "".join(kept)
    first = pieces[0]
    for end in range(len(first), 0, -1):
        if count(first[:end]) <= limit:
            return first[:end]
    return ""


def figures():
    vocabulary = read("data/vocabulary.csv")
    ranks = {bytes.fromhex(row["token"]): int(row["rank"]) for row in vocabulary}
    shop = tiktoken.Encoding(
        "shop", pat_str=PATTERN, mergeable_ranks=ranks, special_tokens={}
    )

    def count(text):
        return len(shop.encode_ordinary(text))

    rows = [row for row in read("data/titles.csv") if row["set"] == "test"]
    values = {"limit": str(LIMIT)}
    for name in ["us", "es", "jp"]:
        titles = [row["title"] for row in rows if row["shop"] == name]
        cut = []
        for title in titles:
            short = shorten(title, LIMIT, count)
            assert count(short) <= LIMIT
            if short != title:
                cut.append(len(short) / len(title))
        values[f"{name}_titles"] = str(len(titles))
        values[f"{name}_cut"] = str(len(cut))
        values[f"{name}_kept"] = f"{sum(cut) / len(cut):.0%}"
    japanese = [row["title"] for row in rows if row["shop"] == "jp"]
    over = [t for t in japanese if count(regex.findall(PATTERN, t)[0]) > LIMIT]
    values["jp_inside"] = str(len(over))
    # The first test title whose first piece takes fewer tokens with one more character.
    for row in rows:
        first = regex.findall(PATTERN, row["title"])[0]
        counts = [count(first[:end]) for end in range(1, len(first) + 1)]
        drop = next(
            (i for i in range(1, len(counts)) if counts[i] < counts[i - 1]), None
        )
        if drop is not None:
            values["shorter"] = first[:drop]
            values["shorter_tokens"] = str(counts[drop - 1])
            values["longer"] = first[: drop + 1]
            values["longer_tokens"] = str(counts[drop])
            break
    return values
