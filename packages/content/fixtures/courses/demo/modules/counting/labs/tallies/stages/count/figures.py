import csv


def figures():
    with open("data/votes.csv", encoding="utf-8") as file:
        votes = [row["choice"] for row in csv.DictReader(file)]
    return {"total": str(len(votes)), "yes": str(votes.count("yes"))}
