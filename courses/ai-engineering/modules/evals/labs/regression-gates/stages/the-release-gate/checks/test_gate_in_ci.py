import csv
import re
from collections import defaultdict
import pytest

from gate import gate
from release_gate import check, main, scored


def read(name):
    with open(f"data/{name}", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


QUESTIONS = read("questions.csv")
NAMES = [question["question"] for question in QUESTIONS]
PAGES = [question["page"] for question in QUESTIONS]
RELEVANT = defaultdict(set)
for row in read("relevant.csv"):
    RELEVANT[row["question"]].add(row["passage"])
REPLIES = read("replies.csv")
SAMPLES = [1, 2, 3, 4, 5]


def planted():
    """The rerun's replies, with the citations taken out of the replies to every fourth
    question."""
    dropped = set(NAMES[::4])
    rows = []
    for row in REPLIES:
        if row["release"] == "rerun":
            reply = row["reply"]
            if row["question"] in dropped:
                reply = re.sub(r"\s*\[p\d+\]", "", reply)
            rows.append({**row, "release": "planted", "reply": reply})
    return rows


def written(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(REPLIES[0]))
        writer.writeheader()
        writer.writerows(rows)
    return str(path)


@pytest.mark.id("tst_yaaltg")
def test_planted(tmp_path):
    """Stops a release whose replies to every fourth question cite nothing"""
    path = written(tmp_path / "replies.csv", REPLIES + planted())
    assert main([path, "current", "planted"]) == 1


@pytest.mark.id("tst_9a6pfy")
def test_rerun():
    """Ships a rerun of the current release, either way round"""
    assert main(["data/replies.csv", "current", "rerun"]) == 0
    assert main(["data/replies.csv", "rerun", "current"]) == 0


@pytest.mark.id("tst_6ip836")
def test_warmer():
    """Stops the release whose prompt asks for warm, complete answers"""
    assert main(["data/replies.csv", "current", "warmer"]) == 1


@pytest.mark.id("tst_32bta1")
def test_each_score():
    """Gates each score at alpha over the number of scores"""
    baseline = scored(REPLIES, RELEVANT, NAMES, "current", SAMPLES)
    candidate = scored(REPLIES, RELEVANT, NAMES, "unranked", SAMPLES)
    verdicts = check(baseline, candidate, PAGES, 0.05)
    assert sorted(verdicts) == ["brief", "cites_answer", "finished"]
    for name, verdict in verdicts.items():
        assert verdict == gate(baseline[name], candidate[name], PAGES, 0.05 / 3)


@pytest.mark.id("tst_swkjub")
def test_scores():
    """Scores whether each reply ended by itself and how long it ran"""
    found = scored(REPLIES, RELEVANT, NAMES, "warmer", [2, 4])
    rows = {(row["question"], row["release"], row["sample"]): row for row in REPLIES}
    for index, name in enumerate(NAMES):
        for column, sample in enumerate(("2", "4")):
            row = rows[name, "warmer", sample]
            assert found["finished"][index, column] == float(row["finish"] == "stop")
            words = len(row["reply"].split())
            assert found["brief"][index, column] == float(words <= 100)
