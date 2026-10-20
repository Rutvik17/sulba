import csv
import re

# The most words a chunk of the help desk's holds.
MOST = 100
WORD = re.compile(r"\S+")


def windows(block, most):
    words = [match.span() for match in WORD.finditer(block)]
    return [
        block[words[first][0] : words[min(first + most, len(words)) - 1][1]]
        for first in range(0, len(words), most)
    ]


def split(text, most, joiner="\n\n", counted=True, last=True):
    """The chunker as it should be, or with one of the assistant's problems: blocks
    joined by another joiner, the joined blocks' words not counted, or the last chunk
    dropped."""
    chunks = []
    current, count = "", 0
    for block in text.split("\n\n"):
        size = len(block.split())
        if current and count + size > most:
            chunks.append(current)
            current, count = "", 0
        if size > most:
            chunks.extend(windows(block, most))
        elif current:
            current += joiner + block
            count += size if counted else 0
        else:
            current, count = block, size
    if current and last:
        chunks.append(current)
    return chunks


def places(text, chunks, onward=True):
    """Each chunk's place, found from where the one before ended, or from the start."""
    found = []
    end = 0
    for chunk in chunks:
        start = text.find(chunk, end if onward else 0)
        end = start + len(chunk)
        found.append((start, end))
    return found


def figures():
    with open("data/pages.csv", encoding="utf-8", newline="") as file:
        pages = {row["page"]: row["text"] for row in csv.DictReader(file)}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        page_of = {row["question"]: row["page"] for row in csv.DictReader(file)}
    with open("data/answers.csv", encoding="utf-8", newline="") as file:
        parts = [
            (row["question"], int(row["start"]), int(row["end"]))
            for row in csv.DictReader(file)
        ]
    chunked = {page: split(text, MOST) for page, text in pages.items()}
    chunks = sum(len(found) for found in chunked.values())

    # The last chunk dropped: the text after the last chunk kept is in no chunk.
    kept_to = {}
    for page, text in pages.items():
        found = places(text, split(text, MOST, last=False))
        kept_to[page] = found[-1][1] if found else 0
    lost = [page for page, text in pages.items() if text[kept_to[page] :].split()]
    lost_words = sum(len(pages[page][kept_to[page] :].split()) for page in lost)
    lost_questions = {
        question for question, _, end in parts if end > kept_to[page_of[question]]
    }

    # The joined blocks' words not counted.
    uncounted = [
        len(chunk.split())
        for text in pages.values()
        for chunk in split(text, MOST, counted=False)
    ]

    # Blocks joined by one newline: a chunk of two or more blocks isn't the page's text.
    joined = sum("\n\n" in chunk for found in chunked.values() for chunk in found)

    # Places found from the start of the page: a chunk takes the place of an earlier
    # copy.
    moved = {
        page: sum(
            a != b
            for a, b in zip(
                places(pages[page], found), places(pages[page], found, onward=False)
            )
        )
        for page, found in chunked.items()
    }
    return {
        "pages": str(len(pages)),
        "chunks": f"{chunks:,}",
        "lost_pages": str(len(lost)),
        "lost_words": f"{lost_words:,}",
        "lost_questions": str(len(lost_questions)),
        "questions": str(len(page_of)),
        "over": f"{sum(size > MOST for size in uncounted):,}",
        "uncounted": f"{len(uncounted):,}",
        "longest": f"{max(uncounted):,}",
        "joined": f"{joined:,}",
        "moved": str(sum(moved.values())),
        "moved_pages": str(sum(count > 0 for count in moved.values())),
    }
