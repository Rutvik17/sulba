import csv
from collections import defaultdict

import pytest

from chunk import blocks, joined, windows, words


@pytest.fixture(scope="module")
def pages():
    """Each page's text, by page."""
    with open("data/pages.csv", encoding="utf-8", newline="") as file:
        return {row["page"]: row["text"] for row in csv.DictReader(file)}


@pytest.fixture(scope="module")
def chunkings():
    """Each chunking's chunks, by page, in order."""
    found = defaultdict(lambda: defaultdict(list))
    with open("data/chunks.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            place = (int(row["start"]), int(row["end"]))
            found[row["chunking"]][row["page"]].append(place)
    return found


def cut(text, places):
    return [text[start:end] for start, end in places]


@pytest.mark.id("tst_9wfbz5")
def test_words():
    """Each word's place, whatever space comes between"""
    assert words("a  bc\nd\t\te") == [(0, 1), (3, 5), (6, 7), (9, 10)]
    assert words(" \n ") == []


@pytest.mark.id("tst_14eas6")
def test_windows():
    """Windows of words, the last ending at the last word"""
    text = "one two  three\nfour five six seven"
    assert cut(text, windows(text, 3)) == ["one two  three", "four five six", "seven"]
    assert cut(text, windows(text, 3, 1)) == [
        "one two  three",
        "three\nfour five",
        "five six seven",
    ]
    assert cut(text, windows(text, 10)) == [text]
    assert windows("", 3) == []


@pytest.mark.id("tst_1bllba")
def test_overlap():
    """No overlap as long as the window"""
    for size, overlap in ((3, 3), (3, 5), (3, -1), (0, 0)):
        with pytest.raises(ValueError):
            windows("one two three", size, overlap)


@pytest.mark.id("tst_yugrq1")
def test_pages_in_windows(pages, chunkings):
    """Every page in windows of 100, 200 and 400 words, and of 200 sharing 50"""
    for name, size, overlap in (
        ("words-100", 100, 0),
        ("words-200", 200, 0),
        ("words-400", 400, 0),
        ("words-200-50", 200, 50),
    ):
        for page, text in pages.items():
            assert windows(text, size, overlap) == chunkings[name][page], (name, page)


@pytest.mark.id("tst_fv1qt7")
def test_blocks():
    """Each block, its lines together"""
    text = "# Apply\n\nApply online.\nOr by phone.\n\n\n- Sign in."
    assert cut(text, blocks(text)) == [
        "# Apply",
        "Apply online.\nOr by phone.",
        "- Sign in.",
    ]


@pytest.mark.id("tst_y2i97p")
def test_joined():
    """Blocks joined until the next would pass the most words"""
    text = "a b\n\nc d e\n\nf\n\ng h i j k l"
    assert cut(text, joined(text, 5)) == ["a b\n\nc d e", "f", "g h i j k l"]
    assert cut(text, joined(text, 100)) == [text]


@pytest.mark.id("tst_378txb")
def test_pages_joined(pages, chunkings):
    """Every page's blocks joined to 100 and to 200 words"""
    for name, most in (("blocks-100", 100), ("blocks-200", 200)):
        for page, text in pages.items():
            assert joined(text, most) == chunkings[name][page], (name, page)
