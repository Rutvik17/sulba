import numpy as np
import pytest

from gate import Verdict, gate
from release_gate import check, report, scored

RELEVANT = {"q1": {"p3"}, "q2": {"p4"}}


def reply(question, sample, text, finish="stop"):
    return {
        "question": question,
        "release": "current",
        "sample": str(sample),
        "reply": text,
        "finish": finish,
    }


@pytest.mark.id("tst_qbcfj8")
def test_scored():
    """Scores each reply on the three scores, a row for each question"""
    replies = [
        reply("q1", 1, "Apply online [p3]."),
        reply("q1", 2, "word " * 101 + "[p3]", "length"),
        reply("q2", 1, "Bring your ID [p5]."),
        reply("q2", 2, "Bring your ID [p4]."),
    ]
    found = scored(replies, RELEVANT, ["q1", "q2"], "current", [1, 2])
    assert list(found) == ["cites_answer", "finished", "brief"]
    assert found["cites_answer"].tolist() == [[1.0, 1.0], [0.0, 1.0]]
    assert found["finished"].tolist() == [[1.0, 0.0], [1.0, 1.0]]
    assert found["brief"].tolist() == [[1.0, 0.0], [1.0, 1.0]]


@pytest.mark.id("tst_jm6sl1")
def test_report():
    """A line for each score, then the decision"""
    verdicts = {
        "cites_answer": Verdict(change=-0.05, low=-0.1, high=0.002, ships=True),
        "finished": Verdict(change=-0.2, low=-0.25, high=-0.15, ships=False),
    }
    assert report(verdicts) == [
        "cites_answer: -0.050 (-0.100 to +0.002), ships",
        "finished: -0.200 (-0.250 to -0.150), stopped",
        "stopped",
    ]


@pytest.mark.id("tst_gbego8")
def test_same_release():
    """Ships a release whose scores are the baseline's"""
    rng = np.random.default_rng(2)
    pages = [f"page-{number // 2}" for number in range(40)]
    scores = {
        name: (rng.random((40, 5)) < 0.6).astype(float)
        for name in ("cites_answer", "finished", "brief")
    }
    verdicts = check(scores, scores, pages, 0.05)
    assert all(verdict.ships for verdict in verdicts.values())
    assert verdicts["brief"] == gate(scores["brief"], scores["brief"], pages, 0.05 / 3)
    assert report(verdicts)[-1] == "ships"
