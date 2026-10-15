import numpy as np
import pytest

from sampling import balanced_weights, reweighted_mean, weighted_choice


class Uniforms:
    """Stands in for a generator, giving set numbers from random()."""

    def __init__(self, numbers):
        self.numbers = np.array(numbers, dtype=float)

    def random(self, size=None):
        count = 1 if size is None else int(np.prod(size))
        taken, self.numbers = self.numbers[:count], self.numbers[count:]
        return taken[0] if size is None else taken.reshape(size)


@pytest.fixture(scope="module")
def labels():
    """The records' diagnoses."""
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    return table[table[:, 0] == 0, 1]


@pytest.mark.id("tst_o48nzq")
def test_by_hand():
    """Draws worked by hand, a row of weight 0 never among them"""
    uniforms = Uniforms([0.0, 0.1, 0.25, 0.5, 0.99])
    rows = weighted_choice(np.array([0.0, 1.0, 1.0, 2.0]), 5, uniforms)
    assert np.asarray(rows).tolist() == [1, 1, 2, 3, 3]


@pytest.mark.id("tst_97h2zf")
def test_same_as_numpy(labels):
    """The same draws as NumPy's Generator.choice, given the probabilities and the same seed"""
    n = len(labels)
    for weights in (
        np.where(labels == 1, 3.0, 1.0),
        np.random.default_rng(7).random(n),
    ):
        expected = np.random.default_rng(8).choice(n, 10_000, p=weights / weights.sum())
        found = weighted_choice(weights, 10_000, np.random.default_rng(8))
        assert np.array_equal(found, expected)


@pytest.mark.id("tst_lhyqyx")
def test_never_past_the_end():
    """Never past the last row, even when the weights' running total ends a little under 1"""
    largest = np.nextafter(1.0, 0.0)
    rows = weighted_choice(np.full(10, 0.1), 1, Uniforms([largest]))
    assert np.asarray(rows).tolist() == [9]
    rows = weighted_choice(np.array([1.0, 1.0, 0.0, 0.0]), 1, Uniforms([largest]))
    assert np.asarray(rows).tolist() == [1]


@pytest.mark.id("tst_wwhur4")
def test_balanced(labels):
    """Balanced weights give every class the same total, and batches half malignant"""
    found = balanced_weights(np.array([0.0, 0.0, 0.0, 1.0]))
    assert found == pytest.approx([1 / 3, 1 / 3, 1 / 3, 1])
    found = balanced_weights(np.array([2, 0, 2, 1, 2]))
    assert found == pytest.approx([1 / 3, 1, 1 / 3, 1, 1 / 3])
    weights = np.asarray(balanced_weights(labels))
    assert weights[labels == 1].sum() == pytest.approx(weights[labels == 0].sum())
    rows = np.random.default_rng(9).choice(
        len(labels), 20_000, p=weights / weights.sum()
    )
    assert abs(labels[rows].mean() - 0.5) < 4 * np.sqrt(0.25 / 20_000)


@pytest.mark.id("tst_1lh107")
def test_reweighted_mean(labels):
    """The reweighted mean worked by hand, and right on average over balanced batches"""
    values, weights = np.array([1.0, 2.0, 3.0, 6.0]), np.array([1.0, 1.0, 1.0, 3.0])
    assert reweighted_mean(values, np.array([3, 3, 0]), weights) == pytest.approx(2.5)
    batch = np.array([0, 2, 2])
    assert reweighted_mean(values, batch, np.ones(4)) == pytest.approx(
        values[batch].mean()
    )
    n = len(labels)
    weights = np.where(labels == 1, 1 / labels.sum(), 1 / (n - labels.sum()))
    rng = np.random.default_rng(10)
    batches = rng.choice(n, (2000, 32), p=weights / weights.sum())
    means = np.array([reweighted_mean(labels, batch, weights) for batch in batches])
    assert abs(means.mean() - labels.mean()) < 4 * means.std() / np.sqrt(len(means))
