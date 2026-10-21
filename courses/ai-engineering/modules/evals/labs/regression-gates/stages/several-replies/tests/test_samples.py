import json
from pathlib import Path

import numpy as np
import pytest

from samples import cites_answer, sampling_variance, scores, standard_error

RECORDED = json.loads(Path("references/changes.json").read_text(encoding="utf-8"))[
    "cases"
]
RELEVANT = {"q1": {"p3", "p9"}, "q2": {"p4"}}


def reply(question, release, sample, text):
    return {
        "question": question,
        "release": release,
        "sample": str(sample),
        "reply": text,
    }


@pytest.mark.id("tst_g0msnn")
def test_cites_answer():
    """Scores a reply 1 when a passage it cites holds the answer"""
    assert cites_answer("You can apply online [p2][p9].", {"p3", "p9"}) == 1.0
    assert cites_answer("You can apply online [p2].", {"p3", "p9"}) == 0.0
    assert cites_answer("You can apply online (p3).", {"p3", "p9"}) == 0.0
    assert cites_answer("The passages don't say.", {"p3"}) == 0.0


@pytest.mark.id("tst_l7vsr3")
def test_scores():
    """A row for each question and a column for each sample, in the order asked for"""
    replies = [
        reply("q2", "current", 2, "Bring your ID [p4]."),
        reply("q1", "current", 1, "Apply online [p9]."),
        reply("q1", "unranked", 1, "Apply online [p3]."),
        reply("q2", "current", 1, "Bring your ID [p5]."),
        reply("q1", "current", 2, "Apply by phone [p1]."),
        reply("q2", "unranked", 1, "Bring your ID."),
    ]
    found = scores(replies, RELEVANT, ["q2", "q1"], "current", [1, 2])
    assert found.tolist() == [[0.0, 1.0], [1.0, 0.0]]
    found = scores(replies, RELEVANT, ["q1", "q2"], "unranked", [1])
    assert found.tolist() == [[1.0], [0.0]]


@pytest.mark.id("tst_3cfg1k")
def test_standard_error():
    """statsmodels' standard error of the mean question score, each page's together"""
    for case in RECORDED:
        for name in ("baseline", "candidate"):
            found = standard_error(np.array(case[name]), case["pages"])
            assert found == pytest.approx(case[f"{name}_error"], rel=1e-9)


@pytest.mark.id("tst_i1q465")
def test_sampling_variance():
    """The mean of each question's sample variance, over the number of samples"""
    found = np.array(
        [[1, 1, 0, 1], [0, 0, 0, 1], [1, 1, 1, 1], [0, 1, 0, 0]], dtype=float
    )
    expected = np.mean([0.25, 0.25, 0, 0.25]) / 4
    assert sampling_variance(found) == pytest.approx(expected)
    assert sampling_variance(np.ones((3, 5))) == 0
