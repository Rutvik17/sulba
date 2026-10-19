import pytest
import torch

from cache import Cache
from generator import step, story
from smollm import smollm

# The app's opening line, "Once upon a time, there was a little girl named Lily."
OPENING = [6403, 1980, 253, 655, 28, 665, 436, 253, 1838, 8180, 3365, 14176, 30]


@pytest.fixture(scope="module")
def model():
    return smollm()


@pytest.mark.id("tst_exvu1o")
def test_logits(model):
    """A logit for every token in the vocabulary"""
    with torch.no_grad():
        logits = step(model, torch.tensor(OPENING), Cache(30))
    assert logits.shape == (len(OPENING), 49152)
    assert torch.isfinite(logits).all()


@pytest.mark.id("tst_janl6e")
def test_cache_grows(model):
    """The cache holds every token read"""
    cache = Cache(30)
    with torch.no_grad():
        step(model, torch.tensor(OPENING), cache)
        step(model, torch.tensor([401]), cache)
    assert len(cache) == len(OPENING) + 1
    assert cache.keys[29].shape == (3, len(OPENING) + 1, 64)


@pytest.mark.id("tst_g2sn89")
def test_story(model):
    """A story of the length asked for"""
    written = story(model, OPENING, 3)
    assert len(written) == 3
    assert all(0 <= token < 49152 for token in written)
