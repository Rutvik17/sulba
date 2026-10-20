import csv
import re
from collections import defaultdict
from statistics import mean

BLOCK = re.compile(r"[^\n]+(?:\n(?!\n)[^\n]+)*")
NAMES = {
    "blocks": "blocks",
    "blocks-100": "blocks_100",
    "blocks-200": "blocks_200",
    "words-100": "words_100",
    "words-200": "words_200",
    "words-400": "words_400",
    "words-200-50": "words_200_50",
}


def figures():
    with open("data/pages.csv", encoding="utf-8", newline="") as file:
        pages = {row["page"]: row["text"] for row in csv.DictReader(file)}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        page_of = {
            row["question"]: row["page"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        }
    answers = defaultdict(list)
    with open("data/answers.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in page_of:
                answers[row["question"]].append((int(row["start"]), int(row["end"])))
    chunks = defaultdict(lambda: defaultdict(list))
    with open("data/chunks.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            place = (int(row["start"]), int(row["end"]))
            chunks[row["chunking"]][row["page"]].append(place)
    for page, text in pages.items():
        chunks["blocks"][page] = [match.span() for match in BLOCK.finditer(text)]

    def holding(name):
        """Each validation question's answer, and the chunks that hold part of it."""
        for question, parts in answers.items():
            answer = [at for start, end in parts for at in range(start, end)]
            found = [
                (start, end)
                for start, end in chunks[name][page_of[question]]
                if any(start <= at < end for at in answer)
            ]
            yield answer, found

    def precision(name):
        return mean(
            sum(any(start <= at < end for start, end in found) for at in answer)
            / sum(end - start for start, end in found)
            for answer, found in holding(name)
        )

    def count(name):
        return mean(len(found) for _, found in holding(name))

    lengths = [sum(end - start for start, end in parts) for parts in answers.values()]
    values = {
        "questions": str(len(answers)),
        "answer": f"{mean(lengths):.0f}",
        "plain_chunks": f"{count('words-200'):.2f}",
        "shared_chunks": f"{count('words-200-50'):.2f}",
    }
    for name, key in NAMES.items():
        sizes = [
            end - start for places in chunks[name].values() for start, end in places
        ]
        values[f"{key}_size"] = f"{mean(sizes):,.0f}"
        values[key] = f"{precision(name):.0%}"
    return values
