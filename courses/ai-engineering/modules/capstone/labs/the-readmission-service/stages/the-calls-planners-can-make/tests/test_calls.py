import numpy as np
import pytest
from sklearn.metrics import precision_score, recall_score

from features import stays
from model import calls, out_of_fold, threshold_for


@pytest.fixture(scope="module")
def drawn():
    """Readmissions and probabilities for 1,000 made-up stays, the readmitted ones higher."""
    rng = np.random.default_rng(0)
    y = rng.random(1000) < 0.1
    probabilities = np.clip(rng.normal(0.1 + 0.1 * y, 0.05), 0, 1)
    return y, probabilities


@pytest.mark.id("tst_xizn74")
def test_threshold(drawn):
    """Puts the threshold at the probabilities' 1 - share quantile"""
    _, probabilities = drawn
    for share in (0.05, 0.1, 0.2, 0.5):
        expected = np.quantile(probabilities, 1 - share)
        assert threshold_for(probabilities, share) == pytest.approx(expected, abs=1e-12)


@pytest.mark.id("tst_tgkk42")
def test_probabilities_untouched(drawn):
    """Leaves the probabilities as they were"""
    y, probabilities = drawn
    given = probabilities.copy()
    calls(y, given, threshold_for(given, 0.1))
    assert np.array_equal(given, probabilities)


@pytest.mark.id("tst_r1e3o7")
def test_calls(drawn):
    """Gives the stays called, the recall and the precision, as scikit-learn does"""
    y, probabilities = drawn
    for threshold in (0.1, 0.15, 0.2, 0.3):
        called = probabilities >= threshold
        count, recall, precision = calls(y, probabilities, threshold)
        assert count == called.sum()
        assert recall == pytest.approx(recall_score(y, called), abs=1e-12)
        assert precision == pytest.approx(precision_score(y, called), abs=1e-12)


@pytest.mark.id("tst_16f2gt")
def test_by_hand():
    """Five stays, worked by hand"""
    count, recall, precision = calls([1, 0, 1, 0, 0], [0.9, 0.8, 0.3, 0.2, 0.1], 0.3)
    assert count == 3
    assert recall == pytest.approx(1)
    assert precision == pytest.approx(2 / 3)
    assert threshold_for([0.1, 0.2, 0.3, 0.4, 0.5], 0.5) == pytest.approx(0.3)


@pytest.mark.id("tst_bujj4j")
def test_lab_stays():
    """Calls the tenth of the lab's stays rated most likely to come back"""
    table = stays("data/encounters.csv")
    y = table["readmitted"]
    probabilities = out_of_fold(table)
    count, recall, _ = calls(y, probabilities, threshold_for(probabilities, 0.1))
    expected = probabilities >= np.quantile(probabilities, 0.9)
    assert count == expected.sum()
    assert recall == pytest.approx(recall_score(y, expected), abs=1e-12)
