import pytest
import torch
from torch import nn
from torch.optim.optimizer import register_optimizer_step_post_hook

from classifier import Classifier, classify, fit
from photos import photos

# The shop's design: a stem of 1 channel to 16, two blocks of 16 to 16 each with weights of
# its own, and a head from 16 channels of 7 by 7 to the kinds.
PARAMETERS = (16 * 9 + 2 * 16) + 2 * (16 * 16 * 9 + 2 * 16) + (16 * 7 * 7 * 10 + 10)


def shop(count):
    images, labels = photos("train")
    return images[:count], labels[:count]


@pytest.fixture
def own_kernels(monkeypatch):
    """On some machines, the process ends at PyTorch's first bfloat16 matrix multiply, which
    oneDNN runs. With oneDNN off, PyTorch runs bfloat16 in its own kernels."""
    monkeypatch.setattr(torch.backends.mkldnn, "enabled", False)


class Optimizers:
    """The optimizers that take a step while it's open."""

    def __enter__(self):
        self.seen = []
        self.hook = register_optimizer_step_post_hook(self.step)
        return self

    def step(self, optimizer, args, kwargs):
        if optimizer not in self.seen:
            self.seen.append(optimizer)

    def __exit__(self, *exception):
        self.hook.remove()


@pytest.mark.id("tst_shu6d1")
def test_design():
    """The network the shop designed"""
    net = Classifier()
    assert sum(param.numel() for param in net.parameters()) == PARAMETERS


@pytest.mark.id("tst_wi2gw6")
def test_logits():
    """Logits from the network, probabilities from classify"""
    images, _ = shop(32)
    net = Classifier().eval()
    linear = next(m for m in net.head.modules() if isinstance(m, nn.Linear))
    with torch.no_grad():
        linear.weight.zero_()
        linear.bias.copy_(torch.arange(10) / 4)
        scores = linear.bias.expand(32, 10)
        assert torch.equal(net(images), scores)
    _, probabilities = classify(net, images)
    assert torch.allclose(probabilities, torch.softmax(scores, dim=1))


@pytest.mark.id("tst_p9g8ml")
@pytest.mark.usefixtures("own_kernels")
def test_autocast():
    """Trained in bfloat16 under autocast, its weights kept in float32"""
    images, labels = shop(256)
    net = Classifier()
    dtypes = set()
    hooks = [
        module.register_forward_hook(lambda m, i, output: dtypes.add(output.dtype))
        for module in net.modules()
        if isinstance(module, nn.Conv2d)
    ]
    fit(net, images, labels, epochs=1, seed=0)
    for hook in hooks:
        hook.remove()
    assert dtypes == {torch.bfloat16}
    assert all(param.dtype == torch.float32 for param in net.parameters())


@pytest.mark.id("tst_8x2l6w")
@pytest.mark.usefixtures("own_kernels")
def test_every_layer():
    """Every layer trains"""
    images, labels = shop(256)
    net = Classifier()
    with Optimizers() as optimizers:
        fit(net, images, labels, epochs=1, seed=0)
    trained = {
        id(param)
        for optimizer in optimizers.seen
        for group in optimizer.param_groups
        for param in group["params"]
    }
    assert {id(param) for param in net.parameters()} <= trained
