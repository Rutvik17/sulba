import csv

# The numbers in each of nomic-embed-text-v1.5's vectors.
DIMENSIONS = 768


def figures():
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = list(csv.DictReader(file))
    return {
        "passages": f"{len(passages):,}",
        "dimensions": str(DIMENSIONS),
        # pgvector's documentation: "Each vector takes 4 * dimensions + 8 bytes of
        # storage."
        "bytes": f"{4 * DIMENSIONS + 8:,}",
        # Postgres's documentation: "The TOAST management code is triggered only when a
        # row value to be stored in a table is wider than TOAST_TUPLE_THRESHOLD bytes
        # (normally 2 kB)."
        "toast": "2 kB",
    }
