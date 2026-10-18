import numpy as np
import pytest

from network import forward, loss_and_grads
from run import train_office

# The office's budget, and what its network must read of new writers' digits.
BATCHES, BATCH, TARGET = 1000, 64, 0.94


@pytest.fixture(scope="module")
def office():
    """The pixels, on a scale of 0 to 1, the digits, and the set each digit is in."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    return table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]


@pytest.fixture(scope="module")
def run():
    """The office's run, with the size of each batch it trained on."""
    seen = []

    def counting(params, X, digits):
        seen.append(len(X))
        return loss_and_grads(params, X, digits)

    params, report = train_office(0, loss_and_grads=counting)
    return params, report, seen


def read(office, params, part):
    X, digits, sets = office
    rows = sets == part
    return np.mean(forward(params, X[rows])[2].argmax(axis=1) == digits[rows])


@pytest.mark.id("tst_vi0cu1")
def test_new_writers(office, run, record_property):
    """94% of new writers' digits"""
    share = read(office, run[0], 2)
    record_property("note", f"{share:.1%} right")
    assert share >= TARGET


@pytest.mark.id("tst_isvdhq")
def test_report(office, run, record_property):
    """Its report holds up"""
    params, report, seen = run
    share = read(office, params, 1)
    record_property("note", f"reports {report['validation']:.1%}, reads {share:.1%}")
    assert report["validation"] == pytest.approx(share, abs=1e-12)
    assert report["batches"] == len(seen) and report["batch"] == max(seen)


@pytest.mark.id("tst_mvn2q5")
def test_budget(run, record_property):
    """Within the office's budget"""
    seen = run[2]
    record_property("note", f"{len(seen)} batches of up to {max(seen)} digits")
    assert len(seen) <= BATCHES and max(seen) <= BATCH
