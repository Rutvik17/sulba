import csv
import re

import pytest

from chunker import chunks

MOST = 100
# The edit each page gets: a sentence after the first word of its middle block, of those
# that aren't headings.
SENTENCE = " Call the help line for more."
LIMIT = 1.5
# The share of the test questions' answer parts that must lie within one chunk.
WHOLE = 0.99
WORD = re.compile(r"\S+")
BLOCK = re.compile(r"[^\n]+(?:\n(?!\n)[^\n]+)*")


@pytest.fixture(scope="module")
def pages():
    """Each page's text, by page."""
    with open("data/pages.csv", encoding="utf-8", newline="") as file:
        return {row["page"]: row["text"] for row in csv.DictReader(file)}


def edited(text):
    blocks = [
        match for match in BLOCK.finditer(text) if not match.group().startswith("#")
    ]
    block = blocks[len(blocks) // 2]
    at = block.start() + WORD.match(block.group()).end()
    return text[:at] + SENTENCE + text[at:]


@pytest.mark.id("tst_ktwfs5")
def test_every_word(pages):
    """Every word of every page in one chunk, in order"""
    for page, text in pages.items():
        found = chunks(text)
        assert all(a[1] <= b[0] for a, b in zip(found, found[1:])), page
        words = [word for start, end in found for word in text[start:end].split()]
        assert words == text.split(), page


@pytest.mark.id("tst_i7tzvm")
def test_most_words(pages):
    """No chunk of more than 100 words"""
    for page, text in pages.items():
        for start, end in chunks(text):
            assert len(text[start:end].split()) <= MOST, page


@pytest.mark.id("tst_nyxzr7")
def test_cuts(pages):
    """Cut only between blocks, but in a block of more than 100 words"""
    for page, text in pages.items():
        blocks = [
            (match.start(), match.end(), len(match.group().split()))
            for match in BLOCK.finditer(text)
        ]
        starts = {start for start, _, _ in blocks}
        for start, end in chunks(text):
            assert start in starts or any(
                first < start < last and size > MOST for first, last, size in blocks
            ), (page, start)
            before = text[start - 1] if start else " "
            after = text[end] if end < len(text) else " "
            assert before.isspace() and not text[start].isspace(), (page, start)
            assert after.isspace() and not text[end - 1].isspace(), (page, end)


@pytest.mark.id("tst_j0le40")
def test_answers(pages, record_property):
    """The test questions' answers kept whole"""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        page_of = {
            row["question"]: row["page"]
            for row in csv.DictReader(file)
            if row["set"] == "test"
        }
    with open("data/answers.csv", encoding="utf-8", newline="") as file:
        parts = [
            (page_of[row["question"]], int(row["start"]), int(row["end"]))
            for row in csv.DictReader(file)
            if row["question"] in page_of
        ]
    cut = {page: chunks(text) for page, text in pages.items()}
    whole = sum(
        any(first <= start and end <= last for first, last in cut[page])
        for page, start, end in parts
    )
    record_property("note", f"{whole} of {len(parts)} parts within one chunk")
    assert whole >= WHOLE * len(parts)


@pytest.mark.id("tst_xzitvl")
def test_edits(pages, record_property):
    """An edit sends few chunks to be embedded again"""
    again = 0
    for text in pages.values():
        before = {text[start:end] for start, end in chunks(text)}
        after = edited(text)
        again += sum(after[start:end] not in before for start, end in chunks(after))
    record_property("note", f"{again / len(pages):.2f} chunks a page embedded again")
    assert again <= LIMIT * len(pages)


@pytest.mark.id("tst_b153ui")
def test_windows_and_spaces(pages):
    """The same chunks for a page saved on Windows, or with spaces on its blank lines"""
    for page, text in pages.items():
        expected = [text[start:end] for start, end in chunks(text)]
        for saved in (text.replace("\n", "\r\n"), text.replace("\n\n", "\n \t \n")):
            found = [saved[start:end].replace("\r", "") for start, end in chunks(saved)]
            assert [chunk.replace("\n \t \n", "\n\n") for chunk in found] == expected, (
                page
            )
