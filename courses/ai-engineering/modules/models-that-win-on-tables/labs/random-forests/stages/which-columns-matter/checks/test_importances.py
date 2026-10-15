import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

from forest import CATEGORIES, NUMBERS, encode, importances

# The forest the checks measure, how many times each group is shuffled, and the groups: each
# column alone, the bank's earlier contact with the client together, and a column the forest
# doesn't read.
TREES, REPEATS, SEED = 20, 2, 11
PAST = ["pdays", "previous", "poutcome"]
GROUPS = {name: [name] for name in NUMBERS + CATEGORIES}
GROUPS |= {"past contact": PAST, "day_of_week": ["day_of_week"]}


def reference(score, calls, said_yes, groups, repeats, rng):
    base = roc_auc_score(said_yes, score(calls))
    found = {}
    for name, columns in groups.items():
        falls = []
        for _ in range(repeats):
            order = rng.permutation(len(calls))
            shuffled = calls.copy()
            for column in columns:
                shuffled[column] = calls[column].to_numpy()[order]
            falls.append(base - roc_auc_score(said_yes, score(shuffled)))
        found[name] = (np.mean(falls), np.std(falls))
    return found


@pytest.fixture(scope="module")
def measured():
    table = pd.read_csv("data/calls.csv")
    train, validation = table[table["set"] == 0], table[table["set"] == 1]
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    model = RandomForestClassifier(TREES, min_samples_leaf=10, random_state=0)
    model.fit(encode(train, categories), (train["subscribed"] == "yes").to_numpy())

    def score(calls):
        return model.predict_proba(encode(calls, categories))[:, 1]

    said_yes = (validation["subscribed"] == "yes").to_numpy()
    kept = validation.copy()
    found = importances(
        score, validation, said_yes, GROUPS, REPEATS, np.random.default_rng(SEED)
    )
    wanted = reference(
        score, kept, said_yes, GROUPS, REPEATS, np.random.default_rng(SEED)
    )
    return found, wanted, validation, kept


@pytest.mark.id("tst_349rfo")
def test_each_column(measured):
    """Each column's fall on the validation calls, and its spread"""
    found, wanted, _, _ = measured
    for name in NUMBERS + CATEGORIES:
        np.testing.assert_allclose(found[name], wanted[name], rtol=0, atol=1e-12)


@pytest.mark.id("tst_iwem0b")
def test_past_contact(measured):
    """The bank's earlier contact, shuffled as one"""
    found, wanted, _, _ = measured
    np.testing.assert_allclose(
        found["past contact"], wanted["past contact"], rtol=0, atol=1e-12
    )
    assert found["past contact"][0] > max(found[name][0] for name in PAST)


@pytest.mark.id("tst_ea0908")
def test_unread(measured):
    """No importance for a column the forest doesn't read"""
    found, _, _, _ = measured
    assert found["day_of_week"] == (0.0, 0.0)


@pytest.mark.id("tst_xh9fmi")
def test_unchanged(measured):
    """The validation calls left as they were"""
    _, _, validation, kept = measured
    pd.testing.assert_frame_equal(validation, kept)
