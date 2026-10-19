import json
from pathlib import Path

import pytest
import torch

from batch import stories
from cache import END
from smollm import SmolLM, smollm

STORIES = json.loads(Path("references/stories.json").read_text())["stories"]


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


@pytest.mark.id("tst_dyipp1")
def test_two_stories():
    """Two stories of different lengths at once, each as it goes alone"""
    found = stories(smollm(), [STORIES[0]["prompt"], STORIES[2]["prompt"]], 5)
    assert found == [STORIES[0]["written"][:5], STORIES[2]["written"][:5]]


@pytest.mark.id("tst_ylip9t")
def test_end():
    """Each story ends with END, or after steps tokens"""
    model = tiny()
    assert stories(model, [[3], [2, 1], [1, 1, 3]], 4) == [[END], [1, 1, 1, 1], [END]]
    assert stories(model, [[2, 1]], 0) == [[]]
