import csv
from collections import defaultdict

import numpy as np
import pytest

from compare import compared, ranked, within

# The words of the chunks a search hands the model.
BUDGET = 400


def read(path):
    """A vector file's ids, and its whole numbers."""
    with open(path, encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))[1:]
    return [row[0] for row in rows], np.array([row[1:] for row in rows], dtype=np.int64)


@pytest.fixture(scope="module")
def validation():
    """The validation questions' vectors, and each question's answer."""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        page_of = {
            row["question"]: row["page"]
            for row in csv.DictReader(file)
            if row["set"] == "validation"
        }
    parts = defaultdict(list)
    with open("data/answers.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["question"] in page_of:
                place = (page_of[row["question"]], int(row["start"]), int(row["end"]))
                parts[row["question"]].append(place)
    ids, vectors = read("data/question-vectors-256.csv")
    rows = [index for index, id_ in enumerate(ids) if id_ in page_of]
    return vectors[rows], [parts[ids[row]] for row in rows]


def chunking(name):
    """A chunking's chunks, in the order of its vectors: their places, their vectors and
    their words."""
    with open("data/pages.csv", encoding="utf-8", newline="") as file:
        pages = {row["page"]: row["text"] for row in csv.DictReader(file)}
    with open("data/chunks.csv", encoding="utf-8", newline="") as file:
        place_of = {
            row["chunk"]: (row["page"], int(row["start"]), int(row["end"]))
            for row in csv.DictReader(file)
            if row["chunking"] == name
        }
    ids, vectors = read(f"data/vectors-{name}.csv")
    places = [place_of[id_] for id_ in ids]
    words = [len(pages[page][start:end].split()) for page, start, end in places]
    return places, vectors, words


def scores(questions, answers, places, vectors, words, budget):
    """The mean recall, precision and IoU, worked out character by character."""
    found = []
    for question, parts in zip(questions, answers):
        order = np.argsort(-(vectors @ question), kind="stable")
        sizes = np.cumsum([words[row] for row in order])
        taken = [
            places[row] for row in order[: np.searchsorted(sizes, budget, "right")]
        ]
        answer = {(page, at) for page, start, end in parts for at in range(start, end)}
        held = {(page, at) for page, start, end in taken for at in range(start, end)}
        shared = len(answer & held)
        size = sum(end - start for _, start, end in taken)
        found.append(
            (
                shared / len(answer),
                shared / size if taken else 0.0,
                shared / (len(answer) + size - shared),
            )
        )
    return tuple(np.mean(found, axis=0))


@pytest.mark.id("tst_8rb51x")
def test_ranked():
    """The most similar first, a tie going to the earlier row"""
    vectors = np.array([[1, 0], [3, 4], [0, 5], [3, 4]], dtype=np.int64)
    assert ranked(np.array([0, 1]), vectors).tolist() == [2, 1, 3, 0]
    assert ranked(np.array([1, 0]), vectors).tolist() == [1, 3, 0, 2]


@pytest.mark.id("tst_jmoffz")
def test_within():
    """Chunks in order until the next would pass the budget"""
    words = [50, 120, 80, 30]
    assert within(np.array([1, 2, 0, 3]), words, 250) == [1, 2, 0]
    assert within(np.array([3, 0, 2, 1]), words, 160) == [3, 0, 2]
    assert within(np.array([1, 3]), words, 100) == []


@pytest.mark.id("tst_g9ktsn")
def test_compared():
    """Each question's scores, averaged over the questions"""
    places = [("a", 0, 10), ("a", 10, 20), ("b", 0, 10)]
    vectors = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.int64)
    questions = np.array([[1, 0], [0, 1]], dtype=np.int64)
    answers = [[("a", 0, 5)], [("a", 12, 18)]]
    found = compared(questions, answers, places, vectors, [2, 2, 2], 4)
    assert found == pytest.approx((1.0, 0.275, 0.275))


@pytest.mark.id("tst_tu6jo7")
def test_chunkings(validation):
    """The validation questions on two chunkings, at 400 words"""
    questions, answers = validation
    for name in ("blocks-100", "words-200-50"):
        places, vectors, words = chunking(name)
        expected = scores(questions, answers, places, vectors, words, BUDGET)
        found = compared(questions, answers, places, vectors, words, BUDGET)
        assert found == pytest.approx(expected), name
