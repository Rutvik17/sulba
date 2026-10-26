import csv


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


BATCH = 32


def figures():
    passages = read("data/passages.csv")
    return {
        "passages": f"{len(passages):,}",
        "pages": str(len({passage["page"] for passage in passages})),
        "batch": str(BATCH),
        "requests": str(-(-len(passages) // BATCH)),
    }
