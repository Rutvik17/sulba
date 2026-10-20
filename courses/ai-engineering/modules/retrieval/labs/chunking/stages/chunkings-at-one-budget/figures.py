import csv
from collections import defaultdict
from fractions import Fraction

import numpy as np

# The words of the chunks a search hands the model, and a budget twice as large.
BUDGET = 400
LARGER = 800
NAMES = {
    "words-100": "words_100",
    "blocks-100": "blocks_100",
    "words-200": "words_200",
    "words-200-50": "words_200_50",
    "blocks-200": "blocks_200",
    "words-400": "words_400",
}


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


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
    places = defaultdict(dict)
    with open("data/chunks.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            place = (row["page"], int(row["start"]), int(row["end"]))
            places[row["chunking"]][row["chunk"]] = place
    ids, questions = read("data/question-vectors-256.csv")
    asked = [index for index, id_ in enumerate(ids) if id_ in page_of]

    def search(name, budget):
        """Each validation question's recall and IoU, as fractions, and its chunks
        found."""
        chunk_ids, vectors = read(f"data/vectors-{name}.csv")
        found = [places[name][id_] for id_ in chunk_ids]
        words = [len(pages[page][start:end].split()) for page, start, end in found]
        for row in asked:
            order = np.argsort(-(vectors @ questions[row]), kind="stable")
            taken, total = [], 0
            for chunk in order.tolist():
                if total + words[chunk] > budget:
                    break
                taken.append(found[chunk])
                total += words[chunk]
            page = page_of[ids[row]]
            answer = {
                at for start, end in answers[ids[row]] for at in range(start, end)
            }
            held = sum(
                any(p == page and start <= at < end for p, start, end in taken)
                for at in answer
            )
            size = sum(end - start for _, start, end in taken)
            yield (
                Fraction(held, len(answer)),
                Fraction(held, len(answer) + size - held),
                len(taken),
            )

    values = {
        "budget": str(BUDGET),
        "larger": str(LARGER),
        "questions": str(len(asked)),
    }
    for name, key in NAMES.items():
        results = list(search(name, BUDGET))
        count = len(results)
        values[f"{key}_found"] = f"{Fraction(sum(n for *_, n in results), count):.1f}"
        values[f"{key}_recall"] = f"{sum(r for r, *_ in results) / count:.3f}"
        values[f"{key}_iou"] = f"{sum(i for _, i, _ in results) / count:.3f}"
    for name in ("words-100", "blocks-200"):
        results = list(search(name, LARGER))
        recall = sum(r for r, *_ in results) / len(results)
        values[f"{NAMES[name]}_larger"] = f"{recall:.3f}"
    return values
