import csv

import numpy as np
import pytest

from cache import Cache
from embed import DOCUMENT, QUERY
from index import Index

# The bytes the saved index may take for each passage, ids included, and how many
# passages a question gets.
BUDGET = 300
K = 5
# The share of the test questions the full vectors answer in their first K that the
# index must answer too.
KEPT = 0.98


def vectors(path):
    """A vector file's vectors by id, as the model gave them."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return {row[0]: np.array(row[1:], dtype=np.int64) for row in rows}


@pytest.fixture(scope="module")
def desk():
    """The help desk's passages and test questions, with the vectors
    nomic-embed-text-v1.5 gave them, the passages that answer each question, and the
    full vectors' recall at K."""
    with open("data/passages.csv", encoding="utf-8", newline="") as file:
        passages = {row["passage"]: row["text"] for row in csv.DictReader(file)}
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        questions = {
            row["question"]: row["text"]
            for row in csv.DictReader(file)
            if row["set"] == "test"
        }
    relevant = {question: set() for question in questions}
    with open("data/relevant.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in relevant:
                relevant[row["question"]].add(row["passage"])
    passage_vectors = vectors("data/passage-vectors.csv")
    question_vectors = vectors("data/question-vectors.csv")
    texts = {DOCUMENT + text: passage_vectors[id_] for id_, text in passages.items()}
    texts |= {QUERY + text: question_vectors[id_] for id_, text in questions.items()}
    ids = list(passages)
    stored = np.array([passage_vectors[id_] for id_ in ids])
    asked = np.array([question_vectors[id_] for id_ in questions])
    best = np.argsort(-(asked @ stored.T), axis=1, kind="stable")[:, :K]
    answered = [
        bool({ids[index] for index in row} & answers)
        for row, answers in zip(best, relevant.values())
    ]
    return passages, questions, relevant, texts, sum(answered) / len(answered)


def scripted(model, texts):
    model.embeds(lambda text: (texts[text] / 32767).tolist())


@pytest.mark.id("tst_t8b2ma")
def test_fits(model, tmp_path, desk, record_property):
    """At most 300 bytes a passage"""
    passages, _, _, texts, _ = desk
    scripted(model, texts)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        Index.build(model.client(), cache, passages).save(tmp_path / "index.npz")
    size = (tmp_path / "index.npz").stat().st_size / len(passages)
    record_property("note", f"{size:.0f} bytes a passage")
    assert size <= BUDGET


@pytest.mark.id("tst_k0z6ne")
def test_answers(model, tmp_path, desk, record_property):
    """Finds the answers the full vectors find"""
    passages, questions, relevant, texts, full = desk
    scripted(model, texts)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        index = Index.build(model.client(), cache, passages)
        found = index.find(model.client(), cache, list(questions.values()), k=K)
    answered = [
        bool(set(ids) & answers) for ids, answers in zip(found, relevant.values())
    ]
    recall = sum(answered) / len(answered)
    record_property("note", f"recall at {K}: {recall:.3f}, against {full:.3f} in full")
    assert recall >= KEPT * full


@pytest.mark.id("tst_r1j4wq")
def test_once(model, tmp_path, desk):
    """Embeds each text once, and only what changed"""
    passages, _, _, texts, _ = desk
    scripted(model, texts)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        Index.build(model.client(), cache, passages)
        sent = [text for request in model.requests for text in request.body["input"]]
        assert sorted(sent) == sorted({DOCUMENT + text for text in passages.values()})
        model.requests.clear()
        Index.build(model.client(), cache, passages)
        assert model.requests == []
        changed = dict(passages)
        first = next(iter(changed))
        changed[first] = "Call us to change your address."
        texts[DOCUMENT + changed[first]] = texts[DOCUMENT + passages[first]]
        Index.build(model.client(), cache, changed)
        sent = [text for request in model.requests for text in request.body["input"]]
        assert sent == [DOCUMENT + changed[first]]


@pytest.mark.id("tst_e5n9cr")
def test_best_first(model, tmp_path):
    """The best passage first, and the first of two that tie"""
    shares = {"p1": 0.5, "p2": 0.9, "p3": 0.7, "p4": 0.9, "p5": 0.3}
    passages = {id_: f"Passage {id_}." for id_ in shares}

    def vector(text):
        text = text.removeprefix(DOCUMENT).removeprefix(QUERY)
        share = shares.get(text.removeprefix("Passage ").removesuffix("."), 1.0)
        found = np.zeros(768)
        found[:4] = [share, 0.0, np.sqrt(1 - share**2), 0.0]
        if text == "Which passage?":
            found[:4] = [0.8, 0.0, 0.0, 0.6]
        return found.tolist()

    model.embeds(vector)
    with Cache(tmp_path / "vectors.sqlite") as cache:
        index = Index.build(model.client(), cache, passages)
        assert index.find(model.client(), cache, ["Which passage?"], k=4) == [
            ["p2", "p4", "p3", "p1"]
        ]


@pytest.mark.id("tst_h6u0yt")
def test_loaded(model, tmp_path, desk):
    """Finds the same after loading"""
    passages, questions, _, texts, _ = desk
    scripted(model, texts)
    asked = list(questions.values())[:40]
    with Cache(tmp_path / "vectors.sqlite") as cache:
        index = Index.build(model.client(), cache, passages)
        index.save(tmp_path / "index.npz")
        found = index.find(model.client(), cache, asked, k=K)
        assert (
            Index.load(tmp_path / "index.npz").find(model.client(), cache, asked, k=K)
            == found
        )
