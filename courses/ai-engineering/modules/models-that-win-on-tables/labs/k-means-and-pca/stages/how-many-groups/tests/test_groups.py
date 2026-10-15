import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import silhouette_score

from groups import MEASUREMENTS, best_of, k_means, plus_plus, scale, silhouette

# Four rows on a line: two near 0 and two near 10.
LINE = np.array([[0.0], [1.0], [10.0], [12.0]])


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0][MEASUREMENTS].to_numpy(dtype=float)
    Z, _ = scale(train, train)
    return Z


@pytest.mark.id("tst_6hy83j")
def test_draws():
    """Each centre drawn as the brief describes"""
    draws = np.random.default_rng(5)
    first = LINE[draws.integers(len(LINE))]
    weights = ((LINE - first) ** 2).sum(axis=1)
    second = LINE[draws.choice(len(LINE), p=weights / weights.sum())]
    found = plus_plus(LINE, 2, np.random.default_rng(5))
    np.testing.assert_array_equal(found, [first, second])


@pytest.mark.id("tst_uvefb5")
def test_rows(beans):
    """Starting centres from the rows, none twice"""
    found = plus_plus(beans, 7, np.random.default_rng(3))
    rows = {tuple(row) for row in beans}
    assert found.shape == (7, len(MEASUREMENTS))
    assert all(tuple(centre) in rows for centre in found)
    assert len({tuple(centre) for centre in found}) == 7


@pytest.mark.id("tst_r9e648")
def test_best_of(beans):
    """The start with the least inertia, of several from one generator"""
    rng = np.random.default_rng(2)
    runs = [k_means(beans, plus_plus(beans, 4, rng)) for _ in range(3)]
    wanted = min(runs, key=lambda run: run[2])
    labels, centres, inertia = best_of(beans, 4, 3, np.random.default_rng(2))
    assert labels.tolist() == wanted[0].tolist()
    np.testing.assert_array_equal(centres, wanted[1])
    assert inertia == wanted[2]


@pytest.mark.id("tst_5snq3c")
def test_silhouette_by_hand():
    """The silhouette of four rows, by hand"""
    labels = np.array([0, 0, 1, 1])
    # Row 0: a = 1, b = (10 + 12) / 2 = 11. Row 1: a = 1, b = (9 + 11) / 2 = 10.
    # Row 2: a = 2, b = (10 + 9) / 2 = 9.5. Row 3: a = 2, b = (12 + 11) / 2 = 11.5.
    rows = [(11 - 1) / 11, (10 - 1) / 10, (9.5 - 2) / 9.5, (11.5 - 2) / 11.5]
    assert silhouette(LINE, labels) == pytest.approx(np.mean(rows))


@pytest.mark.id("tst_aou7z2")
def test_silhouette_beans(beans):
    """The beans' silhouette as scikit-learn gives it"""
    for k, seed in [(3, 0), (7, 1)]:
        labels, _, _ = best_of(beans, k, 1, np.random.default_rng(seed))
        wanted = silhouette_score(beans, labels)
        assert silhouette(beans, labels) == pytest.approx(wanted, rel=1e-9)
