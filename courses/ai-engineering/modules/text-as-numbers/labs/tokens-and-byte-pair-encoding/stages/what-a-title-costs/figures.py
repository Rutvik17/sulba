import pandas as pd
import regex
import tiktoken

# GPT-2's pattern, as in bpe.py.
PATTERN = (
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
)


def seen(titles, known):
    """The share of the titles' pieces that occur in the known pieces."""
    pieces = [piece for title in titles for piece in regex.findall(PATTERN, title)]
    return sum(piece in known for piece in pieces) / len(pieces)


def figures():
    vocabulary = pd.read_csv("data/vocabulary.csv")
    ranks = {
        bytes.fromhex(t): int(r)
        for r, t in zip(vocabulary["rank"], vocabulary["token"])
    }
    shop = tiktoken.Encoding(
        "shop", pat_str=PATTERN, mergeable_ranks=ranks, special_tokens={}
    )
    titles = pd.read_csv("data/titles.csv")
    test = titles[titles["set"] == "test"]
    test = test.assign(
        characters=test["title"].str.len(),
        tokens=[len(shop.encode_ordinary(title)) for title in test["title"]],
    )
    totals = test.groupby("shop")[["characters", "tokens", "qwen"]].sum()
    count = test.groupby("shop").size()
    assert (count == count["us"]).all()
    values = {"per_shop": str(count["us"])}
    for shop_name in ["us", "es", "jp"]:
        row = totals.loc[shop_name]
        values[f"{shop_name}_characters"] = (
            f"{row['characters'] / count[shop_name]:.1f}"
        )
        values[f"{shop_name}_tokens"] = f"{row['tokens'] / count[shop_name]:.1f}"
        values[f"{shop_name}_per"] = f"{row['characters'] / row['tokens']:.2f}"
        values[f"{shop_name}_qwen"] = f"{row['qwen'] / count[shop_name]:.1f}"
        values[f"{shop_name}_qwen_per"] = f"{row['characters'] / row['qwen']:.2f}"
    tokens, characters, qwen = totals["tokens"], totals["characters"], totals["qwen"]
    values["jp_ratio"] = f"{tokens['jp'] / tokens['us']:.1f}"
    values["jp_qwen_ratio"] = f"{qwen['jp'] / qwen['us']:.1f}"
    values["jp_per_character"] = f"{tokens['jp'] / characters['jp']:.1f}"
    known = {
        piece
        for title in titles.loc[titles["set"] == "train", "title"]
        for piece in regex.findall(PATTERN, title)
    }
    by_shop = {name: group["title"] for name, group in test.groupby("shop")}
    values["us_seen"] = f"{seen(by_shop['us'], known):.0%}"
    values["es_seen"] = f"{seen(by_shop['es'], known):.0%}"
    japanese = "".join(by_shop["jp"])
    three = sum(len(character.encode()) == 3 for character in japanese)
    values["jp_three_bytes"] = f"{three / len(japanese):.0%}"
    return values
