import csv


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        texts = [row["text"] for row in csv.DictReader(file)]
    distinct = len(set(texts))
    return {
        "passages": f"{len(texts):,}",
        "repeated": f"{len(texts) - distinct:,}",
        "distinct": f"{distinct:,}",
    }
