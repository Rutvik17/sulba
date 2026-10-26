import random
import re

import pytest

from faq import HANDOVER, MODEL, Answer, Entry, answer


def shown_ids(model):
    """The ids of the office's answers listed in each request's system message, each at the
    start of a line."""
    return [
        re.findall(r"^\[(f\d+)\]", request.body["messages"][0]["content"], re.MULTILINE)
        for request in model.requests
    ]


@pytest.mark.id("tst_w5jt6q")
def test_the_briefs_example(model):
    """Answers from the office's answers, citing the one it used"""
    model.says("We're open Monday to Friday, 8:30 to 4:30 [f1].")
    question = "When is the office open on Friday?"
    found = answer(model.client(), question)
    assert found == Answer("We're open Monday to Friday, 8:30 to 4:30 [f1].", ("f1",))
    (request,) = model.requests
    assert request.body["model"] == MODEL
    system, user = request.body["messages"]
    assert system["role"] == "system" and "[f1]" in system["content"]
    assert user == {"role": "user", "content": question}


@pytest.mark.id("tst_az488e")
def test_the_three_that_share_most(model):
    """Shows the three answers that share the most words, the earlier first on a tie"""
    model.says("Book a session with an adviser [f5].")
    answer(model.client(), "Can an adviser help me fill in the form at the front desk?")
    assert shown_ids(model) == [["f5", "f3", "f4"]]


@pytest.mark.id("tst_1evgmh")
def test_words_that_count(model):
    """Compares words in lower case, without punctuation, of four letters or more"""
    model.says("Visitors park free for two hours [f6].")
    assert answer(model.client(), "WHERE... do I PARK?!").cited == ("f6",)
    assert shown_ids(model) == [["f6", "f9"]]
    assert answer(model.client(), "Can I do it?") == Answer(HANDOVER, ())
    assert len(model.requests) == 1


@pytest.mark.id("tst_jv17dh")
def test_answers_it_cant_give(model):
    """Hands over an answer that cites none of those shown, or one that wasn't"""
    question = "When is the office open on Friday?"
    model.says("We're open on weekdays.")
    assert answer(model.client(), question) == Answer(HANDOVER, ())
    model.says("We're open on weekdays [f1], and you can park behind it [f6].")
    assert answer(model.client(), question) == Answer(HANDOVER, ())
    model.says("We're open on weekdays [f1] [f1].")
    assert answer(model.client(), question).cited == ("f1",)


@pytest.mark.id("tst_4pmmtk")
def test_the_model_down(model):
    """Hands over when the model fails or doesn't answer"""
    model.fails(500, "Internal error")
    assert answer(model.client(), "Where do I park?") == Answer(HANDOVER, ())
    model.hangs()
    assert answer(model.client(), "Where do I park?") == Answer(HANDOVER, ())


@pytest.mark.id("tst_95zv85")
def test_random_questions(model):
    """Shows the answers a count of shared words ranks first, on random questions"""
    rng = random.Random(402)
    vocabulary = [f"word{n}" for n in range(30)]
    faq = [
        Entry(
            f"f{n}",
            " ".join(rng.sample(vocabulary, 4)),
            " ".join(rng.sample(vocabulary, 6)),
        )
        for n in range(12)
    ]
    for _ in range(100):
        question = " ".join(rng.sample(vocabulary, rng.randint(1, 6)))
        asked = set(question.split())
        ranked = sorted(
            (-len(asked & set(f"{e.question} {e.answer}".split())), place, e.id)
            for place, e in enumerate(faq)
        )
        expected = [entry for count, _, entry in ranked if count < 0][:3]
        before = len(model.requests)
        if expected:
            model.says(f"From the office's answers [{expected[0]}].")
        found = answer(model.client(), question, faq)
        if expected:
            assert shown_ids(model)[before] == expected
            assert found.cited == (expected[0],)
        else:
            assert found == Answer(HANDOVER, ()) and len(model.requests) == before
