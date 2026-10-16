import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import TargetEncoder

from encoding import cross_fit, encode


@pytest.fixture(scope="module")
def pairs():
    calls = pd.read_csv("data/calls.csv")
    calls = calls.assign(pair=calls["job"] + "/" + calls["education"])
    return (
        calls[calls["set"] == 0].reset_index(drop=True),
        calls[calls["set"] == 1].reset_index(drop=True),
    )


def said_yes(calls):
    return (calls["subscribed"] == "yes").to_numpy(dtype=int)


@pytest.mark.id("tst_xkdpeh")
def test_by_hand():
    """Four calls by hand"""
    found = encode(
        pd.Series(["a", "a", "b", "c"]),
        np.array([1, 0, 1, 0]),
        pd.Series(["a", "b", "c", "d"]),
        2,
    )
    np.testing.assert_allclose(found, [0.5, 2 / 3, 1 / 3, 0.5])


@pytest.mark.id("tst_35jd08")
def test_target_encoder(pairs):
    """Encodings as scikit-learn's TargetEncoder learns them"""
    train, validation = pairs
    for smooth in [0, 10, 100]:
        encoder = TargetEncoder(smooth=smooth, target_type="binary")
        encoder.fit(train[["pair"]], said_yes(train))
        wanted = encoder.transform(validation[["pair"]])[:, 0]
        found = encode(train["pair"], said_yes(train), validation["pair"], smooth)
        np.testing.assert_allclose(found, wanted, rtol=0, atol=1e-12)


@pytest.mark.id("tst_e9lhag")
def test_cross_fit(pairs):
    """Cross-fitted as TargetEncoder's fit_transform"""
    train, _ = pairs
    y = said_yes(train)
    for seed in [0, 1]:
        folds = StratifiedKFold(5, shuffle=True, random_state=seed)
        splits = list(folds.split(train[["pair"]], y))
        encoder = TargetEncoder(
            smooth=10, target_type="binary", shuffle=True, random_state=seed
        )
        wanted = encoder.fit_transform(train[["pair"]], y)[:, 0]
        found = cross_fit(train["pair"], y, splits, 10)
        np.testing.assert_allclose(found, wanted, rtol=0, atol=1e-12)


@pytest.mark.id("tst_0mtbql")
def test_own_answer(pairs):
    """No call's own answer in its encoding"""
    train, _ = pairs
    y = said_yes(train)
    splits = list(StratifiedKFold(5, shuffle=True, random_state=0).split(train, y))
    before = cross_fit(train["pair"], y, splits, 10)
    for call in [0, 1, 2, 3, 4]:
        flipped = y.copy()
        flipped[call] = 1 - flipped[call]
        after = cross_fit(train["pair"], flipped, splits, 10)
        assert after[call] == before[call]
