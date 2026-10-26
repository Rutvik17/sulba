import csv
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Timing:
    question: str
    release: str
    first: float
    whole: float


def read(path):
    """Each request's timing in the file at path: its seconds to the first piece of the reply,
    the prompt and one token, and to the whole reply."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    timings = []
    for row in rows:
        prompt, written = float(row["prompt_ms"]), float(row["predicted_ms"])
        tokens = int(row["predicted_n"])
        one = written / tokens if tokens else 0
        timings.append(
            Timing(
                row["question"],
                row["release"],
                (prompt + one) / 1000,
                (prompt + written) / 1000,
            )
        )
    return timings


def percentile(values, share):
    """The smallest of the values that at least share of them are at or below."""
    ordered = sorted(values)
    return ordered[max(math.ceil(share * len(ordered)), 1) - 1]


def per_hour(seconds):
    """How many replies an hour one server writes, one at a time, at the seconds they take."""
    return 3600 * len(seconds) / sum(seconds)


def busy(peak, hourly):
    """The share of each hour the server spends replying at peak questions an hour."""
    return peak / hourly
