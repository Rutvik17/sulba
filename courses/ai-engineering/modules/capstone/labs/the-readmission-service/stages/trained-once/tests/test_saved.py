import numpy
import pytest
import scipy
import sklearn

import train
from features import features, stays


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    """The model trained on the extract's first 2,000 encounters."""
    path = tmp_path_factory.mktemp("extract") / "encounters.csv"
    with open("data/encounters.csv") as extract:
        path.write_text("".join(next(extract) for _ in range(2001)))
    return train.train(path)


@pytest.fixture(scope="module")
def rows():
    return features(stays("data/encounters.csv").head(20))


@pytest.mark.id("tst_iaula9")
def test_versions():
    """Gives the versions of scikit-learn, NumPy and SciPy running"""
    assert train.versions() == {
        "scikit-learn": sklearn.__version__,
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
    }


@pytest.mark.id("tst_fxuy6v")
def test_round_trip(trained, rows, tmp_path):
    """Loads the model it saved, with its threshold, recall and precision"""
    path = tmp_path / "model.joblib"
    train.save(trained, path)
    loaded = train.load(path)
    assert set(loaded) == set(trained)
    assert loaded["model"] is not trained["model"]
    assert (
        loaded["model"].predict_proba(rows) == trained["model"].predict_proba(rows)
    ).all()
    for name in ("threshold", "recall", "precision"):
        assert loaded[name] == trained[name]


@pytest.mark.id("tst_5ykptu")
def test_other_versions_refused(trained, tmp_path, monkeypatch):
    """Refuses a model trained with other versions"""
    path = tmp_path / "model.joblib"
    train.save(trained, path)
    running = train.versions()
    monkeypatch.setattr(train, "versions", lambda: {**running, "scikit-learn": "1.0.0"})
    with pytest.raises(ValueError):
        train.load(path)


@pytest.mark.id("tst_wzu1tx")
def test_trained_untouched(trained, tmp_path):
    """Leaves what it saves as it was"""
    before = dict(trained)
    train.save(trained, tmp_path / "model.joblib")
    assert trained == before


@pytest.mark.id("tst_eilw0y")
def test_model_path(trained, rows, tmp_path, monkeypatch):
    """Saves to MODEL_PATH and loads from it unless told otherwise"""
    monkeypatch.chdir(tmp_path)
    train.save(trained)
    assert (tmp_path / train.MODEL_PATH).exists()
    loaded = train.load()
    assert (
        loaded["model"].predict_proba(rows) == trained["model"].predict_proba(rows)
    ).all()
