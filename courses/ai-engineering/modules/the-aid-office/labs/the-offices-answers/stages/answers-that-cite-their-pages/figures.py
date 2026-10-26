import csv


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def figures():
    return {"passages": f"{len(read('data/passages.csv')):,}"}
