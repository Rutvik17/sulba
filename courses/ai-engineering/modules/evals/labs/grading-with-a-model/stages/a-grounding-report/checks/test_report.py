import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest

from grader import template
from grounding import report, risks, to_read
from judge import chosen

CHAT = template(Path("data/tokenizer_config.json"))
TODAY = "October 20, 2026"


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def risk(row):
    return float(row["yes"]) / (float(row["yes"]) + float(row["no"]))


QUESTIONS = {row["question"]: row for row in read("questions.csv")}
GRADES = {row["question"]: risk(row) for row in read("grades.csv")}
THRESHOLD = chosen(
    read("begin.csv"), {row["item"]: risk(row) for row in read("begin-grades.csv")}
)


def clustered(flags, pages, confidence):
    sums = defaultdict(float)
    for page, error in zip(pages, flags - flags.mean(), strict=True):
        sums[page] += error
    groups = len(sums)
    spread = math.sqrt(groups / (groups - 1) * sum(total**2 for total in sums.values()))
    return NormalDist().inv_cdf((1 + confidence) / 2) * spread / len(flags)


def flags(names):
    return np.array([float(GRADES[name] >= THRESHOLD) for name in names])


def reply_in(text):
    """The reply a grader's prompt asks about."""
    return text.split("\nAssistant Message: ", 1)[1].split("\n<end_of_turn>", 1)[0]


@pytest.mark.id("tst_dicyg9")
def test_passages_shown(model):
    """Grades each reply with the passages the help desk showed, in their order and form"""
    passages = {row["passage"]: row for row in read("passages.csv")}
    ranked = defaultdict(list)
    for row in read("ranked.csv"):
        ranked[row["question"]].append(row["passage"])
    replies = {row["question"]: row["reply"] for row in read("replies.csv")}
    asked = {reply: name for name, reply in replies.items()}
    given = {name: (number % 97 + 1) / 99 for number, name in enumerate(replies)}

    def answer(request):
        found = given[asked[reply_in(request.body["prompt"])]]
        model.says("No", probabilities=[{"Yes": found, "No": 1 - found}])

    model.answers(answer)
    found = risks(model.client(), CHAT, replies, passages, ranked, TODAY)
    assert list(found) == list(replies)
    assert found == pytest.approx(given)
    for request in model.requests:
        name = asked[reply_in(request.body["prompt"])]
        context = "\n\n".join(
            f"[{p}] {passages[p]['title']}\n{passages[p]['text']}"
            for p in ranked[name][:5]
        )
        assert f"Context: {context}\nAssistant Message: " in request.body["prompt"]


@pytest.mark.id("tst_dp3kz4")
def test_pages_together():
    """Counts each page's replies together in each margin"""
    names = list(GRADES)
    lines = report(GRADES, QUESTIONS, THRESHOLD, 0.95)
    pages = [QUESTIONS[name]["page"] for name in names]
    assert lines["all"].flagged == pytest.approx(flags(names).mean())
    assert lines["all"].margin == pytest.approx(clustered(flags(names), pages, 0.95))
    assert lines["all"].replies == len(names)


@pytest.mark.id("tst_sg94j8")
def test_services_alone():
    """Gives each service the share and margin of its own replies"""
    lines = report(GRADES, QUESTIONS, THRESHOLD, 0.9)
    services = sorted({row["domain"] for row in QUESTIONS.values()})
    assert list(lines) == ["all", *services]
    for service in services:
        theirs = [name for name in GRADES if QUESTIONS[name]["domain"] == service]
        pages = [QUESTIONS[name]["page"] for name in theirs]
        assert lines[service].flagged == pytest.approx(flags(theirs).mean())
        assert lines[service].margin == pytest.approx(
            clustered(flags(theirs), pages, 0.9)
        )
        assert lines[service].replies == len(theirs)


@pytest.mark.id("tst_s6bxun")
def test_likeliest_first():
    """Lists every reply the grader flags, the highest risk first"""
    found = to_read(GRADES, THRESHOLD)
    flagged = [name for name in GRADES if GRADES[name] >= THRESHOLD]
    assert sorted(found) == sorted(flagged)
    assert found == sorted(flagged, key=lambda name: -GRADES[name])
