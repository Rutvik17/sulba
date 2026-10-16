import numpy as np
import pandas as pd
import pytest
from scipy.stats import t
from sklearn.base import clone
from sklearn.metrics import roc_auc_score

from compare import choose, latest, models, review

# The folds' calls fitted on and held out.
N_FIT, N_HELD = 3294, 824


def scored(leads, spreads=None, folds=25, seed=0):
    """A baseline's AUCs on each fold, and a model's for each lead: its differences from
    the baseline, a standard deviation of spread apart, have a mean of lead corrected
    standard errors."""
    rng = np.random.default_rng(seed)
    base = 0.72 + rng.normal(0, 0.02, folds)
    table = {"baseline": base}
    for i, lead in enumerate(leads):
        spread = 0.01 if spreads is None else spreads[i]
        noise = rng.normal(0, 1, folds)
        noise = (noise - noise.mean()) / noise.std(ddof=1)
        se = spread * np.sqrt(1 / folds + N_HELD / N_FIT)
        table[f"model {i}"] = base + lead * se + spread * noise
    return pd.DataFrame(table)


def reference(differences, n_fit, n_held, confidence):
    n = len(differences)
    se = np.sqrt(np.var(differences, ddof=1) * (1 / n + n_held / n_fit))
    half = t.ppf((1 + confidence) / 2, n - 1) * se
    return np.mean(differences) - half, np.mean(differences) + half


@pytest.mark.id("tst_3gyo7x")
def test_by_hand():
    """A review of two models by hand"""
    base = np.array([0.70, 0.72, 0.74, 0.71])
    scores = pd.DataFrame(
        {
            "baseline": base,
            "a": base + [0.01, 0.02, 0.03, 0.02],
            "b": base + [-0.01, 0.0, 0.01, 0.0],
        }
    )
    found = review(scores, "baseline", 300, 100, 0.9)
    assert list(found.index) == ["a", "b"]
    for name in ["a", "b"]:
        low, high = reference(scores[name] - base, 300, 100, 0.95)
        assert found.loc[name, "difference"] == pytest.approx(
            np.mean(scores[name] - base)
        )
        assert found.loc[name, "low"] == pytest.approx(low, rel=1e-9)
        assert found.loc[name, "high"] == pytest.approx(high, rel=1e-9)
    assert found["beats"].tolist() == [True, False]


@pytest.mark.id("tst_0jftev")
def test_shared():
    """Intervals at a confidence shared among four models"""
    scores = scored([1, 2, 3, 4])
    found = review(scores, "baseline", N_FIT, N_HELD, 0.95)
    for name in found.index:
        differences = scores[name] - scores["baseline"]
        low, high = reference(differences, N_FIT, N_HELD, 1 - 0.05 / 4)
        assert found.loc[name, "low"] == pytest.approx(low, rel=1e-9)
        assert found.loc[name, "high"] == pytest.approx(high, rel=1e-9)


@pytest.mark.id("tst_mstivw")
def test_largest_lead():
    """The largest lead among the models that beat the baseline"""
    scores = scored([1, 8, 8], spreads=[0.05, 0.002, 0.004])
    assert choose(scores, "baseline", N_FIT, N_HELD, 0.95) == "model 2"


@pytest.mark.id("tst_j7f1p5")
def test_none_beats():
    """The baseline when no model beats it"""
    scores = scored([0.5, 1.0, -2.0])
    assert choose(scores, "baseline", N_FIT, N_HELD, 0.95) == "baseline"


@pytest.mark.id("tst_qifqt4")
def test_latest():
    """The last share of the calls, fitted on the calls before them"""
    table = pd.read_csv("data/calls.csv")
    calls = table.iloc[::5].reset_index(drop=True)
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    tree = models()["decision tree"]
    start = len(calls) - round(len(calls) * 0.25)
    fitted = clone(tree).fit(calls.iloc[:start], said_yes[:start])
    chances = fitted.predict_proba(calls.iloc[start:])[:, 1]
    wanted = roc_auc_score(said_yes[start:], chances)
    assert latest(tree, calls, said_yes, 0.25) == pytest.approx(wanted, rel=1e-12)
