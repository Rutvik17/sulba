import csv
import math
import statistics
from collections import defaultdict
from statistics import NormalDist

# The office's figures, as mix.py and worth.py give them.
OFFICE = {"question": 3_000, "case": 900, "callback": 700, "new": 400, "vague": 200}
MINUTES = {"question": 7, "case": 6, "callback": 4, "new": 9, "vague": 3}
AGENT = 0.75
HOST = 0.50
SUPPORT = 4_000
PRICE = 40_600


def figures():
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        runs = [row for row in csv.DictReader(file) if row["variant"] == "agent"]
    tasks = defaultdict(lambda: defaultdict(list))
    taken = defaultdict(list)
    for run in runs:
        tasks[run["kind"]][run["task"]].append(run["outcome"] == "done")
        taken[run["kind"]].append(float(run["seconds"]))
    shares = {}
    for kind, each in tasks.items():
        done = [sum(trials) / len(trials) for trials in each.values()]
        shares[kind] = (
            statistics.fmean(done),
            statistics.stdev(done) / math.sqrt(len(done)),
        )
    z = NormalDist().inv_cdf(0.975)
    total = sum(OFFICE.values())
    share = sum(OFFICE[k] / total * shares[k][0] for k in OFFICE)
    error = math.sqrt(sum((OFFICE[k] / total * shares[k][1]) ** 2 for k in OFFICE))
    low, high = share - z * error, share + z * error
    saved = AGENT * sum(OFFICE[k] * MINUTES[k] * shares[k][0] for k in OFFICE)
    spread = AGENT * math.sqrt(
        sum((OFFICE[k] * MINUTES[k] * shares[k][1]) ** 2 for k in OFFICE)
    )
    hours = sum(OFFICE[k] * statistics.fmean(taken[k]) for k in OFFICE) / 3600
    net = saved - hours * HOST - SUPPORT
    net_low = net - z * spread
    months_high = PRICE / net_low
    assert net_low > 0
    return {
        "low": f"{low * 100:.3f}%",
        "low_shown": f"{math.floor(low * 1000) / 10:.1f}%",
        "high": f"{high * 100:.3f}%",
        "high_shown": f"{math.ceil(high * 1000) / 10:.1f}%",
        "months_high": f"{months_high:.3f}",
        "months_high_shown": f"{math.ceil(months_high * 10) / 10:.1f}",
        "vague_tasks": f"{len(tasks['vague'])}",
    }
