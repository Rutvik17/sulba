"""Chooses the plant's strength model on the validation mixes, fits it with
scikit-learn, and says how far off it will be on mixes the plant hasn't made yet."""

import numpy as np
from sklearn import model_selection
from sklearn.linear_model import Ridge
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

DEGREES = [1, 2, 3]
PENALTIES = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]


def model(degree, penalty, rows):
    """Polynomial features of the eight measurements, standardized, then ridge
    regression with the penalty from model.py, to be fit on `rows` tests."""
    return make_pipeline(
        PolynomialFeatures(degree, include_bias=False),
        StandardScaler(),
        # Ridge penalizes the sum of the squared errors, not their mean.
        Ridge(alpha=penalty * rows),
    )


def choose(train, validation):
    """The degree and penalty with the lowest error on the validation mixes."""
    X, y = train
    X_val, y_val = validation
    errors = {}
    for degree in DEGREES:
        for penalty in PENALTIES:
            fitted = model(degree, penalty, len(y)).fit(X, y)
            errors[degree, penalty] = root_mean_squared_error(
                y_val, fitted.predict(X_val)
            )
    return min(errors, key=errors.get)


def split(mixes):
    """The tests to fit on and the tests to score on: a fifth of the plant's
    mixes, held out with every test of each."""
    tests = np.arange(len(mixes))
    held = model_selection.GroupShuffleSplit(test_size=0.2, random_state=0)
    return next(held.split(tests, groups=mixes))


def expected_error(X, y, mixes, degree, penalty):
    """The RMSE to expect on mixes the plant hasn't made yet."""
    fit, new = split(mixes)
    fitted = model(degree, penalty, len(fit)).fit(X[fit], y[fit])
    return root_mean_squared_error(y[new], fitted.predict(X[new]))
