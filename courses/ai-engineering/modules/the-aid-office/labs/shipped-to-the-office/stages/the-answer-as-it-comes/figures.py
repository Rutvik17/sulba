import csv


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def figures():
    replies = read("data/replies.csv")
    return {
        "passages": f"{len(read('data/passages.csv')):,}",
        "replies": str(len(replies)),
        "cut": str(sum(row["finish"] == "length" for row in replies)),
    }
