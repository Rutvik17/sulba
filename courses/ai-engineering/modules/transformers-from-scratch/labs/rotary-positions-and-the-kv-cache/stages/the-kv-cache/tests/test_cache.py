import json
from pathlib import Path

import pytest
import torch

from cache import END, Cache, generate, step
from rope import rotate
from smollm import THETA, SmolLM, smollm

STORIES = json.loads(Path("references/stories.json").read_text())


@pytest.fixture(scope="module")
def model():
    return smollm()


def tiny():
    """A SmolLM whose blocks add nothing, so each token predicts the token whose embedding
    lies closest to its own: END after token 3, and token 1 after itself."""
    model = SmolLM(vocab=5, width=8, hidden=8, layers=1, heads=2, kv_heads=1)
    with torch.no_grad():
        for parameter in model.layers.parameters():
            parameter.zero_()
        embeddings = torch.zeros(5, 8)
        embeddings[0, 0] = 3
        embeddings[1, 2] = 1
        embeddings[2, 3] = 1
        embeddings[3, :2] = 1
        embeddings[4, 4] = 1
        model.embed_tokens.weight.copy_(embeddings)
    return model.eval()


@pytest.mark.id("tst_j0srce")
def test_full_pass(model):
    """Logits as the full pass gives them, read in pieces of any length"""
    double = model.double()
    tokens = torch.tensor(
        STORIES["stories"][2]["prompt"] + STORIES["stories"][2]["written"]
    )
    cache = Cache(len(double.layers))
    with torch.no_grad():
        expected = double(tokens[None, :12])[0]
        found = torch.cat(
            [
                step(double, tokens[a:b], cache)
                for a, b in [(0, 5), (5, 6), (6, 10), (10, 12)]
            ]
        )
    model.float()
    assert torch.allclose(found, expected, rtol=1e-9, atol=1e-9)


@pytest.mark.id("tst_tk4kyz")
def test_cache(model):
    """Every token's keys, rotated by its position, and its values"""
    tokens = torch.tensor(STORIES["stories"][0]["prompt"])
    cache = Cache(len(model.layers))
    with torch.no_grad():
        step(model, tokens[:4], cache)
        step(model, tokens[4:], cache)
        layer = model.layers[0]
        h = layer.input_layernorm(model.embed_tokens(tokens))
        keys = layer.self_attn.k_proj(h).view(len(tokens), 3, 64).transpose(0, 1)
        values = layer.self_attn.v_proj(h).view(len(tokens), 3, 64).transpose(0, 1)
    assert len(cache) == len(tokens)
    assert cache.keys[29].shape == cache.values[29].shape == (3, len(tokens), 64)
    expected = rotate(keys, torch.arange(len(tokens)), THETA)
    assert torch.allclose(cache.keys[0], expected, rtol=1e-5, atol=1e-5)
    assert torch.allclose(cache.values[0], values, rtol=1e-5, atol=1e-5)


@pytest.mark.id("tst_ptykqv")
def test_stories(model):
    """SmolLM2's stories, as transformers writes them"""
    for story in STORIES["stories"]:
        assert generate(model, story["prompt"], STORIES["steps"]) == story["written"]


@pytest.mark.id("tst_27w9kd")
def test_end():
    """A story ends with END, or after steps tokens"""
    model = tiny()
    assert generate(model, [3], 5) == [END]
    assert generate(model, [2, 1], 4) == [1, 1, 1, 1]
    assert generate(model, [1], 0) == []
