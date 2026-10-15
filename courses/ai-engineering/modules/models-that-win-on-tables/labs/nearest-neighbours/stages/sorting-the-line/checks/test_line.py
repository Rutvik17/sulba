import numpy as np
import pandas as pd
import pytest

from sorter import MEASUREMENTS, Line

# The line's neighbours, and how much larger than a Bombay bean each stone is: its lengths
# 1.5 times as long, its areas 2.25 times as large.
K, LONGER = 12, 1.5
LENGTHS = ["Perimeter", "MajorAxisLength", "MinorAxisLength", "EquivDiameter"]
AREAS = ["Area", "ConvexArea"]


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    parts = [table[table["set"] == number] for number in (0, 1, 2)]
    return [
        (part[MEASUREMENTS].to_numpy(), part["variety"].to_numpy()) for part in parts
    ]


@pytest.fixture(scope="module")
def line(beans):
    (train, varieties), _, _ = beans
    return Line(train, varieties, K)


def stones(beans):
    """The test set's Bombay beans, grown into stones larger than any bean."""
    _, _, (test, truth) = beans
    grown = test[truth == "BOMBAY"].copy()
    for name in LENGTHS:
        grown[:, MEASUREMENTS.index(name)] *= LONGER
    for name in AREAS:
        grown[:, MEASUREMENTS.index(name)] *= LONGER**2
    return grown


@pytest.mark.id("tst_c8ufzz")
def test_a_stone(beans, line):
    """A stone on the line"""
    _, _, (test, _) = beans
    batch = np.vstack([test[:100], stones(beans)[:1]])
    assert line.sort(batch)[-1] == "UNKNOWN"


@pytest.mark.id("tst_3zkfah")
def test_stones(beans, line):
    """A batch of stones"""
    grown = stones(beans)
    assert list(line.sort(grown)) == ["UNKNOWN"] * len(grown)


@pytest.mark.id("tst_9zelch")
def test_split_votes(beans, line):
    """Split votes sent to a person"""
    (train, varieties), _, (test, _) = beans
    mean, sd = train.mean(axis=0), train.std(axis=0)
    a, b = (train - mean) / sd, (test - mean) / sd
    expected = []
    for bean in b:
        nearest = np.argsort(((a - bean) ** 2).sum(axis=1), kind="stable")[:K]
        names, counts = np.unique(varieties[nearest], return_counts=True)
        expected.append(names[counts.argmax()] if counts.max() * 2 > K else "UNSURE")
    assert "UNSURE" in expected
    assert list(line.sort(test)) == expected


@pytest.mark.id("tst_1ra17f")
def test_no_false_alarms(beans, line):
    """No bean taken for a stone"""
    _, (validation, _), _ = beans
    assert "UNKNOWN" not in list(line.sort(validation))
