import numpy as np
import pandas as pd
import pytest

from sorter import MEASUREMENTS, Line


@pytest.fixture(scope="module")
def beans():
    table = pd.read_csv("data/beans.csv")
    train, test = table[table["set"] == 0], table[table["set"] == 2]
    return (
        train[MEASUREMENTS].to_numpy(),
        train["variety"].to_numpy(),
        test[MEASUREMENTS].to_numpy(),
    )


@pytest.fixture(scope="module")
def line(beans):
    train, varieties, _ = beans
    return Line(train, varieties, 12)


@pytest.mark.id("tst_33jj2c")
def test_by_hand():
    """A split vote, a clear one and a bean out of reach, worked by hand"""
    train = np.array([[0.0], [1.0], [2.0], [10.0], [11.0], [12.0]])
    varieties = np.array(["SIRA", "SIRA", "CALI", "CALI", "SIRA", "CALI"])
    batch = np.array([[1.5], [11.2], [6.0]])
    assert list(Line(train, varieties, 4).sort(batch)) == ["UNSURE", "CALI", "UNKNOWN"]


@pytest.mark.id("tst_e8919f")
def test_at_the_reach():
    """A bean as far as the reach named, one farther out of reach"""
    train, varieties = np.array([[-1.0], [1.0]]), np.array(["SIRA", "CALI"])
    named = Line(train, varieties, 1).sort(np.array([[3.0], [3.5]]))
    assert list(named) == ["CALI", "UNKNOWN"]


@pytest.mark.id("tst_uh5194")
def test_alone(beans, line):
    """Each bean named as it is alone"""
    _, _, test = beans
    alone = [line.sort(test[i : i + 1])[0] for i in range(20)]
    assert list(line.sort(test[:20])) == alone


@pytest.mark.id("tst_cbb0oj")
def test_unchanged(beans, line):
    """The arrays given left as they were"""
    table = pd.read_csv("data/beans.csv")
    train, test = table[table["set"] == 0], table[table["set"] == 2]
    line.sort(beans[2][:20])
    np.testing.assert_array_equal(beans[0], train[MEASUREMENTS].to_numpy())
    np.testing.assert_array_equal(beans[1], train["variety"].to_numpy())
    np.testing.assert_array_equal(beans[2], test[MEASUREMENTS].to_numpy())
