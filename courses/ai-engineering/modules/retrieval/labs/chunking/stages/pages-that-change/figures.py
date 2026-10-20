import csv
import re
from fractions import Fraction

# The most words a chunk holds, and the most chunks an edit may send to be embedded
# again, on average over the pages.
MOST = 100
LIMIT = Fraction(3, 2)
# The share of the test questions' answer parts that must lie within one chunk, and the
# budget of words the chunks of 100 words found the most at.
WHOLE = Fraction(99, 100)
BUDGET = 400
SENTENCE = " Call the help line for more."
WORD = re.compile(r"\S+")
BLOCK = re.compile(r"[^\n]+(?:\n(?!\n)[^\n]+)*")


def edited(text):
    """The page with a sentence put after the first word of its middle block, of those
    that aren't headings."""
    blocks = [
        match for match in BLOCK.finditer(text) if not match.group().startswith("#")
    ]
    at = (
        blocks[len(blocks) // 2].start()
        + WORD.match(blocks[len(blocks) // 2].group()).end()
    )
    return text[:at] + SENTENCE + text[at:]


def windows(text):
    words = [match.span() for match in WORD.finditer(text)]
    return [
        (words[first][0], words[min(first + MOST, len(words)) - 1][1])
        for first in range(0, len(words), MOST)
    ]


def joined(text, headings=False):
    """The blocks joined until another would pass MOST words, a block of more cut into
    windows; with headings, each heading starting a new chunk unless the chunk so far
    holds only headings."""
    found = []
    only = False
    for match in BLOCK.finditer(text):
        start, end = match.span()
        size = len(match.group().split())
        heading = headings and match.group().startswith("#")
        if size > MOST:
            found += [[start + s, start + e, MOST] for s, e in windows(match.group())]
            only = False
        elif found and found[-1][2] + size <= MOST and (only or not heading):
            found[-1][1:] = [end, found[-1][2] + size]
            only = only and heading
        else:
            found.append([start, end, size])
            only = heading
    return [(start, end) for start, end, _ in found]


def figures():
    with open("data/pages.csv", encoding="utf-8", newline="") as file:
        pages = {row["page"]: row["text"] for row in csv.DictReader(file)}
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
    chunkers = {
        "windows": windows,
        "joined": joined,
        "desk": lambda text: joined(text, headings=True),
    }
    values = {
        "pages": str(len(pages)),
        "most": str(MOST),
        "questions": str(len(page_of)),
        "parts": str(len(parts)),
        "limit": f"{LIMIT:.1f}",
        "whole": f"{WHOLE:.0%}",
        "budget": str(BUDGET),
    }
    for name, chunker in chunkers.items():
        again = 0
        for text in pages.values():
            before = {text[start:end] for start, end in chunker(text)}
            after = edited(text)
            again += sum(
                after[start:end] not in before for start, end in chunker(after)
            )
        cut = {page: chunker(text) for page, text in pages.items()}
        whole = sum(
            any(first <= start and end <= last for first, last in cut[page])
            for page, start, end in parts
        )
        values[f"{name}_again"] = f"{again:,}"
        values[f"{name}_per_page"] = f"{Fraction(again, len(pages)):.2f}"
        values[f"{name}_whole"] = str(whole)
    return values
