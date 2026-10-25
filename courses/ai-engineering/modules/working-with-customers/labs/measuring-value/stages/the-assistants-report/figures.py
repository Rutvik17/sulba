"""What each of the report's problems would have changed in the office's report: the share
weighted by the test set's trials, each kind's error over its trials, the months' ends swapped,
and the net without the support."""

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
    shares, errors, by_trials = {}, {}, {}
    for kind, each in tasks.items():
        done = [sum(trials) / len(trials) for trials in each.values()]
        shares[kind] = statistics.fmean(done)
        errors[kind] = statistics.stdev(done) / math.sqrt(len(done))
        count = sum(map(len, each.values()))
        by_trials[kind] = math.sqrt(shares[kind] * (1 - shares[kind]) / count)
    total = sum(OFFICE.values())
    share = sum(OFFICE[k] / total * shares[k] for k in OFFICE)
    pooled = statistics.fmean(
        d for k in OFFICE for each in tasks[k].values() for d in each
    )
    z = NormalDist().inv_cdf(0.975)

    def error(of):
        return AGENT * math.sqrt(
            sum((OFFICE[k] * MINUTES[k] * of[k]) ** 2 for k in OFFICE)
        )

    saved = AGENT * sum(OFFICE[k] * MINUTES[k] * shares[k] for k in OFFICE)
    hours = sum(OFFICE[k] * statistics.fmean(taken[k]) for k in OFFICE) / 3600
    unsupported = saved - hours * HOST
    net = unsupported - SUPPORT
    low, high = net - z * error(errors), net + z * error(errors)
    return {
        "questions": f"{OFFICE['question'] / total:.0%}",
        "share": f"{share:.1%}",
        "pooled": f"{pooled:.1%}",
        "net": dollars(net),
        "net_low": dollars(low),
        "net_high": dollars(high),
        "trials_low": dollars(net - z * error(by_trials)),
        "trials_high": dollars(net + z * error(by_trials)),
        "swapped_low": f"{PRICE / low:.1f}",
        "swapped_high": f"{PRICE / high:.1f}",
        "months": f"{PRICE / net:.1f}",
        "support": dollars(SUPPORT),
        "unsupported": dollars(unsupported),
        "unsupported_months": f"{PRICE / unsupported:.1f}",
    }
