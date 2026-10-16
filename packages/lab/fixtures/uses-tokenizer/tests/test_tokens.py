import pytest
from tokens import encoding, pieces


@pytest.mark.id("tst_regx01")
def test_pieces():
    """Splits text into words, numbers and marks"""
    assert pieces("Mug's 12 oz, café") == ["Mug", "'s", " 12", " oz", ",", " café"]


@pytest.mark.id("tst_tikt01")
def test_encoding():
    """Encodes with the merges given and decodes back"""
    shop = encoding([b"ll", b"he", b"hell"])
    tokens = shop.encode_ordinary("hello")
    assert tokens == [258, ord("o")]
    assert shop.decode(tokens) == "hello"
