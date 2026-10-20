import csv
import re
from collections import defaultdict

# The tokens of a text the lab's model embeds at once: the context
# `uv run sulba.py model` gives an embedding model (decision record 34).
CONTEXT = 2048
BLOCK = re.compile(r"[^\n]+(?:\n(?!\n)[^\n]+)*")


def figures():
    with open("data/pages.csv", encoding="utf-8", newline="") as file:
        pages = {row["page"]: row["text"] for row in csv.DictReader(file)}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        page_of = {
            row["question"]: row["page"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        }
    with open("data/answers.csv", encoding="utf-8", newline="") as file:
        parts = [
            (page_of[row["question"]], int(row["start"]), int(row["end"]))
            for row in csv.DictReader(file)
            if row["question"] in page_of
        ]
    chunks = defaultdict(lambda: defaultdict(list))
    with open("data/chunks.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            place = (int(row["start"]), int(row["end"]))
            chunks[row["chunking"]][row["page"]].append(place)

    def split(name):
        return sum(
            not any(
                first <= start and end <= last for first, last in chunks[name][page]
            )
            for page, start, end in parts
        )

    words = {page: len(text.split()) for page, text in pages.items()}
    blocks = [
        len(match.group().split())
        for text in pages.values()
        for match in BLOCK.finditer(text)
    ]
    shared = sum(
        len(pages[page][start:end].split())
        for page, places in chunks["words-200-50"].items()
        for start, end in places
    )
    return {
        "pages": str(len(pages)),
        "context": f"{CONTEXT:,}",
        "longest": f"{max(words.values()):,}",
        "parts": str(len(parts)),
        "split_words": str(split("words-100")),
        "split_blocks": str(split("blocks-100")),
        "longest_block": str(max(blocks)),
        "extra": f"{shared / sum(words.values()) - 1:.0%}",
    }
