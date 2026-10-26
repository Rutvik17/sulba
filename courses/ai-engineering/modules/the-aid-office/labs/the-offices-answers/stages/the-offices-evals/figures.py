import csv
import math
import re
from statistics import NormalDist


def read(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


RELEASES = {"five": 5, "three": 3}
CONFIDENCE = 0.95


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


def recorded():
    """Each release's outcome for each question, the questions' pages, the pages each was
    shown, and the replies by question and release."""
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
    return found, questions, given, replies


def change(baseline, candidate, pages, name):
    differences = [
        (after == name) - (before == name)
        for before, after in zip(baseline, candidate, strict=True)
    ]
    mean = sum(differences) / len(differences)
    sums = {}
    for page, difference in zip(pages, differences, strict=True):
        sums[page] = sums.get(page, 0.0) + difference - mean
    groups = len(sums)
    error = math.sqrt(groups / (groups - 1) * sum(total**2 for total in sums.values()))
    z = NormalDist().inv_cdf((1 + CONFIDENCE) / 2)
    return mean, z * error / len(differences)


def percent(count, total):
    return f"{count / total:.0%}"


def figures():
    found, questions, given, replies = recorded()
    pages = [row["page"] for row in questions]
    total = len(questions)
    prompts = {
        release: sum(
            int(replies[row["question"], release]["prompt_tokens"]) for row in questions
        )
        / total
        for release in RELEASES
    }
    hedged = []
    for row in questions:
        reply = replies[row["question"], "five"]["reply"]
        pages_cited = cited(reply, given[row["question"]])
        if pages_cited and "i don't know" in reply.lower():
            hedged.append(row["page"] not in pages_cited)
    out = {
        "questions": str(total),
        "pages": str(len(set(pages))),
        "confidence": f"{CONFIDENCE:.0%}",
        "prompt_five": f"{prompts['five']:,.0f}",
        "prompt_three": f"{prompts['three']:,.0f}",
        "saved": f"{1 - prompts['three'] / prompts['five']:.0%}",
        "hedged": str(len(hedged)),
        "hedged_wrong": str(sum(hedged)),
    }
    for release, shown in RELEASES.items():
        seen = sum(row["page"] in given[row["question"]][:shown] for row in questions)
        out[f"shown_{release}"] = percent(seen, total)
        for name in ("right", "wrong", "staff"):
            out[f"{name}_{release}"] = percent(found[release].count(name), total)
    for name in ("right", "wrong"):
        mean, margin = change(found["five"], found["three"], pages, name)
        out[f"{name}_change"] = f"{mean * 100:+.1f}"
        out[f"{name}_margin"] = f"{margin * 100:.1f}"
    return out
