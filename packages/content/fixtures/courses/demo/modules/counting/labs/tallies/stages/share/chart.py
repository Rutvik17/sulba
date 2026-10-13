import csv

from tally import share


def chart(votes):
    with open("data/votes.csv", encoding="utf-8") as file:
        choices = [row["choice"] for row in csv.DictReader(file)][:votes]
    counted = range(1, votes + 1)
    shares = [share(choices[:n], "yes") for n in counted]
    return {
        "x": {"min": 1, "max": 3, "step": 1, "label": "votes counted"},
        "y": {"min": 0, "max": 1, "step": 0.5, "label": "share"},
        "lines": [
            {"style": "dashed", "label": "Half", "x": [1, 3], "y": [0.5, 0.5]},
            {"style": "main", "label": "Your share", "x": list(counted), "y": shares},
        ],
        "points": [{"x": votes, "y": shares[-1]}],
        "readouts": [
            {"label": f"Share of yes in the first {votes}", "value": f"{shares[-1]:.4f}"},
        ],
        "description": f"Your share of yes votes in the first 1 to {votes} votes of the poll",
    }
