import numpy as np
import pytest
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from features import CATEGORIES, COUNTS, features, stays
from model import brier, calibration, out_of_fold


@pytest.fixture(scope="module")
def table():
    return stays("data/encounters.csv")


@pytest.fixture(scope="module")
def probabilities(table):
    return out_of_fold(table)


@pytest.mark.id("tst_47o0rk")
def test_out_of_fold(table, probabilities):
    """Gives each stay its fold model's probability, as cross_val_predict does"""
    encode = ColumnTransformer(
        [
            ("numbers", StandardScaler(), [*COUNTS, "age"]),
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORIES),
        ]
    )
    model = make_pipeline(encode, LogisticRegression(max_iter=1000))
    expected = cross_val_predict(
        model,
        features(table),
        table["readmitted"],
        cv=StratifiedKFold(5, shuffle=True, random_state=0),
        method="predict_proba",
    )[:, 1]
    assert len(probabilities) == len(table)
    assert np.allclose(probabilities, expected, rtol=0, atol=1e-9)


@pytest.mark.id("tst_jehiea")
def test_out_of_fold_other_model(table):
    """Gives each stay the probability the model make gives, from the fold that held it out"""
    constant = out_of_fold(table, make=lambda: DummyClassifier(), folds=2)
    folds = StratifiedKFold(2, shuffle=True, random_state=0)
    y = table["readmitted"].to_numpy()
    for learn, test in folds.split(table, y):
        assert np.allclose(constant[test], y[learn].mean(), rtol=0, atol=1e-12)


@pytest.mark.id("tst_dxtt9s")
def test_calibration(table, probabilities):
    """Groups the stays as calibration_curve does with strategy="quantile\""""
    y = table["readmitted"].to_numpy()
    for bins in (5, 10, 20):
        predicted, observed = calibration(y, probabilities, bins)
        share, mean = calibration_curve(
            y, probabilities, n_bins=bins, strategy="quantile"
        )
        assert np.allclose(predicted, mean, rtol=0, atol=1e-12)
        assert np.allclose(observed, share, rtol=0, atol=1e-12)


@pytest.mark.id("tst_3lf8ej")
def test_small_calibration():
    """Four stays in two groups, worked by hand"""
    predicted, observed = calibration([0, 1, 0, 1], [0.1, 0.2, 0.6, 0.9], bins=2)
    assert np.allclose(predicted, [0.15, 0.75])
    assert np.allclose(observed, [0.5, 0.5])


@pytest.mark.id("tst_i2iro9")
def test_brier(table, probabilities):
    """Gives the Brier score scikit-learn gives"""
    y = table["readmitted"].to_numpy()
    assert brier(y, probabilities) == pytest.approx(
        brier_score_loss(y, probabilities), abs=1e-12
    )
    assert brier([0, 1], [0.0, 1.0]) == 0
    assert brier([0, 1], [1.0, 0.0]) == 1
