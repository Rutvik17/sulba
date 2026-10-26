import csv
import math
import re
from statistics import NormalDist


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


PEAK = 240
RELEASES = {"five": 5, "three": 3}


def cited(reply, pages):
    found = []
    for number in re.findall(r"\[(\d+)\]", reply):
        place = int(number) - 1
        if 0 <= place < len(pages) and pages[place] not in found:
            found.append(pages[place])
    return found


def outcome(reply, shown, page):
    pages = cited(reply, shown)
    if not pages or "i don't know" in reply.lower():
        return "staff"
    return "right" if page in pages else "wrong"


def figures():
    questions = read("data/questions.csv")
    given = {}
    for row in sorted(read("data/shown.csv"), key=lambda row: int(row["number"])):
        given.setdefault(row["question"], []).append(row["page"])
    replies = {
        (row["question"], row["release"]): row for row in read("data/replies.csv")
    }
    found = {
        release: [
            outcome(
                replies[row["question"], release]["reply"],
                given[row["question"]][:shown],
                row["page"],
            )
            for row in questions
        ]
        for release, shown in RELEASES.items()
    }
    differences = [
        (after == "wrong") - (before == "wrong")
        for before, after in zip(found["five"], found["three"], strict=True)
    ]
    mean = sum(differences) / len(differences)
    sums = {}
    for row, difference in zip(questions, differences, strict=True):
        sums[row["page"]] = sums.get(row["page"], 0.0) + difference - mean
    groups = len(sums)
    error = math.sqrt(groups / (groups - 1) * sum(total**2 for total in sums.values()))
    margin = NormalDist().inv_cdf(0.975) * error / len(differences)
    prompts = {
        release: sum(
            int(replies[row["question"], release]["prompt_tokens"]) for row in questions
        )
        for release in RELEASES
    }
    times = timed()
    hourly = 3600 * len(times["five"][1]) / sum(times["five"][1])
    return {
        "peak": str(PEAK),
        "saved": f"{1 - prompts['three'] / prompts['five']:.0%}",
        "whole_five": f"{percentile(times['five'][1], 0.95):.1f}",
        "whole_three": f"{percentile(times['three'][1], 0.95):.1f}",
        "wrong_change": f"{mean * 100:+.1f}",
        "wrong_margin": f"{margin * 100:.1f}",
        "hourly_five": f"{hourly:,.0f}",
        "busy_five": f"{PEAK / hourly:.0%}",
    }
