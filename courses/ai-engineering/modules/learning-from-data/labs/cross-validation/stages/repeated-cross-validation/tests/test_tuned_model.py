import numpy as np
import pytest

from cv import features
from tuning import TunedModel, fitted, records, scores


@pytest.fixture(scope="module")
def plant():
    """The plant's records of its first 100 mixes: (X, y, mixes)."""
    X, y, mixes = records(np.loadtxt("data/concrete.csv", delimiter=",", skiprows=1))
    first = mixes < 100
    return X[first], y[first], mixes[first]


@pytest.fixture(scope="module")
def shipped(plant):
    return TunedModel(*(part.copy() for part in plant))


@pytest.mark.id("tst_ez0ubb")
def test_scores_averaged_over_seeds(plant, shipped):
    """Each pair's RMSE is averaged over a shuffle for each seed"""
    each = [scores(*(part.copy() for part in plant), seed) for seed in (0, 1)]
    assert set(shipped.scores) == set(each[0])
    for pair in each[0]:
        expected = np.mean([found[pair] for found in each])
        assert shipped.scores[pair] == pytest.approx(expected, abs=1e-9)


@pytest.mark.id("tst_nkeqxo")
def test_one_seed(plant):
    """With one seed, the scores are that shuffle's"""
    model = TunedModel(*(part.copy() for part in plant), seeds=(7,))
    found = scores(*(part.copy() for part in plant), 7)
    for pair, error in found.items():
        assert model.scores[pair] == pytest.approx(error, abs=1e-9)


@pytest.mark.id("tst_pttsee")
def test_chooses_lowest_average(shipped):
    """Chooses the pair with the lowest average"""
    assert (shipped.degree, shipped.penalty) == min(
        shipped.scores, key=shipped.scores.get
    )


@pytest.mark.id("tst_30ggf9")
def test_fit_on_every_record(plant, shipped):
    """Fit on every record"""
    X, y, _ = plant
    degree, penalty = shipped.degree, shipped.penalty
    model = fitted(features(X, degree), y, penalty)
    strengths = np.asarray(shipped.predict(X[:50].copy()), dtype=float)
    assert np.max(np.abs(strengths - model(features(X[:50], degree)))) <= 1e-9
