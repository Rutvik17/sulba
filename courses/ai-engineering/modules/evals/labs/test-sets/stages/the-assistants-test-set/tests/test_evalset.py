import numpy as np
import pytest

from evalset import held_out, report


def asked(name, page, text):
    return {"question": name, "page": page, "domain": page.split("-")[0], "text": text}


QUESTIONS = [asked(f"q{n}", f"ssa-{n}", f"Question {n}?") for n in range(1, 11)]


@pytest.mark.id("tst_eqacpl")
def test_holds_its_share():
    """Holds half the questions for a share of a half"""
    assert len(held_out(QUESTIONS, 0.5, np.random.default_rng(0))) == 5


@pytest.mark.id("tst_ojesvh")
def test_same_seed():
    """Gives the same test set for the same seed"""
    first = held_out(QUESTIONS, 0.5, np.random.default_rng(4))
    assert held_out(QUESTIONS, 0.5, np.random.default_rng(4)) == first


@pytest.mark.id("tst_ime26d")
def test_leaves_out_repeats():
    """Keeps one of two questions with the same words"""
    repeated = [*QUESTIONS, asked("q11", "ssa-11", "question 1")]
    assert "q11" not in held_out(repeated, 1, np.random.default_rng(0))


@pytest.mark.id("tst_wjrkha")
def test_report():
    """Reports the pass rate and a margin of error"""
    passed = {"q1": True, "q2": False, "q3": True, "q4": True}
    pages = {"q1": "ssa-1", "q2": "ssa-2", "q3": "ssa-3", "q4": "ssa-4"}
    rate, reach = report(passed, pages)
    assert rate == 0.75
    assert 0 < reach < 1
