import numpy as np
import pandas as pd
import pytest

from boost import call_model, frame, raised

# The calls more that raised counts up to, and the most calls more a client is given.
MORE, MOST = 5, 10


@pytest.fixture(scope="module")
def bank():
    table = pd.read_csv("data/calls.csv")
    train, validation, test = (table[table["set"] == part] for part in range(3))
    free = call_model(train, validation, False)
    ruled = call_model(train, validation, True)
    kept = validation.copy()
    count = raised(free, validation, MORE)
    return train, validation, test, free, ruled, count, kept


def chances(model, calls):
    return model.predict_proba(frame(calls))[:, 1]


def chances_after(model, calls, most):
    """Each call's chance with 1 to most calls more, a row for each number of calls."""
    later = pd.concat(
        [calls.assign(campaign=calls["campaign"] + extra) for extra in range(1, most + 1)]
    )
    return chances(model, later).reshape(most, len(calls))


@pytest.mark.id("tst_4ppesb")
def test_never_moved_up(bank):
    """Never moved up for another call"""
    _, validation, _, _, ruled, _, _ = bank
    now = chances(ruled, validation)
    assert (chances_after(ruled, validation, MOST) <= now).all()


@pytest.mark.id("tst_ijrezv")
def test_moved_up_without_rule(bank):
    """The clients moved up without the rule"""
    _, validation, _, free, _, count, kept = bank
    now = chances(free, kept)
    higher = (chances_after(free, kept, MORE) > now).any(axis=0)
    assert count == higher.sum()


@pytest.mark.id("tst_9j8dk5")
def test_unseen_category(bank):
    """A category the training calls never had"""
    train, _, test, _, ruled, _, _ = bank
    unseen = test[~test["default"].isin(train["default"])]
    assert len(unseen) > 0
    missing = unseen.assign(default=np.nan)
    np.testing.assert_allclose(
        chances(ruled, unseen), chances(ruled, missing), rtol=0, atol=1e-12
    )


@pytest.mark.id("tst_c3jxwp")
def test_unchanged(bank):
    """The clients left as they were"""
    _, validation, _, _, _, _, kept = bank
    pd.testing.assert_frame_equal(validation, kept)
