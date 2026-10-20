import csv
from collections import defaultdict

import pytest

from splitter import places, split

# The most words a chunk of the help desk's holds.
MOST = 100


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


@pytest.mark.id("tst_0182mi")
def test_places(pages, chunkings):
    """Each chunk at its own place in its page"""
    for name, chunked in chunkings.items():
        if name == "words-200-50":
            continue
        for page, found in chunked.items():
            text = pages[page]
            chunks = [text[start:end] for start, end in found]
            assert places(text, chunks) == found, (name, page)


@pytest.mark.id("tst_muyr17")
def test_most_words(pages):
    """No chunk of more than 100 words"""
    for page, text in pages.items():
        for chunk in split(text, MOST):
            assert len(chunk.split()) <= MOST, page


@pytest.mark.id("tst_2c4lhj")
def test_every_word(pages):
    """Every word of every page in its chunks, in order"""
    for page, text in pages.items():
        words = [word for chunk in split(text, MOST) for word in chunk.split()]
        assert words == text.split(), page


@pytest.mark.id("tst_8vmt7l")
def test_page_text(pages):
    """Every chunk the page's own text"""
    for page, text in pages.items():
        end = 0
        for chunk in split(text, MOST):
            start = text.find(chunk, end)
            assert start >= 0, page
            end = start + len(chunk)
