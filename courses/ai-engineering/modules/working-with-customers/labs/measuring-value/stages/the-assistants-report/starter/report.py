"""The desk's value report for the office: the share of its contacts the desk does, what it
saves a month, and the months the pilot takes to pay for itself."""

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from statistics import NormalDist

from mix import OFFICE, Estimate
from worth import AGENT, HOST, MINUTES, PRICE, SUPPORT


@dataclass(frozen=True)
class Report:
    """The share of the contacts done, the net saving a month, and the months to pay back."""

    share: Estimate
    net: Estimate
    months: Estimate


def report(
    runs: list[dict[str, str]],
    variant: str,
    volumes: dict[str, int] = OFFICE,
    minutes: dict[str, float] = MINUTES,
    agent: float = AGENT,
    host: float = HOST,
    support: float = SUPPORT,
    price: float = PRICE,
    confidence: float = 0.95,
) -> Report:
    """The report for the variant's runs, from runs.csv's rows."""
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    trials: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    taken: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        if run["variant"] == variant:
            trials[run["kind"]][run["task"]].append(run["outcome"] == "done")
            taken[run["kind"]].append(float(run["seconds"]))

    # Each kind's share done, and its standard error.
    shares, errors = {}, {}
    for kind, tasks in trials.items():
        each = [sum(done) / len(done) for done in tasks.values()]
        shares[kind] = statistics.fmean(each)
        errors[kind] = math.sqrt(
            shares[kind] * (1 - shares[kind]) / sum(map(len, tasks.values()))
        )

    total = sum(volumes.values())
    share = statistics.fmean(
        d for k in volumes for done in trials[k].values() for d in done
    )
    spread = z * math.sqrt(sum((volumes[k] / total * errors[k]) ** 2 for k in volumes))

    saved = agent * sum(volumes[k] * minutes[k] * shares[k] for k in volumes)
    error = agent * math.sqrt(
        sum((volumes[k] * minutes[k] * errors[k]) ** 2 for k in volumes)
    )
    hours = sum(volumes[k] * statistics.fmean(taken[k]) for k in volumes) / 3600
    net = saved - hours * host

    def months(dollars: float) -> float:
        return price / dollars if dollars > 0 else math.inf

    return Report(
        Estimate(share, max(share - spread, 0.0), min(share + spread, 1.0)),
        Estimate(net, net - z * error, net + z * error),
        Estimate(months(net), months(net - z * error), months(net + z * error)),
    )
