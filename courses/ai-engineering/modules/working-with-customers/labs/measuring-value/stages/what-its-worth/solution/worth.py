"""What the desk is worth to the office each month, and how long the pilot takes to pay for
itself."""

import math
import statistics
from collections import defaultdict
from statistics import NormalDist

from kinds import Share
from mix import OFFICE, Estimate

# The office's figures: an agent's minutes on each kind of contact, and what an agent's minute
# costs it. The desk's machine costs HOST dollars an hour, the team's support SUPPORT dollars a
# month, and the pilot PRICE dollars, as the quote gave it.
MINUTES = {"question": 7, "case": 6, "callback": 4, "new": 9, "vague": 3}
AGENT = 0.75
HOST = 0.50
SUPPORT = 4_000
PRICE = 40_600


def seconds(runs: list[dict[str, str]], variant: str) -> dict[str, float]:
    """Each kind's mean seconds a trial for the variant, from runs.csv's rows."""
    taken: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        if run["variant"] == variant:
            taken[run["kind"]].append(float(run["seconds"]))
    return {kind: statistics.fmean(each) for kind, each in taken.items()}


def monthly(
    shares: dict[str, Share],
    durations: dict[str, float],
    volumes: dict[str, int] = OFFICE,
    minutes: dict[str, float] = MINUTES,
    agent: float = AGENT,
    host: float = HOST,
    support: float = SUPPORT,
    confidence: float = 0.95,
) -> Estimate:
    """The dollars a month the desk saves the office, net of its machine and support, less and
    plus z standard errors."""
    saved = agent * sum(
        count * minutes[kind] * shares[kind].value for kind, count in volumes.items()
    )
    error = agent * math.sqrt(
        sum(
            (count * minutes[kind] * shares[kind].error) ** 2
            for kind, count in volumes.items()
        )
    )
    hours = sum(count * durations[kind] for kind, count in volumes.items()) / 3600
    net = saved - hours * host - support
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    return Estimate(net, net - z * error, net + z * error)


def payback(price: float, net: Estimate) -> Estimate:
    """The months the pilot takes to pay for itself at the net a month given, its ends from the
    net's, and infinity where the net doesn't pay."""

    def months(dollars: float) -> float:
        return price / dollars if dollars > 0 else math.inf

    return Estimate(months(net.value), months(net.high), months(net.low))
