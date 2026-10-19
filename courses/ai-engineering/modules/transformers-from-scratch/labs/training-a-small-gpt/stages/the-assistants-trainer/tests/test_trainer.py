import pytest
import torch

from tokenizer import decode, stories, train
from train import GPT
from trainer import batch, corpus, learning_rate, write

FILE = "data/TinyStoriesV2-GPT4-valid.txt"


@pytest.mark.id("tst_48peal")
def test_corpus():
    """Every story's text, in order"""
    told = stories(FILE)[:50]
    merges = train(told, 300)
    text = decode(corpus(told, merges).tolist(), merges)
    at = 0
    for story in told:
        at = text.index(story, at) + len(story)


@pytest.mark.id("tst_w5ii03")
def test_batch():
    """Windows of the stream, with their targets"""
    inputs, targets = batch(torch.arange(500), 16, 8, torch.Generator().manual_seed(0))
    assert inputs.shape == targets.shape == (8, 16)
    assert torch.equal(inputs, inputs[:, :1] + torch.arange(16))


@pytest.mark.id("tst_1mwmok")
def test_learning_rate():
    """Up to the peak over the warm-up, then down"""
    assert learning_rate(0, 1000, 1e-3, 10) == pytest.approx(1e-4)
    assert learning_rate(9, 1000, 1e-3, 10) == pytest.approx(1e-3)
    assert learning_rate(10, 1000, 1e-3, 10) == pytest.approx(1e-3)
    assert learning_rate(100, 1000, 1e-3, 10) < 1e-3


@pytest.mark.id("tst_2lxfwp")
def test_write():
    """New tokens from the vocabulary"""
    torch.manual_seed(0)
    model = GPT(64, 16, 32, 2, 2)
    written = write(model, [1, 2, 3], 5, torch.Generator().manual_seed(1))
    assert written[:3] == [1, 2, 3]
    assert 3 < len(written) <= 8
    assert all(0 <= token < 64 for token in written)
