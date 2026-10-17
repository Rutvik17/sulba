import pytest

from features import features, stays
from train import train


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    """The script run on the extract's first 2,000 encounters."""
    path = tmp_path_factory.mktemp("extract") / "encounters.csv"
    with open("data/encounters.csv") as extract:
        path.write_text("".join(next(extract) for _ in range(2001)))
    return train(path)


@pytest.mark.id("tst_rb2lh5")
def test_gives_what_the_service_needs(trained):
    """Gives the model, its threshold, and the recall and precision there"""
    assert set(trained) == {"model", "threshold", "recall", "precision"}


@pytest.mark.id("tst_77799v")
def test_threshold_is_a_probability(trained):
    """Sets the threshold at a probability"""
    assert 0 < trained["threshold"] < 1


@pytest.mark.id("tst_l46z9f")
def test_recall_and_precision_are_shares(trained):
    """Gives the recall and precision as shares"""
    assert 0 <= trained["recall"] <= 1
    assert 0 <= trained["precision"] <= 1


@pytest.mark.id("tst_llkqu2")
def test_model_answers(trained):
    """Gives a model that answers for each stay"""
    rows = stays("data/encounters.csv").head(5)
    probabilities = trained["model"].predict_proba(features(rows))[:, 1]
    assert probabilities.shape == (5,)
    assert all(0 <= p <= 1 for p in probabilities)
