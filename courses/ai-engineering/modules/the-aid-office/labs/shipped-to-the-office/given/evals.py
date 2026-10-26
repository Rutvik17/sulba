from dataclasses import dataclass
from statistics import NormalDist

import numpy as np
from answers import cited

OUTCOMES = ("right", "wrong", "staff")
# Each release by name, with how many of a question's passages it gives the model.
RELEASES = {"five": 5, "three": 3}


@dataclass(frozen=True)
class Change:
    change: float
    margin: float


def outcome(reply, shown, page):
    """How a reply went, shown giving the page of each passage the model was given and page
    the question's own: "staff" when the answer would go to staff, "right" when it cites the
    question's page, and "wrong" when it cites only others."""
    pages = cited(reply, shown)
    if not pages or "i don't know" in reply.lower():
        return "staff"
    return "right" if page in pages else "wrong"


def outcomes(replies, shown, questions, release):
    """Each question's outcome in the release, in the order of questions, from the rows of
    replies.csv, shown.csv and questions.csv."""
    given = {}
    for row in sorted(shown, key=lambda row: int(row["number"])):
        given.setdefault(row["question"], []).append(row["page"])
    reply = {
        row["question"]: row["reply"] for row in replies if row["release"] == release
    }
    return [
        outcome(
            reply[row["question"]],
            given[row["question"]][: RELEASES[release]],
            row["page"],
        )
        for row in questions
    ]


def shares(found):
    """The share of the outcomes that are each of OUTCOMES."""
    return {name: sum(each == name for each in found) / len(found) for name in OUTCOMES}


def change(baseline, candidate, pages, name, confidence):
    """The candidate's share of the outcome name less the baseline's, on the same questions,
    from each question's difference, with its margin at the confidence given, each page's
    questions counted together."""
    differences = np.array(
        [
            (after == name) - (before == name)
            for before, after in zip(baseline, candidate, strict=True)
        ],
        dtype=np.float64,
    )
    sums = {}
    for page, residual in zip(pages, differences - differences.mean(), strict=True):
        sums[page] = sums.get(page, 0.0) + float(residual)
    groups = len(sums)
    error = np.sqrt(groups / (groups - 1) * sum(total**2 for total in sums.values()))
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    return Change(float(differences.mean()), float(z * error / len(differences)))
