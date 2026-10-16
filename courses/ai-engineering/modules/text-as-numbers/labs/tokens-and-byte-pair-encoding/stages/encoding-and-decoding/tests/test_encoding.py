import csv

import pytest
import tiktoken

from bpe import PATTERN, decode, encode, load_vocabulary


def titles(shop=None):
    with open("data/titles.csv", encoding="utf-8", newline="") as file:
        rows = csv.DictReader(file)
        return [row["title"] for row in rows if shop is None or row["shop"] == shop]


@pytest.fixture(scope="module")
def shop():
    ranks = load_vocabulary()
    encoding = tiktoken.Encoding(
        "shop", pat_str=PATTERN, mergeable_ranks=ranks, special_tokens={}
    )
    return ranks, encoding


@pytest.mark.id("tst_hhz6k5")
def test_by_hand():
    """Merges the pair of lowest rank first, within each piece"""
    ranks = {bytes([byte]): byte for byte in range(256)}
    ranks |= {b"ll": 256, b"he": 257, b"hell": 258}
    assert encode("hello hello", ranks) == [258, 111, 32, 258, 111]


@pytest.mark.id("tst_3chs1l")
def test_tiktoken(shop):
    """Encodes titles from all three shops as tiktoken does"""
    ranks, encoding = shop
    for title in titles()[::5]:
        assert encode(title, ranks) == encoding.encode_ordinary(title), title


@pytest.mark.id("tst_azu8ku")
def test_every_title(shop):
    """Decodes titles from all three shops back to themselves"""
    ranks, encoding = shop
    for title in titles()[::5]:
        assert decode(encoding.encode_ordinary(title), ranks) == title


@pytest.mark.id("tst_d2rlmk")
def test_part_of_a_character(shop):
    """Reads bytes that end inside a character as U+FFFD, as tiktoken does"""
    ranks, encoding = shop
    for title in titles("jp")[:20]:
        tokens = encoding.encode_ordinary(title)
        for end in range(1, len(tokens)):
            assert decode(tokens[:end], ranks) == encoding.decode(tokens[:end])
