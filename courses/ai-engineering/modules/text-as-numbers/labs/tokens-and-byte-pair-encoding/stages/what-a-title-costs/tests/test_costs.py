import numpy as np
import pandas as pd
import pytest
import tiktoken

from bpe import PATTERN, costs, load_vocabulary


@pytest.fixture(scope="module")
def test_titles():
    titles = pd.read_csv("data/titles.csv")
    return titles[titles["set"] == "test"]


@pytest.fixture(scope="module")
def found(test_titles):
    return costs(test_titles, load_vocabulary())


@pytest.mark.id("tst_5pnhbg")
def test_by_hand():
    """Counts two shops' titles by hand"""
    ranks = {bytes([byte]): byte for byte in range(256)} | {b"ab": 256}
    titles = pd.DataFrame({"shop": ["x", "x", "y"], "title": ["ab", "abc", "é"]})
    by_hand = costs(titles, ranks)
    assert by_hand.loc["x", "characters"] == 5
    assert by_hand.loc["x", "tokens"] == 3
    assert by_hand.loc["y", "characters"] == 1
    assert by_hand.loc["y", "tokens"] == 2
    assert by_hand.loc["x", "per_token"] == pytest.approx(5 / 3)


@pytest.mark.id("tst_eor4kp")
def test_tiktoken(test_titles, found):
    """Counts each shop's test titles as tiktoken does"""
    ranks = load_vocabulary()
    encoding = tiktoken.Encoding(
        "shop", pat_str=PATTERN, mergeable_ranks=ranks, special_tokens={}
    )
    for shop, group in test_titles.groupby("shop"):
        tokens = sum(len(encoding.encode_ordinary(title)) for title in group["title"])
        assert found.loc[shop, "tokens"] == tokens
        assert found.loc[shop, "characters"] == group["title"].str.len().sum()


@pytest.mark.id("tst_crt3d6")
def test_per_token(found):
    """Gives each shop's characters per token"""
    assert sorted(found.index) == ["es", "jp", "us"]
    np.testing.assert_allclose(
        found["per_token"], found["characters"] / found["tokens"], rtol=1e-12
    )
