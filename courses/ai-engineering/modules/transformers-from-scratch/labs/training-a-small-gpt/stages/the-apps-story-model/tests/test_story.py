import pytest
import torch

from story import fit, make
from train import GPT


@pytest.mark.id("tst_k6yhlp")
def test_make():
    """A GPT for the stories' vocabulary"""
    model = make()
    assert isinstance(model, GPT)
    assert model.wte.num_embeddings == 2048
    tokens = torch.randint(2048, (2, model.context))
    with torch.no_grad():
        assert model(tokens).shape == (2, model.context, 2048)


@pytest.mark.id("tst_rbjmgx")
def test_fit():
    """It trains the model it's given, and returns it"""
    torch.manual_seed(0)
    model = GPT(2048, 16, 16, 1, 1)
    before = [param.detach().clone() for param in model.parameters()]
    tokens = torch.randint(2048, (20_000,))
    assert fit(model, tokens, torch.Generator().manual_seed(0)) is model
    assert any(
        not torch.equal(param, start)
        for param, start in zip(model.parameters(), before, strict=True)
    )
