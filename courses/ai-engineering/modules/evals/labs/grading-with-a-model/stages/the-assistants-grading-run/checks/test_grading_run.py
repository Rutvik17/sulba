import csv
from collections import defaultdict
from pathlib import Path

import httpx
import numpy as np
import pytest

from agreement import best_threshold
from grader import template
from judge import chosen, graded

CHAT = template(Path("data/tokenizer_config.json"))
TODAY = "October 20, 2026"


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


PASSAGES = {row["passage"]: row for row in read("passages.csv")}
QUESTIONS = read("questions.csv")
RANKED = defaultdict(list)
for row in read("ranked.csv"):
    RANKED[row["question"]].append(row["passage"])


def shown(names):
    """The passages as the help desk shows them."""
    return "\n\n".join(
        f"[{name}] {PASSAGES[name]['title']}\n{PASSAGES[name]['text']}"
        for name in names
    )


def releases():
    """The current release's replies, each with the passages it was shown, leaving out a
    reply that repeats an earlier one."""
    items, seen = [], set()
    for row in read("replies.csv"):
        if row["reply"] not in seen:
            seen.add(row["reply"])
            items.append(
                {"context": shown(RANKED[row["question"]][:5]), "reply": row["reply"]}
            )
    return items


def answering(model, risk):
    """Has the scripted model give each prompt the risk the function gives it."""

    def answer(request):
        found = risk(request.body["prompt"])
        model.says("No", probabilities=[{"Yes": found, "No": 1 - found}])

    model.answers(answer)


@pytest.mark.id("tst_rmi8pq")
def test_each_context(model):
    """Grades people's replies with their own passages and with another service's"""
    relevant = defaultdict(list)
    for row in read("relevant.csv"):
        relevant[row["question"]].append(row["passage"])
    replies = {row["question"]: row["reply"] for row in read("human-replies.csv")}

    def own(question):
        held = relevant[question["question"]]
        return [name for name in held if PASSAGES[name]["page"] == question["page"]]

    items, risks = [], {}
    for index, question in enumerate(QUESTIONS[:20]):
        partner = QUESTIONS[index + len(QUESTIONS) // 2]
        assert partner["domain"] != question["domain"]
        for names, found in ((own(question), 0.1), (own(partner), 0.9)):
            context = shown(names)
            items.append({"context": context, "reply": replies[question["question"]]})
            risks[context[:100]] = found
    answering(model, lambda text: risks[text.split("Context: ", 1)[1][:100]])
    expected = [risks[item["context"][:100]] for item in items]
    assert graded(model.client(), CHAT, items, TODAY) == pytest.approx(expected)


@pytest.mark.id("tst_qfxiwv")
def test_refused(model):
    """Stops when the server refuses a request, rather than count the reply as grounded"""
    model.says("No", probabilities=[{"Yes": 0.2, "No": 0.8}])
    model.says("No", probabilities=[{"Yes": 0.3, "No": 0.7}])
    model.fails(503, "Loading model")
    with pytest.raises(httpx.HTTPStatusError):
        graded(model.client(), CHAT, releases()[:3], TODAY)


@pytest.mark.id("tst_ibont3")
def test_whole_context(model):
    """Shows the grader every passage the help desk showed with each reply"""
    items = releases()
    answering(model, lambda text: 0.2)
    graded(model.client(), CHAT, items, TODAY)
    prompts = [request.body["prompt"] for request in model.requests]
    assert len(prompts) == len(items)
    for item, text in zip(items, prompts, strict=True):
        assert (
            f"Context: {item['context']}\nAssistant Message: {item['reply']}\n" in text
        )


@pytest.mark.id("tst_orkpio")
def test_threshold_on_development():
    """Chooses the threshold on BEGIN's development set, never its test set"""
    begin = read("begin.csv")
    grades = {row["item"]: row for row in read("begin-grades.csv")}
    risks = {
        name: float(row["yes"]) / (float(row["yes"]) + float(row["no"]))
        for name, row in grades.items()
    }
    rows = [row for row in begin if row["set"] == "dev"]
    labels = np.array([row["label"] != "Fully attributable" for row in rows], dtype=int)
    scores = np.array([risks[row["item"]] for row in rows])
    assert chosen(begin, risks) == best_threshold(labels, scores)
