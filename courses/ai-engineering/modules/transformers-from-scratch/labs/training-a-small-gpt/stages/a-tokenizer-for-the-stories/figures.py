from collections import Counter, defaultdict

import regex

PATTERN = regex.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
END = "<|endoftext|>"
FILE = "data/TinyStoriesV2-GPT4-valid.txt"
# The lab's vocabulary, the sizes it's compared with, and the width of the app's model, whose
# token embedding holds a row of that many numbers for each token. And GPT-2's vocabulary, from
# its configuration.
SIZE, SIZES, WIDTH = 2048, (512, 1024, 2048, 4096), 128
GPT2_VOCAB = 50257


def train(texts, size):
    """The merges, as the stage's solution learns them, with two counts of the work: the pairs a
    count of every pair again for each merge reads, and the pairs keeping the counts touches."""
    counts = Counter(piece for text in texts for piece in PATTERN.findall(text))
    words = [list(piece.encode()) for piece in counts]
    weights = list(counts.values())
    pairs, where = Counter(), defaultdict(set)
    for index, word in enumerate(words):
        for pair in zip(word, word[1:]):
            pairs[pair] += weights[index]
            where[pair].add(index)
    total = sum(len(word) - 1 for word in words)
    merges, recounted, touched = [], 0, 0
    while 256 + len(merges) < size - 1 and pairs:
        recounted += total
        best = min(pairs, key=lambda pair: (-pairs[pair], pair))
        new = 256 + len(merges)
        merges.append(best)
        for index in where.pop(best):
            word, weight = words[index], weights[index]
            for pair in zip(word, word[1:]):
                pairs[pair] -= weight
                if not pairs[pair]:
                    del pairs[pair]
            merged, at = [], 0
            while at < len(word):
                if at + 1 < len(word) and (word[at], word[at + 1]) == best:
                    merged.append(new)
                    at += 2
                else:
                    merged.append(word[at])
                    at += 1
            touched += len(word) - 1 + len(merged) - 1
            total += len(merged) - len(word)
            words[index] = merged
            for pair in zip(merged, merged[1:]):
                pairs[pair] += weight
                where[pair].add(index)
    return merges, recounted, touched


def encode(text, merges):
    ranks = {pair: rank for rank, pair in enumerate(merges)}
    known, tokens = {}, []
    for at, part in enumerate(text.split(END)):
        if at:
            tokens.append(256 + len(merges))
        for piece in PATTERN.findall(part):
            if piece not in known:
                word = list(piece.encode())
                while len(word) > 1:
                    rank, place = min(
                        (ranks.get(pair, len(ranks)), place)
                        for place, pair in enumerate(zip(word, word[1:]))
                    )
                    if rank == len(ranks):
                        break
                    word[place : place + 2] = [256 + rank]
                known[piece] = word
            tokens.extend(known[piece])
    return tokens


def figures():
    with open(FILE, encoding="utf-8") as file:
        raw = file.read()
    told = [story.strip() for story in raw.split(END)[1:] if story.strip()]
    text = END.join(told) + END
    data = len(text.encode())
    pieces = Counter(piece for story in told for piece in PATTERN.findall(story))
    found = {}
    for size in SIZES:
        merges, recounted, touched = train(told, size)
        assert len(merges) == size - 257
        tokens = encode(text, merges)
        found[f"vocab_{size}"] = f"{size:,}"
        found[f"bytes_{size}"] = f"{data / len(tokens):.2f}"
        found[f"embedding_{size}"] = f"{size * WIDTH:,}"
        if size == SIZE:
            found |= {
                "tokens": f"{len(tokens):,}",
                "per_story": f"{len(tokens) / len(told):.0f}",
                "recounted": f"{recounted:,}",
                "touched": f"{touched:,}",
                "fewer": f"{recounted / touched:.0f}",
            }
    first = raw.split(END)[0]
    return found | {
        "stories": f"{len(told):,}",
        "file_bytes": f"{len(raw.encode()):,}",
        "text_bytes": f"{data:,}",
        "opening": " ".join(first.split()[:6]),
        "pieces": f"{sum(pieces.values()):,}",
        "distinct": f"{len(pieces):,}",
        "size": f"{SIZE:,}",
        "merges": f"{SIZE - 257:,}",
        "end": f"{SIZE - 1:,}",
        "width": str(WIDTH),
        "gpt2": f"{GPT2_VOCAB:,}",
    }
