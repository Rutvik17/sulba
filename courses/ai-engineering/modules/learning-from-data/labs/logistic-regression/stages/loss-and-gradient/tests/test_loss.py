import numpy as np
import pytest

from model import gradient, log_loss


def training_set():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    train = table[table[:, 0] == 0]
    return train[:, 2:], train[:, 1]


def expected_sigmoid(z):
    """The sigmoid by NumPy's logaddexp, a form that never overflows."""
    return np.exp(-np.logaddexp(0.0, -np.asarray(z, dtype=float)))


def expected_log_loss(y, p):
    """Cross-entropy as the mean of -ln of the probability each label was given."""
    p = np.clip(np.asarray(p, dtype=float), 1e-15, 1 - 1e-15)
    return -np.mean(np.log(np.where(np.asarray(y) == 1, p, 1 - p)))


def numerical_gradient(X, y, w, b, l2):
    """Central differences of the loss with the l2 term: each weight, then the bias,
    moved by h each way."""

    def loss(w, b):
        return expected_log_loss(y, expected_sigmoid(X @ w + b)) + l2 / 2 * (w @ w)

    h = 1e-6
    dw = [(loss(w + h * e, b) - loss(w - h * e, b)) / (2 * h) for e in np.eye(len(w))]
    db = (loss(w, b + h) - loss(w, b - h)) / (2 * h)
    return np.array(dw), db


@pytest.mark.id("tst_n6o6ox")
def test_confident_and_right():
    """A confident, right answer costs little"""
    y, p = np.array([1.0, 0.0]), np.array([0.999, 0.001])
    assert log_loss(y, p) == pytest.approx(expected_log_loss(y, p), rel=1e-12)


@pytest.mark.id("tst_bwuskn")
def test_coin_flip():
    """A coin flip costs ln 2"""
    assert log_loss(np.array([1.0, 0.0]), np.array([0.5, 0.5])) == pytest.approx(
        np.log(2), rel=1e-12
    )


@pytest.mark.id("tst_sfv14j")
def test_sure_and_wrong():
    """A sure, wrong answer is finite"""
    assert log_loss(np.array([1.0]), np.array([0.0])) == pytest.approx(
        -np.log(1e-15), rel=1e-12
    )


@pytest.mark.id("tst_dghgdb")
def test_four_samples():
    """Four samples"""
    y, p = np.array([1.0, 0.0, 1.0, 0.0]), np.array([0.9, 0.2, 0.6, 0.4])
    assert log_loss(y, p) == pytest.approx(expected_log_loss(y, p), rel=1e-12)


@pytest.mark.id("tst_nl63om")
def test_gradient_at_zero_weights():
    """Gradient at zero weights"""
    X = np.array([[1.0, 2.0], [3.0, -1.0]])
    dw, db = gradient(X, np.array([1.0, 0.0]), np.zeros(2), 0.0)
    assert dw == pytest.approx([0.5, -0.75], rel=1e-12)
    assert db == pytest.approx(0.0, abs=1e-12)


@pytest.mark.id("tst_p4pug7")
def test_numerical_gradient():
    """Matches a numerical gradient"""
    rng = np.random.default_rng(7)
    X = rng.normal(size=(12, 4))
    y = (rng.random(12) < 0.5).astype(float)
    w, b, l2 = rng.normal(size=4), 0.3, 0.1
    dw, db = gradient(X, y, w, b, l2)
    expected_dw, expected_db = numerical_gradient(X, y, w, b, l2)
    assert dw == pytest.approx(expected_dw, abs=1e-6)
    assert db == pytest.approx(expected_db, abs=1e-6)


@pytest.mark.id("tst_7fre7r")
def test_training_set():
    """One slope per measurement on the training set"""
    X, y = training_set()
    dw, db = gradient(X, y, np.zeros(X.shape[1]), 0.0)
    expected_dw, expected_db = numerical_gradient(X, y, np.zeros(X.shape[1]), 0.0, 0.0)
    assert np.shape(dw) == (X.shape[1],)
    assert np.shape(db) == ()
    assert dw == pytest.approx(expected_dw, abs=1e-6)
    assert db == pytest.approx(expected_db, abs=1e-6)


@pytest.mark.id("tst_1jt71h")
def test_l2_term():
    """The l2 term changes the weights' slopes, not the bias's"""
    X, y = np.zeros((2, 2)), np.array([1.0, 0.0])
    dw, db = gradient(X, y, np.array([2.0, -4.0]), 1.0, 0.5)
    assert dw == pytest.approx([1.0, -2.0], rel=1e-12)
    assert db == pytest.approx(expected_sigmoid(1.0) - 0.5, rel=1e-12)
