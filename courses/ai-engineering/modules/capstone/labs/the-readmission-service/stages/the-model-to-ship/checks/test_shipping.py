import csv

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from features import CATEGORIES, COUNTS, DEATH_OR_HOSPICE, features, stays
from model import chosen, make_chosen

CODES = ["admission_type_id", "admission_source_id", "discharge_disposition_id"]


@pytest.fixture(scope="module")
def table():
    return stays("data/encounters.csv")


def logistic_regression():
    """Stage 3's model."""
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    return make_pipeline(encode, LogisticRegression(max_iter=1000))


def out_of_fold(table, make):
    """Each stay's probability from the fold model, made by make(), that didn't learn from it,
    and each fold's stays, over the folds cross_validated uses."""
    inputs, y = features(table), table["readmitted"].to_numpy()
    folds = list(StratifiedKFold(5, shuffle=True, random_state=0).split(inputs, y))
    probabilities = np.empty(len(y))
    for learn, test in folds:
        model = make().fit(inputs.iloc[learn], y[learn])
        probabilities[test] = model.predict_proba(inputs.iloc[test])[:, 1]
    return probabilities, [test for _, test in folds]


def mean_and_error(y, probabilities, folds):
    """The folds' mean AUC and its standard error."""
    aucs = [roc_auc_score(y[test], probabilities[test]) for test in folds]
    return np.mean(aucs), np.std(aucs, ddof=1) / np.sqrt(len(aucs))


def mapped_codes(path):
    """Each code column's codes in the ID mapping, three tables one after another, each under a
    header naming its column."""
    codes, column = {}, None
    with open(path, newline="") as file:
        for row in csv.reader(file):
            if not row or not row[0]:
                continue
            if row[0] in CODES:
                column = row[0]
                codes[column] = []
            else:
                codes[column].append(int(row[0]))
    codes["discharge_disposition_id"] = [
        code
        for code in codes["discharge_disposition_id"]
        if code not in DEATH_OR_HOSPICE
    ]
    return codes


@pytest.fixture(scope="module")
def candidate(table):
    """The chosen model's probabilities and folds, or the error it raised."""
    try:
        return out_of_fold(table, make_chosen)
    except Exception as error:
        return error


def scored(candidate, record_property):
    """The chosen model's probabilities and folds, failing the check if there are none."""
    if isinstance(candidate, Exception):
        record_property("note", f"No probabilities for a fold's stays: {candidate}")
        pytest.fail(str(candidate))
    return candidate


@pytest.mark.id("tst_1prpf4")
def test_ranks_as_well(table, candidate, record_property):
    """Ranks stays as well as the logistic regression"""
    y = table["readmitted"].to_numpy()
    mean, error = mean_and_error(y, *scored(candidate, record_property))
    bar, bar_error = mean_and_error(y, *out_of_fold(table, logistic_regression))
    record_property(
        "note",
        f"Mean AUC {mean:.3f} ± {error:.3f}, "
        f"the logistic regression's {bar:.3f} ± {bar_error:.3f}",
    )
    assert mean >= bar - bar_error


@pytest.mark.id("tst_824dam")
def test_expects_the_readmissions(table, candidate, record_property):
    """Expects as many readmissions as came back"""
    probabilities, _ = scored(candidate, record_property)
    readmitted = int(table["readmitted"].sum())
    expected = float(probabilities.sum())
    record_property("note", f"Expects {expected:,.0f}, and {readmitted:,} came back")
    assert abs(expected - readmitted) <= 0.1 * readmitted


@pytest.mark.id("tst_2uysom")
def test_every_code(table, record_property):
    """A probability for every code"""
    model = chosen(table)
    codes = [
        (name, code)
        for name, listed in mapped_codes("data/ids-mapping.csv").items()
        for code in listed
    ]
    # The first stay, once with each code in place of its own.
    stay = table.iloc[0].to_dict()
    requests = pd.DataFrame([{**stay, name: code} for name, code in codes])

    def answered(rows):
        try:
            probabilities = model.predict_proba(features(rows))[:, 1]
        except Exception:
            return False
        return bool(np.all((probabilities >= 0) & (probabilities <= 1)))

    if answered(requests):
        record_property("note", f"A probability for each of {len(codes)} codes")
        return
    for index, (name, code) in enumerate(codes):
        if not answered(requests.iloc[[index]]):
            record_property("note", f"No probability for {name} {code}")
            break
    pytest.fail("A code in the ID mapping got no probability")
