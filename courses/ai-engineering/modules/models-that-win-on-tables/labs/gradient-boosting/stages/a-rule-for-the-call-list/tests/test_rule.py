import numpy as np
import pandas as pd
import pytest
from lightgbm import LGBMClassifier, early_stopping

from boost import (
    CATEGORIES,
    LEAVES,
    NUMBERS,
    PATIENCE,
    RATE,
    ROUNDS,
    call_model,
    frame,
    raised,
)

# A stand-in model's chance of yes for each number of calls, and for any other number.
SHARES, OTHER = {1: 0.2, 2: 0.1, 3: 0.25, 4: 0.05}, 0.1


class Stub:
    """A model whose chance of yes depends only on the calls made."""

    def predict_proba(self, columns):
        share = np.array([SHARES.get(calls, OTHER) for calls in columns["campaign"]])
        return np.column_stack([1 - share, share])


@pytest.fixture(scope="module")
def bank():
    table = pd.read_csv("data/calls.csv")
    return table[table["set"] == 0], table[table["set"] == 1]


def said_yes(calls):
    return (calls["subscribed"] == "yes").to_numpy()


def columns(calls):
    found = calls[NUMBERS + CATEGORIES].copy()
    for name in CATEGORIES:
        found[name] = found[name].astype("category")
    return found


def reference(train, validation, constraints):
    """LightGBM fitted as the brief describes, with these constraints or none."""
    rules = {} if constraints is None else {"monotone_constraints": constraints}
    model = LGBMClassifier(
        n_estimators=ROUNDS, learning_rate=RATE, num_leaves=LEAVES, verbose=-1, **rules
    )
    model.fit(
        columns(train),
        said_yes(train),
        eval_set=[(columns(validation), said_yes(validation))],
        callbacks=[early_stopping(PATIENCE, verbose=False)],
    )
    return model


def same_model(found, wanted, validation):
    assert found.best_iteration_ == wanted.best_iteration_
    np.testing.assert_allclose(
        found.predict_proba(frame(validation))[:, 1],
        wanted.predict_proba(columns(validation))[:, 1],
        rtol=0,
        atol=1e-12,
    )


@pytest.mark.id("tst_lwe2vm")
def test_frame(bank):
    """The numbers as they are, then the categories as pandas categories"""
    train, _ = bank
    calls = train.head(30)
    found = frame(calls)
    assert list(found) == NUMBERS + CATEGORIES
    pd.testing.assert_frame_equal(found[NUMBERS], calls[NUMBERS])
    for name in CATEGORIES:
        assert isinstance(found[name].dtype, pd.CategoricalDtype)
        assert found[name].astype(str).tolist() == calls[name].tolist()


@pytest.mark.id("tst_clevt1")
def test_without_rule(bank):
    """LightGBM as the brief describes, stopped early on the validation calls"""
    train, validation = bank
    found = call_model(train, validation, False)
    same_model(found, reference(train, validation, None), validation)


@pytest.mark.id("tst_j8qjdo")
def test_with_rule(bank):
    """With the rule, campaign's chance never rising"""
    train, validation = bank
    constraints = [-1 if name == "campaign" else 0 for name in NUMBERS + CATEGORIES]
    found = call_model(train, validation, True)
    same_model(found, reference(train, validation, constraints), validation)


@pytest.mark.id("tst_2mfjny")
def test_raised_by_hand(bank):
    """Clients moved up by a call or more, counted by hand"""
    train, _ = bank
    clients = train.head(5).assign(campaign=[1, 2, 3, 4, 5])
    # One call more moves up the clients called twice and four times so far, and two more the
    # client called once. The client called five times keeps its chance.
    assert raised(Stub(), clients, 1) == 2
    assert raised(Stub(), clients, 2) == 3
