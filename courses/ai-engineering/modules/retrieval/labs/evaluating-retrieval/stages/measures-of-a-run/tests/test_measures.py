import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import pytest

from measures import hit_rate, mean, ndcg, recall, reciprocal_rank

RECORDED = json.loads(Path("references/measures.json").read_text(encoding="utf-8"))
MEASURES = {
    "hit_rate": hit_rate,
    "recall": recall,
    "reciprocal_rank": reciprocal_rank,
    "ndcg": ndcg,
}


@pytest.fixture(scope="module")
def help_desk():
    """Each search's run, each question's relevant passages, and each question's set."""
    runs = defaultdict(dict)
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            runs[row["search"]].setdefault(row["question"], []).append(row["passage"])
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        sets = {row["question"]: row["set"] for row in csv.DictReader(file)}
    judgments = {question: set() for question in sets}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            judgments[row["question"]].add(row["passage"])
    return runs, judgments, sets


@pytest.mark.id("tst_fnnxre")
def test_by_hand():
    """Each measure of one ranking, at each cutoff"""
    shown = ["a", "b", "c", "d"]
    relevant = {"c", "x"}
    assert [hit_rate(shown, relevant, k) for k in (1, 2, 3, 4)] == [0, 0, 1, 1]
    assert [recall(shown, relevant, k) for k in (2, 3)] == [0, 0.5]
    assert [reciprocal_rank(shown, relevant, k) for k in (2, 3)] == [
        0,
        pytest.approx(1 / 3),
    ]
    best = 1 + 1 / math.log2(3)
    assert ndcg(shown, relevant, 3) == pytest.approx(0.5 / best, rel=1e-12)
    assert ndcg(["c", "x"], relevant, 2) == pytest.approx(1)
    assert ndcg(["x", "c"], relevant, 2) == pytest.approx(1)


@pytest.mark.id("tst_og22xc")
def test_fewer_shown():
    """Fewer passages shown than the cutoff, and every relevant one counted"""
    relevant = {"a", "b", "c"}
    assert recall(["a"], relevant, 5) == pytest.approx(1 / 3)
    best = 1 + 1 / math.log2(3) + 1 / math.log2(4)
    assert ndcg(["a"], relevant, 5) == pytest.approx(1 / best, rel=1e-12)
    assert ndcg(["a"], relevant, 1) == 1
    assert hit_rate([], relevant, 5) == reciprocal_rank([], relevant, 5) == 0


@pytest.mark.id("tst_5luuzu")
def test_nothing_relevant():
    """A question with no relevant passage scores 0"""
    for measure in MEASURES.values():
        assert measure(["a", "b"], set(), 5) == 0


@pytest.mark.id("tst_5mj0jo")
def test_every_question():
    """A question the run shows nothing for counts, as 0"""
    run = {"q1": ["a", "b"], "q2": ["c"]}
    judgments = {"q1": {"a"}, "q2": {"d"}, "q3": {"e"}}
    assert mean(hit_rate, run, judgments, 5) == pytest.approx(1 / 3)
    assert mean(reciprocal_rank, run, {"q1": {"b"}}, 5) == pytest.approx(0.5)


@pytest.mark.id("tst_qqufel")
def test_made_up():
    """ranx's measures of 300 made-up questions, at each cutoff, and their means"""
    recorded = RECORDED["made_up"]
    run, judgments = {}, {}
    for case in recorded["questions"]:
        relevant = set(case["relevant"])
        if case["shown"]:
            run[case["question"]] = case["shown"]
        judgments[case["question"]] = relevant
        for name, by_k in case["values"].items():
            for k, value in by_k.items():
                found = MEASURES[name](case["shown"], relevant, int(k))
                assert found == pytest.approx(value, abs=1e-12), (
                    case["question"],
                    name,
                    k,
                )
    for name, by_k in recorded["means"].items():
        for k, value in by_k.items():
            found = mean(MEASURES[name], run, judgments, int(k))
            assert found == pytest.approx(value, abs=1e-12), (name, k)


@pytest.mark.id("tst_06zby9")
def test_searches(help_desk):
    """ranx's measures of the help desk's searches, for every tenth question and on average"""
    runs, judgments, sets = help_desk
    for search, recorded in RECORDED["searches"].items():
        run = runs[search]
        for question, values in recorded["questions"].items():
            for name, by_k in values.items():
                for k, value in by_k.items():
                    found = MEASURES[name](
                        run.get(question, []), judgments[question], int(k)
                    )
                    assert found == pytest.approx(value, abs=1e-12), (
                        search,
                        question,
                        name,
                    )
        for which, means in recorded["means"].items():
            judged = {q: r for q, r in judgments.items() if sets[q] == which}
            for name, by_k in means.items():
                for k, value in by_k.items():
                    found = mean(MEASURES[name], run, judged, int(k))
                    assert found == pytest.approx(value, abs=1e-12), (
                        search,
                        which,
                        name,
                        k,
                    )
