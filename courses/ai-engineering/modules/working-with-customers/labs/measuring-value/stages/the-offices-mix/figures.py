import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

# The office's chat contacts a month, as mix.py gives them.
OFFICE = {"question": 3_000, "case": 900, "callback": 700, "new": 400, "vague": 200}


def figures():
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = [row for row in csv.DictReader(file) if row["variant"] == "agent"]
    tasks = defaultdict(lambda: defaultdict(list))
    for run in runs:
        tasks[run["kind"]][run["task"]].append(run["outcome"] == "done")
    shares = {}
    for kind, each in tasks.items():
        done = [sum(trials) / len(trials) for trials in each.values()]
        error = statistics.stdev(done) / math.sqrt(len(done))
        shares[kind] = (statistics.fmean(done), error, len(done))
    z = NormalDist().inv_cdf(0.975)

    def weighted(volumes):
        total = sum(volumes.values())
        value = sum(count / total * shares[kind][0] for kind, count in volumes.items())
        error = math.sqrt(
            sum(
                (count / total * shares[kind][1]) ** 2
                for kind, count in volumes.items()
            )
        )
        return value, value - z * error, value + z * error, error

    office = weighted(OFFICE)
    tests = weighted({kind: share[2] for kind, share in shares.items()})
    total = sum(OFFICE.values())
    question = (OFFICE["question"] / total * shares["question"][1]) ** 2
    out = {f"{kind}_contacts": f"{count:,}" for kind, count in OFFICE.items()}
    return out | {
        "contacts": f"{total:,}",
        "questions": f"{OFFICE['question'] / total:.0%}",
        "office": f"{office[0]:.1%}",
        "office_low": f"{office[1]:.1%}",
        "office_high": f"{office[2]:.1%}",
        "tests": f"{tests[0]:.1%}",
        "tests_low": f"{tests[1]:.1%}",
        "tests_high": f"{tests[2]:.1%}",
        "question_part": f"{question / office[3] ** 2:.0%}",
    }
