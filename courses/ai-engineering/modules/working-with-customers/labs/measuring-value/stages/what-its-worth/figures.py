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


def dollars(amount):
    return f"${amount:,.0f}"


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
    minutes = sum(OFFICE[k] * MINUTES[k] * shares[k][0] for k in OFFICE)
    error = AGENT * math.sqrt(
        sum((OFFICE[k] * MINUTES[k] * shares[k][1]) ** 2 for k in OFFICE)
    )
    hours = sum(OFFICE[k] * statistics.fmean(taken[k]) for k in OFFICE) / 3600
    net = minutes * AGENT - hours * HOST - SUPPORT
    z = NormalDist().inv_cdf(0.975)
    low, high = net - z * error, net + z * error
    assert low > 0
    every = sum(OFFICE[k] * MINUTES[k] for k in OFFICE)
    out = {f"{kind}_minutes": f"{count}" for kind, count in MINUTES.items()}
    return out | {
        "agent": f"${AGENT:.2f}",
        "hourly": dollars(AGENT * 60),
        "host": f"${HOST:.2f}",
        "support": dollars(SUPPORT),
        "price": dollars(PRICE),
        "minutes": f"{minutes:,.0f}",
        "every": f"{every:,}",
        "saved": dollars(minutes * AGENT),
        "hours": f"{hours:.1f}",
        "machine": dollars(hours * HOST),
        "net": dollars(net),
        "net_low": dollars(low),
        "net_high": dollars(high),
        "months": f"{PRICE / net:.1f}",
        "months_low": f"{PRICE / high:.1f}",
        "months_high": f"{PRICE / low:.1f}",
    }
