import csv
import random
import statistics

import pytest

from kinds import Share, by_kind


def read():
    with open("data/runs.csv", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def run(task, kind, outcome, variant="agent"):
    return {"variant": variant, "task": task, "kind": kind, "outcome": outcome}


@pytest.mark.id("tst_trudz9")
def test_the_desks_agent():
    """Gives each kind's share of the desk's agent's trials done, over its tasks"""
    shares = by_kind(read(), "agent")
    assert list(shares) == ["question", "case", "callback", "new", "vague"]
    assert [share.tasks for share in shares.values()] == [40, 20, 20, 20, 20]
    assert shares["question"].value == pytest.approx(0.405)
    assert shares["vague"] == Share(1.0, 0.0, 20)


@pytest.mark.id("tst_2ld5rd")
def test_each_task_counted_once():
    """Takes each task's share first, and the standard error over the tasks"""
    runs = [run("a", "case", "done") for _ in range(4)] + [run("a", "case", "error")]
    runs += [run("b", "case", "done"), run("b", "case", "wrong day")]
    runs += [run("c", "case", "done"), run("c", "case", "done", variant="other")]
    share = by_kind(runs, "agent")["case"]
    assert share.value == pytest.approx((0.8 + 0.5 + 1.0) / 3)
    assert share.error == pytest.approx(statistics.stdev([0.8, 0.5, 1.0]) / 3**0.5)
    assert share.tasks == 3


@pytest.mark.id("tst_4wshhh")
def test_random_runs():
    """Matches each task's share worked out by hand, on random runs"""
    rng = random.Random(102)
    for _ in range(100):
        runs, expected = [], {}
        for kind in ("question", "new"):
            each = []
            for task in range(rng.randint(2, 8)):
                outcomes = [
                    rng.choice(["done", "error"]) for _ in range(rng.randint(1, 6))
                ]
                runs += [run(f"{kind}{task}", kind, outcome) for outcome in outcomes]
                each.append(outcomes.count("done") / len(outcomes))
            expected[kind] = each
        rng.shuffle(runs)
        shares = by_kind(runs, "agent")
        for kind, each in expected.items():
            assert shares[kind].value == pytest.approx(statistics.fmean(each))
            sd = statistics.stdev(each) / len(each) ** 0.5
            assert shares[kind].error == pytest.approx(sd)


@pytest.mark.id("tst_ypwgqx")
def test_one_task():
    """Refuses a kind with one task"""
    with pytest.raises(ValueError):
        by_kind([run("a", "new", "done"), run("a", "new", "done")], "agent")
