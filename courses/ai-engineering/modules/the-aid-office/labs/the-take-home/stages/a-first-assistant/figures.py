import csv
import math
import re
from collections import Counter

WORDS, BEST, BAR = 200, 5, 0.65


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def passages(pages):
    """The pages' passages, as the solution splits them: each page's blocks joined until another
    would take a passage past WORDS words, with the page's name and title."""
    found = []
    for page in pages:
        joined, count = [], 0
        for block in page["text"].split("\n\n"):
            size = len(block.split())
            if joined and count + size > WORDS:
                found.append((page["page"], page["title"] + " " + "\n\n".join(joined)))
                joined, count = [], 0
            joined.append(block)
            count += size
        if joined:
            found.append((page["page"], page["title"] + " " + "\n\n".join(joined)))
    return found


def words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def bm25(found, k1=1.2, b=0.75):
    """A function giving a question's passages' pages, best first, by BM25."""
    counts = [Counter(words(text)) for _, text in found]
    lengths = [sum(each.values()) for each in counts]
    mean = sum(lengths) / len(found)
    held = Counter(word for each in counts for word in each)
    n = len(found)
    idf = {word: math.log(1 + (n - m + 0.5) / (m + 0.5)) for word, m in held.items()}

    def ranked(question):
        query = set(words(question))
        scores = []
        for place, each in enumerate(counts):
            norm = k1 * (1 - b + b * lengths[place] / mean)
            score = sum(
                idf[word] * each[word] * (k1 + 1) / (each[word] + norm)
                for word in query
                if word in each
            )
            if score > 0:
                scores.append((-score, place))
        return [found[place][0] for _, place in sorted(scores)]

    return ranked


def figures():
    pages = read("data/pages.csv")
    questions = read("data/questions.csv")
    found = passages(pages)
    ranked = bm25(found)
    top = first = 0
    for question in questions:
        found_pages = ranked(question["text"])
        top += question["page"] in found_pages[:BEST]
        first += found_pages[:1] == [question["page"]]
    return {
        "pages": str(len(pages)),
        "questions": str(len(questions)),
        "bar": f"{BAR:.0%}",
        "best": str(BEST),
        "found": f"{top / len(questions):.0%}",
        "first": f"{first / len(questions):.0%}",
    }
