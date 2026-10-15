import numpy as np
import pytest

from gradients import directional_slope, gradient_agrees


def bowl(x):
    """x₀² + 3x₁², with its minimum at 0."""
    return float(x[0] * x[0] + 3 * x[1] * x[1])


def bowl_gradient(x):
    return np.array([2 * x[0], 6 * x[1]])


@pytest.mark.id("tst_p2qw2z")
def test_slope_by_hand():
    """The slope along a direction, worked by hand"""
    x = np.array([1.0, 2.0])
    assert directional_slope(bowl, x, np.array([1.0, 0.0])) == pytest.approx(
        2, abs=1e-8
    )
    assert directional_slope(bowl, x, np.array([0.0, 1.0])) == pytest.approx(
        12, abs=1e-8
    )
    assert directional_slope(bowl, x, np.array([0.6, 0.8])) == pytest.approx(
        10.8, abs=1e-8
    )


@pytest.mark.id("tst_jx6r34")
def test_agrees_with_right_gradient():
    """Agrees with a right gradient"""
    x = np.array([1.0, 2.0])
    assert gradient_agrees(bowl, bowl_gradient, x, np.random.default_rng(0))


@pytest.mark.id("tst_dobdjj")
def test_disagrees_with_wrong_gradients():
    """Disagrees with a wrong gradient"""
    x = np.array([1.0, 2.0])
    for wrong in (lambda v: 2 * bowl_gradient(v), lambda v: -bowl_gradient(v)):
        assert not gradient_agrees(bowl, wrong, x, np.random.default_rng(0))


@pytest.mark.id("tst_zn6lmn")
def test_x_kept_and_answer():
    """Leaves x as it was, and answers True or False"""
    x = np.array([1.0, -2.0, 0.5])
    kept = x.copy()
    answer = gradient_agrees(
        lambda v: float(np.sum(v**4)), lambda v: 4 * v**3, x, np.random.default_rng(1)
    )
    assert np.array_equal(x, kept)
    assert answer is True or answer is np.True_
