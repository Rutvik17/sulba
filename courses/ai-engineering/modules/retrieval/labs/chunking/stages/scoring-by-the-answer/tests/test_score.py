import csv
from collections import defaultdict

import pytest

from score import holding, iou, precision, recall


@pytest.fixture(scope="module")
def answers():
    """Each question's answer, its parts as places in its page."""
    with open("data/questions.csv", encoding="utf-8", newline="") as file:
        page_of = {row["question"]: row["page"] for row in csv.DictReader(file)}
    found = defaultdict(list)
    with open("data/answers.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            page = page_of[row["question"]]
            found[row["question"]].append((page, int(row["start"]), int(row["end"])))
    return found


@pytest.fixture(scope="module")
def chunkings():
    """Each chunking's chunks, by page, in order."""
    found = defaultdict(lambda: defaultdict(list))
    with open("data/chunks.csv", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            place = (row["page"], int(row["start"]), int(row["end"]))
            found[row["chunking"]][row["page"]].append(place)
    return found


@pytest.mark.id("tst_oar0te")
def test_scores():
    """A search scored by the characters of the answer it holds"""
    parts = [("a", 10, 20), ("a", 30, 40)]
    found = [("a", 0, 15), ("a", 35, 60)]
    assert recall(parts, found) == pytest.approx(10 / 20)
    assert precision(parts, found) == pytest.approx(10 / 40)
    assert iou(parts, found) == pytest.approx(10 / 50)
    assert recall(parts, [("a", 0, 60)]) == 1
    assert precision(parts, [("a", 10, 20)]) == 1


@pytest.mark.id("tst_z2cx7o")
def test_chunks_that_overlap():
    """Characters two chunks hold: twice in the chunks, once in the answer"""
    parts = [("a", 10, 20)]
    found = [("a", 0, 15), ("a", 5, 25)]
    assert recall(parts, found) == 1
    assert precision(parts, found) == pytest.approx(10 / 35)
    assert iou(parts, found) == pytest.approx(10 / 35)


@pytest.mark.id("tst_v6avi0")
def test_other_pages():
    """Another page's chunks, and no chunks at all"""
    parts = [("a", 0, 10)]
    assert recall(parts, [("b", 0, 10)]) == 0
    assert precision(parts, [("b", 0, 10), ("a", 0, 10)]) == pytest.approx(0.5)
    assert iou(parts, [("b", 0, 10)]) == 0
    assert recall(parts, []) == 0
    assert precision(parts, []) == 0
    assert iou(parts, []) == 0


@pytest.mark.id("tst_fl5t5y")
def test_holding():
    """The chunks that hold any of the answer, in their order"""
    chunks = [("a", 0, 10), ("a", 10, 20), ("a", 20, 30), ("b", 0, 30)]
    assert holding([("a", 9, 10), ("a", 20, 21)], chunks) == [
        ("a", 0, 10),
        ("a", 20, 30),
    ]
    assert holding([("a", 5, 25)], chunks) == chunks[:3]
    assert holding([("c", 0, 5)], chunks) == []


@pytest.mark.id("tst_8wwarh")
def test_answers(answers, chunkings):
    """Every answer, scored on each chunking by the chunks that hold it"""
    for name, pages in chunkings.items():
        for question, parts in answers.items():
            chunks = pages[parts[0][0]]
            answer = {at for _, start, end in parts for at in range(start, end)}
            found = [
                chunk for chunk in chunks if answer & set(range(chunk[1], chunk[2]))
            ]
            assert holding(parts, chunks) == found, (name, question)
            shared = sum(
                any(start <= at < end for _, start, end in found) for at in answer
            )
            size = sum(end - start for _, start, end in found)
            union = len(answer) + size - shared
            assert recall(parts, found) == pytest.approx(shared / len(answer)), (
                name,
                question,
            )
            assert precision(parts, found) == pytest.approx(shared / size), (
                name,
                question,
            )
            assert iou(parts, found) == pytest.approx(shared / union), (name, question)
