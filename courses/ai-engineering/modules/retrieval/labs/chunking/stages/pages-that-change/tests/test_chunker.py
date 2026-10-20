import pytest

from chunker import chunks


def cut(text, places):
    return [text[start:end] for start, end in places]


@pytest.mark.id("tst_yy5j6f")
def test_chunks():
    """Blocks joined in order, each chunk at its place"""
    text = "Apply online.\n\nOr by phone.\n\n" + " ".join(["word"] * 99)
    assert cut(text, chunks(text)) == [
        "Apply online.\n\nOr by phone.",
        " ".join(["word"] * 99),
    ]


@pytest.mark.id("tst_zcr5uv")
def test_no_words():
    """A page with no words has no chunks"""
    assert chunks("") == []
    assert chunks(" \n\n \n") == []
