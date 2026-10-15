import numpy as np
import pytest

from screen import Screen


@pytest.fixture(scope="module")
def clinic():
    """The records' measurements and diagnoses, and the new samples with theirs."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    return table[~new, 2:], table[~new, 1], table[new, 2:], table[new, 1]


@pytest.mark.id("tst_eesdi2")
def test_a_score_each(clinic):
    """A score for each new sample"""
    records, diagnoses, new, _ = clinic
    scores = np.asarray(Screen(records, diagnoses).scores(new))
    assert scores.shape == (len(new),)
    assert np.all(np.isfinite(scores))


@pytest.mark.id("tst_616s77")
def test_malignant_scores_higher(clinic):
    """Malignant samples score higher than benign ones, on average"""
    records, diagnoses, new, own = clinic
    scores = np.asarray(Screen(records, diagnoses).scores(new))
    assert scores[own == 1].mean() > scores[own == 0].mean()


@pytest.mark.id("tst_c2hbuu")
def test_k_records_each(clinic):
    """k records for each new sample, with their distances"""
    records, diagnoses, new, _ = clinic
    near, dist = Screen(records, diagnoses).nearest(new, k=5)
    near, dist = np.asarray(near), np.asarray(dist)
    assert near.shape == dist.shape == (len(new), 5)
    assert np.all((near >= 0) & (near < len(records)))
    assert np.all(dist >= 0)


@pytest.mark.id("tst_7gzesv")
def test_records_share_the_diagnosis(clinic):
    """The records found mostly share the sample's diagnosis"""
    records, diagnoses, new, own = clinic
    near, _ = Screen(records, diagnoses).nearest(new, k=5)
    assert np.mean(diagnoses[np.asarray(near)] == own[:, None]) > 0.8
