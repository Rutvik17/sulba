import pytest
import torch

from gpt2 import GPT
from loader import decode, encode, model, tokenizer

STORY = "Once upon a time, there was a little girl named Lily."


@pytest.fixture(scope="module")
def gpt2():
    return model("data")


@pytest.fixture(scope="module")
def tokens():
    return tokenizer("data")


@pytest.mark.id("tst_eyzbmk")
def test_model(gpt2):
    """GPT-2 small's shapes, in evaluation mode"""
    assert isinstance(gpt2, GPT)
    assert not gpt2.training
    assert gpt2.wte.weight.shape == (50257, 768)
    assert gpt2.blocks[11].mlp.fc.weight.shape == (3072, 768)


@pytest.mark.id("tst_z50s32")
def test_logits(gpt2, tokens):
    """A logit for every token in the vocabulary, each a number"""
    with torch.no_grad():
        logits = gpt2(torch.tensor([encode(STORY, tokens)]))
    assert logits.shape[-1] == 50257
    assert torch.isfinite(logits).all()


@pytest.mark.id("tst_cwj902")
def test_encode(tokens):
    """A story's first tokens, as GPT-2's tokenizer gives them"""
    assert encode(STORY, tokens)[:4] == [7454, 2402, 257, 640]


@pytest.mark.id("tst_ke74ab")
def test_round_trip(tokens):
    """A story back from its tokens"""
    assert STORY in decode(encode(STORY, tokens), tokens)
