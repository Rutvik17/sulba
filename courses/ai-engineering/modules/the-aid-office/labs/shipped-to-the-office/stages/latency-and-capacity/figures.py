import csv
import math


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def timed():
    """Each release's seconds to the first piece and to the whole reply, request by request."""
    times = {}
    for row in read("data/timings.csv"):
        prompt, written = float(row["prompt_ms"]), float(row["predicted_ms"])
        tokens = int(row["predicted_n"])
        first = (prompt + (written / tokens if tokens else 0)) / 1000
        firsts, wholes = times.setdefault(row["release"], ([], []))
        firsts.append(first)
        wholes.append((prompt + written) / 1000)
    return times


def percentile(values, share):
    ordered = sorted(values)
    return ordered[max(math.ceil(share * len(ordered)), 1) - 1]


def figures():
    rows = read("data/timings.csv")
    times = timed()
    out = {
        "requests": str(len(rows)),
        "cached": f"{sum(int(row['cache_n']) for row in rows) / len(rows):,.0f}",
    }
    for release, (firsts, wholes) in times.items():
        hourly = 3600 * len(wholes) / sum(wholes)
        out |= {
            f"first_median_{release}": f"{percentile(firsts, 0.5):.1f}",
            f"first_{release}": f"{percentile(firsts, 0.95):.1f}",
            f"whole_median_{release}": f"{percentile(wholes, 0.5):.1f}",
            f"whole_{release}": f"{percentile(wholes, 0.95):.1f}",
            f"hourly_{release}": f"{hourly:,.0f}",
        }
    return out
