import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

from report import CATEGORIES, encode, expected_auc, grow, importance, report, run

TRAIN, VALIDATION = 1200, 400


@pytest.fixture(scope="module")
def bank():
    table = pd.read_csv("data/calls.csv")
    # The first calls of each set, enough for every check and quick to run.
    train = table[table["set"] == 0].head(TRAIN)
    validation = table[table["set"] == 1].head(VALIDATION)
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    X, said_yes = encode(train, categories), (train["subscribed"] == "yes").to_numpy()
    # A forest grown by scikit-learn, which keeps each tree's sample.
    model = RandomForestClassifier(15, min_samples_leaf=10, random_state=0)
    model.fit(X, said_yes)
    return train, validation, X, said_yes, model


@pytest.mark.id("tst_wytjya")
def test_samples_differ(bank):
    """Each tree grown on a sample of its own"""
    _, _, X, said_yes, _ = bank
    _, samples = grow(X, said_yes, 3, np.random.default_rng(1))
    for i in range(3):
        for j in range(i + 1, 3):
            assert not np.array_equal(samples[i], samples[j])


@pytest.mark.id("tst_aqbs89")
def test_out_of_bag(bank):
    """The expected AUC from each call's out-of-bag trees alone"""
    _, _, X, said_yes, model = bank
    trees, samples = model.estimators_, model.estimators_samples_
    total, count = np.zeros(len(X)), np.zeros(len(X))
    for tree, sample in zip(trees, samples, strict=True):
        left_out = np.ones(len(X), dtype=bool)
        left_out[sample] = False
        total[left_out] += tree.predict_proba(X[left_out])[:, 1]
        count[left_out] += 1
    scored = count > 0
    expected = roc_auc_score(said_yes[scored], total[scored] / count[scored])
    assert abs(expected_auc(trees, samples, X, said_yes) - expected) < 1e-12


@pytest.mark.id("tst_d9wv5c")
def test_validation(bank):
    """Importance measured on the validation calls"""
    train, validation, _, _, model = bank
    trees, samples = model.estimators_, model.estimators_samples_
    _, falls = report(trees, samples, train, validation, np.random.default_rng(2))
    categories = {name: sorted(train[name].unique()) for name in CATEGORIES}
    expected = importance(trees, validation, categories, np.random.default_rng(2))
    assert falls == expected


@pytest.mark.id("tst_l1ikz1")
def test_same_report(bank):
    """The same report each time it runs"""
    train, validation, _, _, _ = bank
    assert run(train, validation) == run(train, validation)
