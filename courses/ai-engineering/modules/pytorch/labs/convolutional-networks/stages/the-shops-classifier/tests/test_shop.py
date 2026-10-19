import copy

import pytest
import torch

from photos import photos
from shop import fit, make


@pytest.mark.id("tst_y9jagn")
def test_logits():
    """A logit for each kind"""
    images, _ = photos("test")
    with torch.no_grad():
        assert make()(images[:8]).shape == (8, 10)


@pytest.mark.id("tst_0qw402")
def test_fit():
    """It trains, and returns the network"""
    images, labels = photos("train")
    torch.manual_seed(0)
    net = make()
    before = copy.deepcopy(net.state_dict())
    assert fit(net, images[:512], labels[:512], seed=0) is net
    state = net.state_dict()
    assert any(not torch.equal(state[name], tensor) for name, tensor in before.items())
