import csv

import pytest
from assistant import (
    BEST,
    INSTRUCTIONS,
    MODEL,
    STAFF,
    WORDS,
    Answer,
    Passage,
    Search,
    answer,
    passages,
)

PAGES = "data/pages.csv"
QUESTIONS = "data/questions.csv"
# The share of the office's questions whose page must be among their best passages' pages.
BAR = 0.65
QUESTION = "How do I renew my FAFSA application?"


def rows(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def split(text):
    """A page's text as its passages should be: its blocks joined until another would take a
    passage past WORDS words."""
    found, joined, count = [], [], 0
    for block in text.split("\n\n"):
        size = len(block.split())
        if joined and count + size > WORDS:
            found.append("\n\n".join(joined))
            joined, count = [], 0
        joined.append(block)
        count += size
    return [*found, "\n\n".join(joined)] if joined else found


@pytest.fixture(scope="module")
def search():
    return Search(passages(PAGES))


@pytest.mark.id("tst_eel21n")
def test_passages():
    """Splits each page into passages of whole blocks, up to the word limit, in order"""
    expected = [
        Passage(page["page"], page["title"], text)
        for page in rows(PAGES)
        for text in split(page["text"])
    ]
    assert passages(PAGES) == expected


@pytest.mark.id("tst_e40jnv")
def test_search(search):
    """Finds the page that answers the office's questions among their best passages"""
    questions = rows(QUESTIONS)
    found = 0
    for question in questions:
        best = search.best(question["text"], BEST)
        assert len(best) <= BEST
        found += question["page"] in {passage.page for passage in best}
    assert found / len(questions) >= BAR


@pytest.mark.id("tst_66idp4")
def test_nothing_found(search, model):
    """Passes a question that shares no word with any page to staff, without asking the model"""
    assert search.best("Qwxz vbnm", BEST) == []
    assert answer(model.client(), search, "Qwxz vbnm") == Answer(STAFF, [], True)
    assert model.requests == []


@pytest.mark.id("tst_52pdn6")
def test_request(search, model):
    """Asks the model once, with the instructions, the best passages numbered and the question"""
    model.says("Renew it each year on fafsa.gov [1].")
    answer(model.client(), search, QUESTION)
    [request] = model.requests
    assert (request.method, request.path) == ("POST", "/v1/chat/completions")
    assert request.body["model"] == MODEL
    system, user = request.body["messages"]
    assert system == {"role": "system", "content": INSTRUCTIONS}
    assert user["role"] == "user"
    place = 0
    for number, passage in enumerate(search.best(QUESTION, BEST), start=1):
        place = user["content"].index(f"[{number}]", place)
        place = user["content"].index(passage.text, place)
    assert QUESTION in user["content"][place:]


@pytest.mark.id("tst_iovriu")
def test_citations(search, model):
    """Gives the reply with the pages it cites, in the order first cited, each once"""
    best = search.best(QUESTION, BEST)
    model.says("Renew it [2], on time [1], each year [2]. See also [9].")
    found = answer(model.client(), search, QUESTION)
    pages = list(dict.fromkeys([best[1].page, best[0].page]))
    expected = "Renew it [2], on time [1], each year [2]. See also [9]."
    assert found == Answer(expected, pages, False)


@pytest.mark.id("tst_q2zkxh")
def test_to_staff(search, model):
    """Passes the question to staff when the model can't answer, cites nothing, or fails"""
    model.says("I don't know.")
    model.says("You can renew it online.")
    model.fails(503, "Loading model")
    model.disconnects()
    model.hangs()
    client = model.client(timeout=5)
    for _ in range(5):
        assert answer(client, search, QUESTION) == Answer(STAFF, [], True)


@pytest.mark.id("tst_2pu71o")
def test_long(search, model):
    """Answers every one of the office's questions in time"""
    model.answers(lambda received: model.says("See [1]."))
    client = model.client()
    for question in rows(QUESTIONS):
        found = answer(client, search, question["text"])
        assert found.to_staff or found.pages
