import csv

import pytest
import regex
import tiktoken

from bpe import PATTERN, load_vocabulary, shorten

# The limits the app sends titles at, and the test titles each check takes from each shop.
LIMITS, PER_SHOP = [2, 3, 4, 8, 16, 32], 100


def titles(shop):
    with open("data/titles.csv", encoding="utf-8", newline="") as file:
        rows = csv.DictReader(file)
        found = [
            row["title"] for row in rows if row["shop"] == shop and row["set"] == "test"
        ]
    return found[:PER_SHOP]


@pytest.fixture(scope="module")
def shop():
    ranks = load_vocabulary()
    encoding = tiktoken.Encoding(
        "shop", pat_str=PATTERN, mergeable_ranks=ranks, special_tokens={}
    )
    return ranks, encoding


@pytest.mark.id("tst_amcrfw")
def test_within(shop):
    """Within the limit in all three shops"""
    ranks, encoding = shop
    for name in ["us", "es", "jp"]:
        for title in titles(name):
            for limit in LIMITS:
                short = shorten(title, limit, ranks)
                assert title.startswith(short), title
                assert len(encoding.encode_ordinary(short)) <= limit, title


@pytest.mark.id("tst_9qfq6a")
def test_whole_pieces(shop):
    """As many whole pieces as fit"""
    ranks, encoding = shop
    for name in ["us", "es", "jp"]:
        for title in titles(name):
            pieces = regex.findall(PATTERN, title)
            counts = [len(encoding.encode_ordinary(piece)) for piece in pieces]
            for limit in LIMITS:
                fit = 0
                while fit < len(pieces) and sum(counts[: fit + 1]) <= limit:
                    fit += 1
                if fit:
                    assert shorten(title, limit, ranks) == "".join(pieces[:fit]), title


@pytest.mark.id("tst_6z8knf")
def test_inside_a_piece(shop):
    """The longest start of a first piece that is over the limit"""
    ranks, encoding = shop
    for name in ["us", "es", "jp"]:
        for title in titles(name):
            first = regex.findall(PATTERN, title)[0]
            for limit in LIMITS:
                if len(encoding.encode_ordinary(first)) <= limit:
                    continue
                ends = [
                    end
                    for end in range(len(first), 0, -1)
                    if len(encoding.encode_ordinary(first[:end])) <= limit
                ]
                wanted = first[: ends[0]] if ends else ""
                assert shorten(title, limit, ranks) == wanted, title


@pytest.mark.id("tst_76cth1")
def test_kept_whole(shop):
    """Titles that fit, whole"""
    ranks, encoding = shop
    for name in ["us", "es", "jp"]:
        for title in titles(name):
            tokens = len(encoding.encode_ordinary(title))
            assert shorten(title, tokens, ranks) == title
            assert shorten(title, tokens - 1, ranks) != title
