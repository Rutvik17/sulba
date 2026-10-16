import csv

import pytest
from tiktoken._educational import bpe_train

from bpe import PATTERN, train


def training_titles():
    with open("data/titles.csv", encoding="utf-8", newline="") as file:
        return [row["title"] for row in csv.DictReader(file) if row["set"] == "train"]


@pytest.mark.id("tst_tf02z8")
def test_by_hand():
    """Merges the commonest pair, and breaks a tie by the pair seen first"""
    ranks = train(["abab ab"], 2)
    assert len(ranks) == 258
    assert ranks[b"ab"] == 256
    assert ranks[b"abab"] == 257


@pytest.mark.id("tst_hhyod4")
def test_bytes_first():
    """Ranks the 256 bytes by their values, and stops when nothing is left to merge"""
    ranks = train(["ab ab"], 5)
    assert [ranks[bytes([byte])] for byte in range(256)] == list(range(256))
    assert len(ranks) == 258
    assert ranks[b" ab"] == 257


@pytest.mark.id("tst_24pcjj")
def test_tiktoken():
    """Learns what tiktoken's trainer learns from 50 titles"""
    titles = training_titles()[:50]
    wanted = bpe_train("\n".join(titles), 256 + 40, PATTERN, visualise=None)
    assert train(titles, 40) == wanted


@pytest.mark.id("tst_3u3qfb")
def test_shop_vocabulary():
    """Learns the shop's first 10 merges from its training titles"""
    with open("data/vocabulary.csv", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    wanted = {bytes.fromhex(row["token"]): int(row["rank"]) for row in rows[: 256 + 10]}
    assert train(training_titles(), 10) == wanted
