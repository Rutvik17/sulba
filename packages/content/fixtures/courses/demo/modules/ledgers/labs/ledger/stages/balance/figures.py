import csv


def figures():
    with open("data/entries.csv", encoding="utf-8") as file:
        amounts = [int(row["amount"]) for row in csv.DictReader(file)]
    return {"entries": str(len(amounts)), "balance": str(sum(amounts))}
