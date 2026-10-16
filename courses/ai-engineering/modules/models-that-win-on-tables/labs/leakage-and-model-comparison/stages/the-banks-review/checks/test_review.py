import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.metrics import roc_auc_score

from compare import BASELINE, choose, latest, models, review

# The folds' calls fitted on and held out, the candidates no better than the baseline, the
# corrected standard errors each one's lead runs to, and a clear winner's.
N_FIT, N_HELD = 3294, 824
CANDIDATES, LEAD, WINNER = 20, 2.5, 6
# The share of the calls, the latest by date, that the baseline is scored on.
SHARE = 0.2


def scored(leads, folds=25, seed=0):
    """A baseline's AUCs on each fold, and a model's for each lead: its differences from
    the baseline have a mean of lead corrected standard errors."""
    rng = np.random.default_rng(seed)
    base = 0.72 + rng.normal(0, 0.02, folds)
    table = {BASELINE: base}
    for i, lead in enumerate(leads):
        noise = rng.normal(0, 1, folds)
        noise = (noise - noise.mean()) / noise.std(ddof=1)
        spread = 0.01
        se = spread * np.sqrt(1 / folds + N_HELD / N_FIT)
        table[f"candidate {i + 1}"] = base + lead * se + spread * noise
    return pd.DataFrame(table)


@pytest.mark.id("tst_dif2gm")
def test_no_better():
    """Candidates no better than the baseline"""
    scores = scored([LEAD] * CANDIDATES)
    assert choose(scores, BASELINE, N_FIT, N_HELD, 0.95) == BASELINE


@pytest.mark.id("tst_ajzqcf")
def test_clear_winner():
    """A clear winner among them"""
    scores = scored([LEAD] * CANDIDATES + [WINNER])
    found = choose(scores, BASELINE, N_FIT, N_HELD, 0.95)
    assert found == f"candidate {CANDIDATES + 1}"


@pytest.mark.id("tst_n0zxw6")
def test_copy():
    """A copy of the baseline"""
    scores = scored([1.0])
    scores["copy"] = scores[BASELINE]
    found = review(scores, BASELINE, N_FIT, N_HELD, 0.95)
    assert found.loc["copy", "difference"] == 0
    assert found.loc["copy", "low"] == 0 and found.loc["copy", "high"] == 0
    assert not found.loc["copy", "beats"]
    assert choose(scores, BASELINE, N_FIT, N_HELD, 0.95) == BASELINE


@pytest.mark.id("tst_n80n2n")
def test_latest(record_property):
    """The bank's latest calls"""
    calls = pd.read_csv("data/calls.csv")
    said_yes = (calls["subscribed"] == "yes").to_numpy(dtype=int)
    baseline = models()[BASELINE]
    start = len(calls) - round(len(calls) * SHARE)
    fitted = clone(baseline).fit(calls.iloc[:start], said_yes[:start])
    chances = fitted.predict_proba(calls.iloc[start:])[:, 1]
    wanted = roc_auc_score(said_yes[start:], chances)
    found = latest(baseline, calls, said_yes, SHARE)
    record_property("note", f"AUC {found:.3f} on the last {len(calls) - start:,} calls")
    assert found == pytest.approx(wanted, rel=1e-12)
