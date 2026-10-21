import numpy as np
import pytest

from grounding import line, shown, to_read

PASSAGES = {
    "p1": {
        "page": "va-1",
        "domain": "va",
        "title": "Pensions",
        "text": "We pay monthly.",
    },
    "p2": {"page": "va-2", "domain": "va", "title": "Forms", "text": "Send form 21."},
}


@pytest.mark.id("tst_5jbhjg")
def test_shown():
    """Shows each passage as its name, its page's title and its text"""
    assert shown(["p2", "p1"], PASSAGES) == (
        "[p2] Forms\nSend form 21.\n\n[p1] Pensions\nWe pay monthly."
    )


@pytest.mark.id("tst_g9f19o")
def test_line_and_list():
    """Gives the share flagged and the replies to read"""
    flags = np.array([1.0, 0.0, 1.0, 1.0])
    found = line(flags, ["va-1", "va-1", "va-2", "va-3"], 0.95)
    assert (found.flagged, found.replies) == (0.75, 4)
    assert found.margin > 0
    risks = {"q1": 0.3, "q2": 0.9, "q3": 0.1, "q4": 0.6, "q5": 0.9}
    assert to_read(risks, 0.3) == ["q2", "q5", "q4", "q1"]
