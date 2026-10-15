import numpy as np
import pytest

from report import candidates, report, trained


@pytest.fixture(scope="module")
def table():
    return np.loadtxt("data/pulsars.csv", delimiter=",", skiprows=1)


@pytest.fixture(scope="module")
def found(table):
    return report(table.copy())


@pytest.mark.id("tst_njadbz")
def test_auc_beats_chance(found):
    """The AUC beats chance"""
    assert 0.5 < found["auc"] <= 1


@pytest.mark.id("tst_efbew9")
def test_precision_is_a_share(found):
    """The precision is a share"""
    assert 0 <= found["precision"] <= 1


@pytest.mark.id("tst_we00a3")
def test_expected_fits_the_candidates(table, found):
    """Expects no more pulsars than there are candidates"""
    X, _ = candidates(table, 2)
    assert 0 <= found["expected"] <= len(X)


@pytest.mark.id("tst_k0doks")
def test_probability_for_each_candidate(table):
    """The classifier gives a probability for each candidate"""
    model = trained(*candidates(table, 0))
    X, _ = candidates(table, 2)
    p = model.predict_proba(X[:10])[:, 1]
    assert p.shape == (10,)
    assert np.all((p >= 0) & (p <= 1))
