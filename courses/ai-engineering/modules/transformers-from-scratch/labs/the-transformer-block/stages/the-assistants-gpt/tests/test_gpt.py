import pytest
import torch
import torch.nn.functional as F

from gpt import AppGPT


def model():
    torch.manual_seed(0)
    return AppGPT(256, 32, 32, 2, 4)


def tokens(length):
    return torch.randint(
        0, 256, (2, length), generator=torch.Generator().manual_seed(1)
    )


@pytest.mark.id("tst_rql3qo")
def test_shape():
    """Logits for every token"""
    assert model()(tokens(9)).shape == (2, 9, 256)


@pytest.mark.id("tst_o3ys5v")
@torch.no_grad()
def test_causal():
    """No token's logits see a later token"""
    gpt, story = model(), tokens(8)
    logits = gpt(story)
    changed = story.clone()
    changed[:, -1] = (changed[:, -1] + 1) % 256
    assert torch.equal(gpt(changed)[:, :-1], logits[:, :-1])


@pytest.mark.id("tst_89j7ac")
def test_head_starts_from_the_embeddings():
    """The output layer starts from the token embeddings"""
    gpt = model()
    assert torch.equal(gpt.head.weight, gpt.wte.weight)


@pytest.mark.id("tst_zbhfp0")
def test_learns():
    """A step of AdamW lowers the loss on a batch"""
    gpt, story = model(), tokens(16)
    optimizer = torch.optim.AdamW(gpt.parameters(), lr=1e-3)
    losses = []
    for _ in range(2):
        logits = gpt(story[:, :-1])
        loss = F.cross_entropy(logits.flatten(0, 1), story[:, 1:].flatten())
        losses.append(loss.item())
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    assert losses[1] < losses[0]
