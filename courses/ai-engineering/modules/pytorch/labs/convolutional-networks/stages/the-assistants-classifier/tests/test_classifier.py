import pytest
import torch

from classifier import Classifier, classify, fit
from photos import photos


def shop(count):
    images, labels = photos("train")
    return images[:count], labels[:count]


@pytest.mark.id("tst_owl8iq")
def test_shapes():
    """A logit for each kind"""
    images, _ = shop(4)
    assert Classifier()(images).shape == (4, 10)


@pytest.mark.id("tst_gosm7p")
def test_classify():
    """A kind and its probabilities for each photo"""
    images, _ = shop(16)
    kinds, probabilities = classify(Classifier(), images)
    assert kinds.shape == (16,) and probabilities.shape == (16, 10)
    assert torch.allclose(probabilities.sum(dim=1), torch.ones(16))
    assert torch.equal(kinds, probabilities.argmax(dim=1))


@pytest.mark.id("tst_fvk9vv")
def test_learns(monkeypatch):
    """It learns the photos it trains on"""
    # On some machines, the process ends at PyTorch's first bfloat16 matrix multiply, which
    # oneDNN runs. With oneDNN off, PyTorch runs bfloat16 in its own kernels.
    monkeypatch.setattr(torch.backends.mkldnn, "enabled", False)
    images, labels = shop(512)
    torch.manual_seed(0)
    losses = fit(Classifier(), images, labels, epochs=3, seed=0)
    assert len(losses) == 3 and losses[-1] < losses[0]
