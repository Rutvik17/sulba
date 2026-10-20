import pytest

from checks import checks, cited, pass_rates

SHOWN = ["p17", "p132", "p110", "p318", "p259"]


@pytest.mark.id("tst_iatfim")
def test_cited():
    """Finds each passage a reply cites by its name in square brackets, once"""
    reply = (
        "Apply online [p17][p132]. Bring form [FS-240] and your card [p17]; see p110."
    )
    assert cited(reply) == ["p17", "p132"]
    assert cited("No passage says.") == []


@pytest.mark.id("tst_a5hoho")
def test_a_reply_that_passes():
    """Passes a short reply that cites a passage it was shown that holds the answer"""
    found = checks("Apply online [p17].", "stop", SHOWN, {"p17", "p2198"}, 80)
    assert found == {
        "cites": True,
        "cites_shown": True,
        "cites_answer": True,
        "finished": True,
        "brief": True,
    }


@pytest.mark.id("tst_1uxybm")
def test_each_check_fails_alone():
    """Fails each check on the reply that breaks it, and no other"""
    relevant = {"p17"}
    cases = {
        "cites": ("The passages don't say.", "stop", relevant),
        "cites_shown": ("Apply online [p17], or by phone [p9].", "stop", relevant),
        "cites_answer": ("Bring your card [p132].", "stop", relevant),
        "finished": ("Apply online [p17], and", "length", relevant),
        "brief": ("Apply online [p17]. " + "More words " * 40, "stop", relevant),
    }
    for failing, (reply, finish, answers) in cases.items():
        found = checks(reply, finish, SHOWN, answers, 80)
        expected = {name: name != failing for name in found}
        if failing == "cites":
            expected["cites_answer"] = False
        assert found == expected, failing


@pytest.mark.id("tst_azjs3u")
def test_words():
    """Counts the words between spaces, up to and including the most allowed"""
    eighty = " ".join(["word"] * 79 + ["[p17]"])
    assert checks(eighty, "stop", SHOWN, {"p17"}, 80)["brief"]
    assert not checks(eighty + " more", "stop", SHOWN, {"p17"}, 80)["brief"]


@pytest.mark.id("tst_r4udxf")
def test_pass_rates():
    """Gives each check's share of the replies, and the share that pass them all"""
    results = [
        {"cites": True, "finished": True},
        {"cites": True, "finished": False},
        {"cites": False, "finished": True},
        {"cites": True, "finished": True},
    ]
    assert pass_rates(results) == {"cites": 0.75, "finished": 0.75, "all": 0.5}
