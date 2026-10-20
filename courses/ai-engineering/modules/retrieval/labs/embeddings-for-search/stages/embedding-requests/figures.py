import csv
import math

# The texts a request carries, and the tokens the runner lets an embedding model take
# in one text (sulba.py, decision record 34).
BATCH, LIMIT = 32, 2048


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = sum(1 for _ in csv.DictReader(file))
    return {
        "passages": f"{passages:,}",
        "requests": str(math.ceil(passages / BATCH)),
        "batch": str(BATCH),
        "limit": f"{LIMIT:,}",
    }
