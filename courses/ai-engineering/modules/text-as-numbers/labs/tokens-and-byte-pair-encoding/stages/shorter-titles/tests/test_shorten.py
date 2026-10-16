import pytest

from bpe import load_vocabulary, shorten

BYTES = {bytes([byte]): byte for byte in range(256)}


@pytest.mark.id("tst_khluoe")
def test_fits():
    """Keeps a title that fits"""
    title = "Stainless Steel Water Bottle, 32 oz"
    assert shorten(title, 100, load_vocabulary()) == title


@pytest.mark.id("tst_iayf3e")
def test_whole_pieces():
    """Cuts after the last whole piece that fits"""
    assert shorten("ab cd ef", 6, BYTES) == "ab cd"
    assert shorten("ab cd ef", 4, BYTES) == "ab"


@pytest.mark.id("tst_hmd962")
def test_inside_first_piece():
    """Cuts inside a first piece that is over the limit"""
    assert shorten("abcdef gh", 4, BYTES) == "abcd"
    assert shorten("é", 1, BYTES) == ""
