import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans

from groups import (
    MEASUREMENTS,
    STARTS,
    fewest_groups,
    make_up,
    name_beans,
    named_groups,
    scale,
)


class Stub:
    """A model that puts the beans in these groups, whatever they are."""

    def __init__(self, groups):
        self.groups = np.array(groups)

    def predict(self, scaled):
        return self.groups[: len(scaled)]


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train = table[table["set"] == 0]
    harvest = table[table["set"] == 1]
    return (
        train[MEASUREMENTS].to_numpy(dtype=float),
        train["variety"].to_numpy(),
        harvest[MEASUREMENTS].to_numpy(dtype=float),
    )


def commonest(labels, varieties, k):
    return [
        pd.Series(varieties[labels == group]).value_counts().index[0]
        for group in range(k)
    ]


@pytest.mark.id("tst_e4rn0h")
def test_named_groups(beans):
    """Groups of the scaled beans, each named by its commonest variety"""
    X, varieties, _ = beans
    Z, _ = scale(X, X)
    wanted = KMeans(5, n_init=STARTS, random_state=3).fit(Z).labels_
    model, names = named_groups(X, varieties, 5, 3)
    assert model.labels_.tolist() == wanted.tolist()
    assert names == commonest(wanted, varieties, 5)


@pytest.mark.id("tst_3rgnvs")
def test_fewest_groups(beans):
    """The fewest groups whose names take in every variety"""
    X, varieties, _ = beans
    model, names = fewest_groups(X, varieties, 0)
    assert set(names) == set(varieties)
    Z, _ = scale(X, X)
    fewer = KMeans(model.n_clusters - 1, n_init=STARTS, random_state=0).fit(Z)
    assert set(commonest(fewer.labels_, varieties, model.n_clusters - 1)) != set(
        varieties
    )


@pytest.mark.id("tst_usb9qd")
def test_name_beans(beans):
    """Each bean named by its group"""
    X, _, V = beans
    names = ["SEKER", "SIRA", "HOROZ"]
    found = name_beans(Stub([2, 0, 0, 1]), names, X, V[:4])
    assert found.tolist() == ["HOROZ", "SEKER", "SEKER", "SIRA"]


@pytest.mark.id("tst_q2wzg9")
def test_make_up(beans):
    """Each name's share, by hand"""
    X, _, V = beans
    names = ["SIRA", "SEKER", "SIRA"]
    shares = make_up(Stub([0, 0, 1, 2]), names, X, V[:4])
    assert shares == {"SEKER": 0.25, "SIRA": 0.75}
    assert list(shares) == ["SEKER", "SIRA"]
