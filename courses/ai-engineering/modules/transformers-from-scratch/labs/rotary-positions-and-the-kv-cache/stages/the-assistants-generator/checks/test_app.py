import pytest
import torch

from cache import END
from generator import allowed, positions, shared, story
from smollm import SmolLM


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


@pytest.mark.id("tst_phrpbm")
def test_positions():
    """New tokens' positions follow the cache's"""
    assert positions(0, 4).tolist() == [0, 1, 2, 3]
    assert positions(13, 1).tolist() == [13]
    assert positions(7, 3).tolist() == [7, 8, 9]


@pytest.mark.id("tst_ip3snc")
def test_shared():
    """Each query head reads its own group's key head"""
    heads = torch.arange(3 * 2 * 4.0).view(3, 2, 4)
    found = shared(heads, 3)
    assert found.shape == (9, 2, 4)
    for query in range(9):
        assert torch.equal(found[query], heads[query // 3])


@pytest.mark.id("tst_9jiu3b")
def test_allowed():
    """Each new token reads every cached token and the new ones up to itself"""
    assert allowed(0, 3).tolist() == [
        [True, False, False],
        [True, True, False],
        [True, True, True],
    ]
    assert allowed(4, 1).tolist() == [[True] * 5]
    assert allowed(3, 2).tolist() == [
        [True, True, True, True, False],
        [True, True, True, True, True],
    ]


@pytest.mark.id("tst_rccuzi")
def test_after_the_prompt():
    """A story goes on from the prompt's last token"""
    model = tiny()
    assert story(model, [3, 1], 3) == [1, 1, 1]
    assert story(model, [1, 3], 3) == [END]
