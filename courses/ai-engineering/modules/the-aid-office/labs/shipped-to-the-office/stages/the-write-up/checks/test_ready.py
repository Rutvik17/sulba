import csv
import math

import pytest
from evals import RELEASES, change, outcomes, shares
from report import PEAK, markdown, report


def rows(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


@pytest.fixture(scope="module")
def made():
    return report()


@pytest.fixture(scope="module")
def expected():
    """Each release's figures, worked out here from the files."""
    replies, shown = rows("data/replies.csv"), rows("data/shown.csv")
    questions = rows("data/questions.csv")
    timed = rows("data/timings.csv")
    figures = {}
    for name in RELEASES:
        share = shares(outcomes(replies, shown, questions, name))
        mine = [row for row in timed if row["release"] == name]
        firsts, wholes = [], []
        for row in mine:
            prompt, written = float(row["prompt_ms"]), float(row["predicted_ms"])
            tokens = int(row["predicted_n"])
            firsts.append((prompt + (written / tokens if tokens else 0)) / 1000)
            wholes.append((prompt + written) / 1000)
        place = math.ceil(0.95 * len(mine)) - 1
        hourly = 3600 * len(wholes) / sum(wholes)
        figures[name] = (
            share["right"],
            share["wrong"],
            share["staff"],
            sorted(firsts)[place],
            sorted(wholes)[place],
            hourly,
            PEAK / hourly,
        )
    return figures


@pytest.mark.id("tst_u7leex")
def test_answers(made, expected):
    """Each release's shares right, wrong and to staff, from the eval"""
    assert [each.name for each in made.releases] == list(RELEASES)
    for each in made.releases:
        assert (each.right, each.wrong, each.staff) == pytest.approx(
            expected[each.name][:3]
        )


@pytest.mark.id("tst_5kodhr")
def test_times(made, expected):
    """Each release's times for 95% of replies, its replies an hour and its busiest hour"""
    for each in made.releases:
        found = (each.first, each.whole, each.hourly, each.busy)
        assert found == pytest.approx(expected[each.name][3:])


@pytest.mark.id("tst_rm06l2")
def test_release(made):
    """Three's change in the share wrong, with its margin, and the release it points to"""
    replies, shown = rows("data/replies.csv"), rows("data/shown.csv")
    questions = rows("data/questions.csv")
    found = {name: outcomes(replies, shown, questions, name) for name in RELEASES}
    pages = [row["page"] for row in questions]
    wrong = change(found["five"], found["three"], pages, "wrong", 0.95)
    assert (made.wrong.change, made.wrong.margin) == pytest.approx(
        (wrong.change, wrong.margin)
    )
    assert made.chosen == "five"


@pytest.mark.id("tst_3z74ko")
def test_write_up(made, expected):
    """The write-up's table and decision, with the report's figures"""
    text = markdown(made)
    for name, (right, wrong, staff, first, whole, hourly, share) in expected.items():
        row = (
            f"| {name} | {right:.0%} | {wrong:.0%} | {staff:.0%} | {first:.1f} s "
            f"| {whole:.1f} s | {hourly:,.0f} | {share:.0%} |"
        )
        assert row in text.splitlines()
    assert text.endswith("The office should run five passages.")
    assert f"{made.wrong.margin * 100:.1f} points at 95%" in text
