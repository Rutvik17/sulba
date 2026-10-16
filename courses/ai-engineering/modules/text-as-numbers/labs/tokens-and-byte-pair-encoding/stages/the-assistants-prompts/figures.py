import codecs
import csv

import tiktoken

# GPT-2's pattern, as in bpe.py, and the separator, as in prompts.py.
PATTERN = (
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)
SEPARATOR = "<|endoftext|>"
# The limits the production check packs US titles into, and how many titles it packs.
LIMITS, PACKED = range(1, 1201), 40


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def pack(titles, limit, encoding, separators_counted):
    """The prompt's tokens as pack gives them, with or without each separator counted."""
    separator = encoding.encode(SEPARATOR, allowed_special={SEPARATOR})
    extra = len(separator) if separators_counted else 0
    tokens, used = [], 0
    for title in titles:
        title_tokens = encoding.encode_ordinary(title)
        if used + len(title_tokens) + extra > limit:
            break
        tokens += title_tokens + separator
        used += len(title_tokens) + extra
    return tokens


def streamed(tokens, encoding):
    """The last text an incremental decoder shows as the tokens arrive."""
    reader = codecs.getincrementaldecoder("utf-8")(errors="replace")
    return "".join(reader.decode(encoding.decode_single_token_bytes(t)) for t in tokens)


def figures():
    vocabulary = read("data/vocabulary.csv")
    ranks = {bytes.fromhex(row["token"]): int(row["rank"]) for row in vocabulary}
    encoding = tiktoken.Encoding(
        "shop",
        pat_str=PATTERN,
        mergeable_ranks=ranks,
        special_tokens={SEPARATOR: len(ranks)},
    )
    rows = [row for row in read("data/titles.csv") if row["set"] == "test"]
    shops = {
        s: [row["title"] for row in rows if row["shop"] == s] for s in ["us", "jp"]
    }
    values = {}
    for shop, titles in shops.items():
        guessed = sum(round(len(title) / 4) for title in titles) / len(titles)
        tokens = sum(len(encoding.encode_ordinary(title)) for title in titles)
        values[f"{shop}_guess"] = f"{guessed:.1f}"
        values[f"{shop}_tokens"] = f"{tokens / len(titles):.1f}"
    values["jp_under"] = f"{float(values['jp_tokens']) / float(values['jp_guess']):.1f}"
    us = shops["us"][:PACKED]
    past = [len(pack(us, limit, encoding, False)) - limit for limit in LIMITS]
    assert all(len(pack(us, limit, encoding, True)) <= limit for limit in LIMITS)
    values["packed"] = str(PACKED)
    values["limits"] = f"{len(LIMITS):,}"
    values["over"] = str(sum(tokens > 0 for tokens in past))
    values["most_over"] = str(max(past))
    broken = 0
    for title in shops["jp"]:
        tokens = encoding.encode_ordinary(title)
        alone = "".join(encoding.decode([token]) for token in tokens)
        broken += alone != title
        assert streamed(tokens, encoding) == title
    values["japanese"] = str(len(shops["jp"]))
    values["broken"] = str(broken)
    return values
