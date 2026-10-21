import csv
import math
import re
from collections import defaultdict
from statistics import NormalDist

import numpy as np

SAMPLES = 5
MOST = 100
ALPHA = 0.05
SCORES = ["cites_answer", "finished", "brief"]
CANDIDATES = ["rerun", "three-passages", "unranked", "warmer", "planted"]
CITED = re.compile(r"\[(p\d+)\]")


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def releases():
    """Each release's three scores, a row for each question and a column for each sample,
    with the planted regression: the rerun's replies to every fourth question without
    their citations."""
    questions = read("questions.csv")
    names = [q["question"] for q in questions]
    dropped = set(names[::4])
    relevant = defaultdict(set)
    for row in read("relevant.csv"):
        relevant[row["question"]].add(row["passage"])
    rows = read("replies.csv")
    rows += [
        {
            **row,
            "release": "planted",
            "reply": re.sub(r"\s*\[p\d+\]", "", row["reply"])
            if row["question"] in dropped
            else row["reply"],
        }
        for row in rows
        if row["release"] == "rerun"
    ]
    found = defaultdict(dict)
    for row in rows:
        cited = CITED.findall(row["reply"])
        found[row["release"]][row["question"], int(row["sample"])] = {
            "cites_answer": float(any(n in relevant[row["question"]] for n in cited)),
            "finished": float(row["finish"] == "stop"),
            "brief": float(len(row["reply"].split()) <= MOST),
        }
    out = {
        release: {
            score: np.array(
                [[theirs[n, k][score] for k in range(1, SAMPLES + 1)] for n in names]
            )
            for score in SCORES
        }
        for release, theirs in found.items()
    }
    return out, [q["page"] for q in questions], len(dropped)


def clustered(values, pages):
    sums = defaultdict(float)
    for page, residual in zip(pages, values - values.mean(), strict=True):
        sums[page] += residual
    groups = len(sums)
    total = sum(v**2 for v in sums.values())
    return math.sqrt(groups / (groups - 1) * total) / len(values)


def figures():
    scores, pages, dropped = releases()
    level = ALPHA / len(SCORES)
    z = NormalDist().inv_cdf(1 - level)
    out = {
        "alpha": f"{ALPHA:.2f}",
        "scores": str(len(SCORES)),
        "level": f"{level:.4f}",
        "most": str(MOST),
        "samples": str(SAMPLES),
        "dropped": str(dropped),
        "each_alpha": f"{len(SCORES) * ALPHA:.0%}",
    }
    verdicts = {}
    for candidate in CANDIDATES:
        key = candidate.replace("-", "_")
        ships = True
        for score in SCORES:
            base = scores["current"][score].mean(axis=1)
            theirs = scores[candidate][score].mean(axis=1)
            change = (theirs - base).mean()
            high = change + z * clustered(theirs - base, pages)
            low = change - z * clustered(theirs - base, pages)
            out[f"{key}_{score}"] = f"{change:+.3f}"
            out[f"{key}_{score}_interval"] = f"{low:+.3f} to {high:+.3f}"
            verdicts[f"{key}_{score}"] = "ships" if high >= 0 else "stopped"
            ships = ships and high >= 0
        out[f"{key}_verdict"] = "ships" if ships else "stopped"
    assert out["rerun_verdict"] == out["three_passages_verdict"] == "ships"
    assert out["unranked_verdict"] == "ships" and out["unranked_cites_answer"][0] == "-"
    assert verdicts["planted_cites_answer"] == out["planted_verdict"] == "stopped"
    assert verdicts["warmer_finished"] == verdicts["warmer_brief"] == "stopped"
    return out
