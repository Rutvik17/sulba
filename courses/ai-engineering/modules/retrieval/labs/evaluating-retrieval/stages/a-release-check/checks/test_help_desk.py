import csv
import math
from collections import defaultdict

import numpy as np
import pytest

from release import check

REPEATS = 10_000


@pytest.fixture(scope="module")
def desk():
    """The searches' runs, and the test questions' judgments, services and first passages."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        texts = {row["passage"]: row["text"] for row in csv.DictReader(file)}
    first_of = {}
    for passage, text in texts.items():
        first_of.setdefault(text, passage)
    first = {passage: first_of[text] for passage, text in texts.items()}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        tests = [row for row in csv.DictReader(file) if row["set"] == "test"]
    judgments = {row["question"]: set() for row in tests}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in judgments:
                judgments[row["question"]].add(row["passage"])
    runs = defaultdict(dict)
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            runs[row["search"]].setdefault(row["question"], []).append(row["passage"])
    services = {row["question"]: row["domain"] for row in tests}
    return runs, judgments, first, services


def seen(shown, first):
    out, before = [], set()
    for passage in shown:
        out.append(None if first[passage] in before else first[passage])
        before.add(first[passage])
    return out


def hits(run, judgments, first):
    """Each judged question's hit rate at 5, as a reader sees the passages."""
    found = []
    for question, relevant in judgments.items():
        texts = {first[passage] for passage in relevant}
        found.append(
            float(not texts.isdisjoint(seen(run.get(question, [])[:5], first)))
        )
    return np.array(found)


def ndcgs(run, judgments, first):
    """Each judged question's nDCG at 10, as a reader sees the passages."""
    found = []
    for question, relevant in judgments.items():
        texts = {first[passage] for passage in relevant}
        shown = seen(run.get(question, []), first)[:10]
        dcg = sum(
            1 / math.log2(rank + 2) for rank, text in enumerate(shown) if text in texts
        )
        best = sum(1 / math.log2(rank + 2) for rank in range(min(10, len(texts))))
        found.append(dcg / best)
    return np.array(found)


def p_value(a, b, seed):
    signs = 1 - 2 * np.random.default_rng(seed).integers(0, 2, size=(REPEATS, len(a)))
    count = np.count_nonzero(np.abs(signs @ (a - b)) >= abs((a - b).sum()))
    return (1 + count) / (1 + REPEATS)


@pytest.mark.id("tst_agscc1")
def test_ships(desk):
    """The reranked search ships over the fused ranking, each text once"""
    runs, judgments, first, services = desk
    found = check(
        runs["fused-once"],
        runs["reranked"],
        judgments,
        first,
        services,
        np.random.default_rng(1),
    )
    now, new = (
        hits(runs["fused-once"], judgments, first),
        hits(runs["reranked"], judgments, first),
    )
    assert found.hit_rate == pytest.approx((now.mean(), new.mean()), abs=1e-12)
    assert found.ship and found.held == []


@pytest.mark.id("tst_f5srw2")
def test_nothing_shown(desk):
    """A search that shows nothing for some questions counts them, and doesn't ship"""
    runs, judgments, first, services = desk
    found = check(
        runs["reranked"],
        runs["confident"],
        judgments,
        first,
        services,
        np.random.default_rng(2),
    )
    expected = hits(runs["confident"], judgments, first).mean()
    assert found.hit_rate[1] == pytest.approx(expected, abs=1e-12)
    assert not found.ship


@pytest.mark.id("tst_zyg58x")
def test_could_be_chance(desk):
    """A gain that chance gives as often as not doesn't ship"""
    runs, judgments, first, services = desk
    found = check(
        runs["reranked-copies"],
        runs["reranked"],
        judgments,
        first,
        services,
        np.random.default_rng(3),
    )
    assert found.hit_rate[1] > found.hit_rate[0]
    assert found.p > 0.05
    assert not found.ship


@pytest.mark.id("tst_5mhgrs")
def test_one_service_worse(desk):
    """A clear gain overall doesn't ship if one service's hit rate falls by more than 0.03"""
    runs, judgments, first, services = desk
    candidate = {}
    for question, relevant in judgments.items():
        if services[question] == "ssa":
            candidate[question] = runs["bm25"][question]
        else:
            candidate[question] = [min(relevant)]
    found = check(
        runs["reranked"],
        candidate,
        judgments,
        first,
        services,
        np.random.default_rng(4),
    )
    assert found.hit_rate[1] > found.hit_rate[0] and found.p < 0.05
    assert found.held == ["ssa"]
    assert not found.ship


@pytest.mark.id("tst_gtkkxc")
def test_ndcg_by_text(desk):
    """Each search's nDCG at 10, a repeated text gaining nothing"""
    runs, judgments, first, services = desk
    found = check(
        runs["reranked"],
        runs["reranked-copies"],
        judgments,
        first,
        services,
        np.random.default_rng(5),
    )
    expected = (
        ndcgs(runs["reranked"], judgments, first).mean(),
        ndcgs(runs["reranked-copies"], judgments, first).mean(),
    )
    assert found.ndcg == pytest.approx(expected, abs=1e-12)


@pytest.mark.id("tst_l6xnsr")
def test_p_value(desk):
    """The p-value from swapping each question's two hit rates where the draws say, and
    each service's hit rates"""
    runs, judgments, first, services = desk
    found = check(
        runs["vectors"],
        runs["fused"],
        judgments,
        first,
        services,
        np.random.default_rng(6),
    )
    now, new = (
        hits(runs["vectors"], judgments, first),
        hits(runs["fused"], judgments, first),
    )
    assert found.p == pytest.approx(p_value(new, now, 6), abs=1e-12)
    questions = list(judgments)
    for service, (was, will) in found.services.items():
        rows = [
            at for at, question in enumerate(questions) if services[question] == service
        ]
        assert (was, will) == pytest.approx(
            (now[rows].mean(), new[rows].mean()), abs=1e-12
        )
    assert sorted(found.services) == sorted(set(services.values()))
