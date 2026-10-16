# /// script
# requires-python = "==3.14.2"
# dependencies = [
#   "numpy==2.4.6",
#   "pyarrow==26.0.0",
#   "regex==2026.3.32",
#   "tiktoken==0.12.0",
#   "tokenizers==0.23.3",
#   "torch==2.14.1",
#   "transformers==5.19.0",
# ]
#
# [[tool.uv.index]]
# name = "pytorch-cpu"
# url = "https://download.pytorch.org/whl/cpu"
# explicit = true
#
# [tool.uv.sources]
# torch = { index = "pytorch-cpu" }
# ///
"""Builds the shop files of Text as numbers from Amazon's Shopping Queries Dataset: search
queries from Amazon's shops in the US, Spain and Japan, the products shown for each, and each
product's title.

titles: `titles.csv` holds 3,500 product titles, chosen at random (NumPy's default_rng, seed 0)
among each shop's titles that have no control characters and no space at either end, each title
once: 2,500 from the US shop, 2,000 of them for training a tokenizer (set `train`), and 500 each
from the Spanish and Japanese shops, as the dataset gives them. Its `qwen` column counts each
title's tokens with Qwen2.5's tokenizer. `vocabulary.csv` is the tokenizer learnt from the
training titles: the 256 bytes, then the 1,000 merges a byte-pair encoding makes when it splits
the titles with GPT-2's pattern, as tiktoken's educational trainer learns them. Each token is
in hexadecimal, beside its rank.

verdicts: `logits.csv` holds 1,000 of the dataset's US query and product pairs, chosen at
random among the training pairs of its reduced version (`small_version`), which leaves out the
queries deemed easy, and whose query and title have no control characters and no space at
either end. Each keeps the label people gave it: E, S, C or I, for an exact match, a
substitute, a complement or an irrelevant product. Each pair was put to Qwen2.5-1.5B-Instruct
in its chat template: "Does this product match the shopping query? Answer Yes or No.", then the
query and the title. The file keeps the logits for the first token of its answer, computed in
float32 on the CPU: the log-sum-exp of all of them, those of Yes and No, and the 20 highest,
each beside its token's text. The first 500 pairs are for validation and the rest for testing.

    uv run tools/datasets/shopping_queries.py titles <folder to write in> [<folder of downloads>]
    uv run tools/datasets/shopping_queries.py verdicts <folder to write in> [<folder of downloads>]

The dataset's files come to 1.2 GB, and the model to 3.1 GB. Given a folder of downloads, the
script keeps the dataset's files there for the next run; without one, it downloads them to a
temporary folder.
"""

import csv
import hashlib
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import regex
import torch
from tiktoken._educational import bpe_train
from tokenizers import Tokenizer
from transformers import AutoModelForCausalLM, AutoTokenizer

# The dataset's repository at the commit of 7 October 2024. Its files are in Git LFS.
SOURCE = (
    "https://media.githubusercontent.com/media/amazon-science/esci-data/"
    "7916cdf6ab75a462e77f20ab40428a10923998d5/shopping_queries_dataset/"
)
# Each file as downloaded on 16 October 2026, which its LFS pointer names too. A different
# file stops the build.
FILES = {
    "shopping_queries_dataset_examples.parquet": (
        "4a735b693b4a424a6fc67f5be6e4c811495c488bbf66d02a602d308b2744263a"
    ),
    "shopping_queries_dataset_products.parquet": (
        "25124442d064d64b26f74082d6fa09438d679efc0c183cf28d19064a2b65a265"
    ),
}
# GPT-2's pattern, from tiktoken's r50k_base: the pieces a byte-pair encoding merges within.
PATTERN = r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""
# Qwen2.5's tokenizer, at the revision of 25 September 2024 of its 1.5B instruct model.
QWEN, QWEN_REVISION = "Qwen/Qwen2.5-1.5B-Instruct", "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
SHOPS = {"us": 2500, "es": 500, "jp": 500}
TRAIN, MERGES = 2000, 1000
# The question each pair is put to the model with, the pairs, those for validation, and how
# many of each answer's highest logits are kept.
QUESTION = "Does this product match the shopping query? Answer Yes or No."
PAIRS, VALIDATION, TOP = 1000, 500, 20


def download(name: str, folder: Path) -> Path:
    """The dataset's file, downloaded into folder unless it is already there, and checked."""
    path = folder / name
    if not path.exists():
        with urllib.request.urlopen(SOURCE + name) as response, open(path, "wb") as file:
            while chunk := response.read(1 << 20):
                file.write(chunk)
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        while chunk := file.read(1 << 20):
            digest.update(chunk)
    if digest.hexdigest() != FILES[name]:
        raise SystemExit(f"{name} has changed: sha256 {digest.hexdigest()}.")
    return path


def clean(text: str | None) -> bool:
    """Whether text is there, without control characters or space at either end."""
    return text is not None and text == text.strip() and not regex.search(r"[\x00-\x1f\x7f]", text)


def shop_titles(products: Path) -> dict[str, list[str]]:
    """Each shop's titles, without control characters or space at either end, each once."""
    table = pq.read_table(products, columns=["product_locale", "product_title"])
    titles: dict[str, list[str]] = {shop: [] for shop in SHOPS}
    seen: set[tuple[str, str]] = set()
    shops = table.column("product_locale").to_pylist()
    for shop, title in zip(shops, table.column("product_title").to_pylist(), strict=True):
        if clean(title) and (shop, title) not in seen:
            seen.add((shop, title))
            titles[shop].append(title)
    return titles


def titles(out: Path, downloads: Path) -> None:
    products = download("shopping_queries_dataset_products.parquet", downloads)
    every = shop_titles(products)
    rng = np.random.default_rng(0)
    chosen = {
        shop: [every[shop][i] for i in rng.choice(len(every[shop]), count, replace=False)]
        for shop, count in SHOPS.items()
    }
    training = chosen["us"][:TRAIN]
    qwen = Tokenizer.from_pretrained(QWEN, revision=QWEN_REVISION)
    with open(out / "titles.csv", "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["shop", "set", "title", "qwen"])
        for shop, picked in chosen.items():
            for i, title in enumerate(picked):
                part = "train" if shop == "us" and i < TRAIN else "test"
                tokens = len(qwen.encode(title, add_special_tokens=False).ids)
                writer.writerow([shop, part, title, tokens])
    # The trainer splits its text with the pattern, and no piece holds a newline beside other
    # characters, so joining the titles with newlines trains on each title's pieces alone.
    ranks = bpe_train("\n".join(training), 256 + MERGES, PATTERN, visualise=None)
    with open(out / "vocabulary.csv", "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["rank", "token"])
        for token, rank in sorted(ranks.items(), key=lambda item: item[1]):
            writer.writerow([rank, token.hex()])


def verdicts(out: Path, downloads: Path) -> None:
    examples = pq.read_table(
        download("shopping_queries_dataset_examples.parquet", downloads),
        columns=["query", "product_id", "esci_label"],
        filters=[("product_locale", "=", "us"), ("small_version", "=", 1), ("split", "=", "train")],
    ).to_pylist()
    products = pq.read_table(
        download("shopping_queries_dataset_products.parquet", downloads),
        columns=["product_id", "product_title"],
        filters=[("product_locale", "=", "us")],
    )
    names = products.column("product_id").to_pylist()
    titles = dict(zip(names, products.column("product_title").to_pylist(), strict=True))
    pairs = [
        row for row in examples if clean(row["query"]) and clean(titles.get(row["product_id"]))
    ]
    rng = np.random.default_rng(0)
    chosen = [pairs[i] for i in rng.choice(len(pairs), PAIRS, replace=False)]
    tokenizer = AutoTokenizer.from_pretrained(QWEN, revision=QWEN_REVISION)
    model = AutoModelForCausalLM.from_pretrained(QWEN, revision=QWEN_REVISION, dtype=torch.float32)
    model.eval()
    answers = [tokenizer.convert_tokens_to_ids(word) for word in ("Yes", "No")]
    with open(out / "logits.csv", "w", encoding="utf-8", newline="\n") as file:
        writer = csv.writer(file, lineterminator="\n")
        tokens = [f"token_{i}" for i in range(1, TOP + 1)]
        logits = [f"logit_{i}" for i in range(1, TOP + 1)]
        writer.writerow(["set", "query", "title", "label", "lse", "yes", "no", *tokens, *logits])
        for number, row in enumerate(chosen):
            title = titles[row["product_id"]]
            prompt = f"{QUESTION}\nQuery: {row['query']}\nProduct: {title}"
            ids = tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
            )["input_ids"]
            with torch.no_grad():
                last = model(ids).logits[0, -1].double()
            top = torch.topk(last, TOP)
            writer.writerow(
                [
                    "validation" if number < VALIDATION else "test",
                    row["query"],
                    title,
                    row["esci_label"],
                    f"{float(torch.logsumexp(last, 0)):.4f}",
                    *(f"{float(last[answer]):.4f}" for answer in answers),
                    *(tokenizer.decode([int(i)]) for i in top.indices),
                    *(f"{float(value):.4f}" for value in top.values),
                ]
            )


if __name__ == "__main__":
    lab, out = sys.argv[1], Path(sys.argv[2])
    builders = {"titles": titles, "verdicts": verdicts}
    if len(sys.argv) > 3:
        builders[lab](out, Path(sys.argv[3]))
    else:
        with tempfile.TemporaryDirectory() as downloads:
            builders[lab](out, Path(downloads))
