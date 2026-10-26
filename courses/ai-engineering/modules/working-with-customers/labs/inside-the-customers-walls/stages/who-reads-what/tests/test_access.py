import random

import pytest

from access import DOCUMENTS, Document, readable, search


def ids(documents):
    return [document.id for document in documents]


@pytest.mark.id("tst_7rfc95")
def test_readable():
    """Gives the documents that name one of the person's groups, and none for no groups"""
    assert ids(readable(DOCUMENTS, frozenset({"benefits"}))) == ["d1", "d2", "d5"]
    assert ids(readable(DOCUMENTS, frozenset({"front-desk", "veterans"}))) == [
        "d4",
        "d5",
        "d6",
    ]
    assert readable(DOCUMENTS, frozenset()) == []
    everyone = frozenset({"benefits", "veterans", "front-desk", "supervisors"})
    assert "d8" not in ids(readable(DOCUMENTS, everyone))


@pytest.mark.id("tst_vzvpoj")
def test_search_within_what_they_may_read():
    """Ranks only what the person may read, filling k from it"""
    question = "Can I agree a repayment plan for an overpayment?"
    assert ids(search(question, DOCUMENTS, frozenset({"supervisors"}))) == ["d2", "d3"]
    assert ids(search(question, DOCUMENTS, frozenset({"benefits"}))) == ["d2"]
    assert search(question, DOCUMENTS, frozenset({"front-desk"})) == []
    staff = frozenset({"benefits", "veterans"})
    found = search(
        "When is the veterans' adviser in for a claim?", DOCUMENTS, staff, k=2
    )
    assert ids(found) == ["d4", "d1"]


@pytest.mark.id("tst_5vogfw")
def test_words_that_count():
    """Compares words in lower case, without punctuation, of four letters or more"""
    found = search("CRISIS?! ...the caller", DOCUMENTS, frozenset({"front-desk"}))
    assert ids(found) == ["d5"]
    assert search("Is it on?", DOCUMENTS, frozenset({"front-desk"})) == []


@pytest.mark.id("tst_x146ml")
def test_random_documents():
    """Matches filtering by hand then counting shared words, on random documents"""
    rng = random.Random(1003)
    vocabulary = [f"word{n}" for n in range(25)]
    names = ["a", "b", "c", "d"]
    for _ in range(200):
        documents = [
            Document(
                f"d{n}",
                " ".join(rng.sample(vocabulary, 2)),
                " ".join(rng.sample(vocabulary, 5)),
                frozenset(rng.sample(names, rng.randint(0, 2))),
            )
            for n in range(rng.randint(1, 12))
        ]
        groups = frozenset(rng.sample(names, rng.randint(0, 3)))
        question = " ".join(rng.sample(vocabulary, rng.randint(1, 5)))
        k = rng.randint(1, 4)
        asked = set(question.split())
        counts = [
            (-len(asked & set(f"{d.title} {d.text}".split())), place, d.id)
            for place, d in enumerate(documents)
            if d.groups & groups
        ]
        expected = [found for count, _, found in sorted(counts) if count < 0][:k]
        assert ids(search(question, documents, groups, k)) == expected
