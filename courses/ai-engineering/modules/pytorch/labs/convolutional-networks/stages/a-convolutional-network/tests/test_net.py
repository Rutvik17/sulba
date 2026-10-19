import copy
import functools

import pytest
import torch
import torch.nn.functional as F
from torch import nn

from net import BATCH, LR, MOMENTUM, Net, multiply_adds, predict, train
from photos import photos

# Your code may sum in another order than these tests do, and training carries any
# difference from step to step.
RTOL, ATOL = 1e-4, 1e-5


@functools.cache
def shop(part, count):
    """The first count photos of part, and their kinds."""
    images, labels = photos(part)
    return images[:count].clone(), labels[:count].clone()


def started(seed=0):
    torch.manual_seed(seed)
    return Net()


def reference(images, labels, epochs, seed, dtype=None):
    """The network the shop's training gives, from the same start as started()."""
    net = started()
    optimizer = torch.optim.SGD(net.parameters(), lr=LR, momentum=MOMENTUM)
    generator = torch.Generator().manual_seed(seed)
    losses = []
    for _ in range(epochs):
        total = 0.0
        for batch in torch.randperm(len(images), generator=generator).split(BATCH):
            with torch.autocast("cpu", dtype=dtype, enabled=dtype is not None):
                loss = F.cross_entropy(net(images[batch]), labels[batch])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(batch)
        losses.append(total / len(images))
    return net, losses


def close(found, expected):
    found, expected = found.state_dict(), expected.state_dict()
    return found.keys() == expected.keys() and all(
        torch.allclose(found[name], tensor, rtol=RTOL, atol=ATOL)
        for name, tensor in expected.items()
    )


class Outputs:
    """The dtypes of the outputs of a network's convolutions and linear layers while it's
    open."""

    def __init__(self, net):
        self.net = net

    def __enter__(self):
        self.dtypes = set()
        self.hooks = [
            module.register_forward_hook(self.record)
            for module in self.net.modules()
            if isinstance(module, (nn.Conv2d, nn.Linear))
        ]
        return self

    def record(self, module, inputs, output):
        self.dtypes.add(output.dtype)

    def __exit__(self, *exception):
        for hook in self.hooks:
            hook.remove()


@pytest.mark.id("tst_lvpsri")
def test_net():
    """The shop's network, layer by layer"""
    net = Net()
    shapes = {name: tuple(param.shape) for name, param in net.named_parameters()}
    assert shapes == {
        "features.0.weight": (16, 1, 3, 3),
        "features.0.bias": (16,),
        "features.3.weight": (32, 16, 3, 3),
        "features.3.bias": (32,),
        "classifier.1.weight": (10, 1568),
        "classifier.1.bias": (10,),
    }
    images, _ = shop("test", 64)
    with torch.no_grad():
        assert net.features(images).shape == (64, 32, 7, 7)
        assert net(images).shape == (64, 10)


@pytest.mark.id("tst_ld2s2x")
def test_multiply_adds():
    """Multiply-adds per photo"""
    assert multiply_adds(Net()) == 1_031_744
    net = nn.Sequential(
        nn.Conv2d(3, 8, (3, 5), stride=2, padding=1, dilation=(2, 1)),
        nn.ReLU(),
        nn.Conv2d(8, 16, 3, padding=1, groups=4),
        nn.MaxPool2d(2),
        nn.Flatten(),
        nn.Linear(16 * 4 * 4, 5),
    )
    # A 20 by 18 photo gives 9 by 8 outputs of 3 by 3 by 5 weights from the first layer,
    # then 9 by 8 outputs of 2 channels by 3 by 3 weights from the second.
    expected = 9 * 8 * 8 * (3 * 3 * 5) + 9 * 8 * 16 * (2 * 3 * 3) + 5 * 256
    assert multiply_adds(net, (3, 20, 18)) == expected


@pytest.mark.id("tst_w6vqn9")
def test_counting_changes_nothing():
    """Counting leaves the network as it was"""
    net = nn.Sequential(
        nn.Conv2d(1, 4, 3, padding=1),
        nn.BatchNorm2d(4),
        nn.Flatten(),
        nn.Linear(4 * 28 * 28, 10),
    )
    before = copy.deepcopy(net.state_dict())
    assert multiply_adds(net) == 28 * 28 * 4 * 9 + 10 * 4 * 28 * 28
    assert net.training
    state = net.state_dict()
    assert all(
        state[name].device.type == "cpu" and torch.equal(state[name], tensor)
        for name, tensor in before.items()
    )


@pytest.mark.id("tst_gp8tp5")
def test_train():
    """Training, batch by batch as the shop trains"""
    images, labels = shop("train", 2_000)
    net = started()
    losses = train(net, images, labels, epochs=2, seed=3)
    expected, expected_losses = reference(images, labels, epochs=2, seed=3)
    assert close(net, expected)
    assert len(losses) == 2 and all(isinstance(loss, float) for loss in losses)
    assert losses == pytest.approx(expected_losses, rel=RTOL)
    assert losses[1] < losses[0]
    other = started()
    train(other, images, labels, epochs=1, seed=4)
    assert not close(other, reference(images, labels, epochs=1, seed=3)[0])


@pytest.mark.id("tst_t0zb5i")
def test_bfloat16(monkeypatch):
    """Training in bfloat16 under autocast"""
    # On some machines, the process ends at PyTorch's first bfloat16 matrix multiply, which
    # oneDNN runs. With oneDNN off, PyTorch runs bfloat16 in its own kernels.
    monkeypatch.setattr(torch.backends.mkldnn, "enabled", False)
    images, labels = shop("train", 1_000)
    net = started()
    with Outputs(net) as outputs:
        train(net, images, labels, seed=5, dtype=torch.bfloat16)
    assert outputs.dtypes == {torch.bfloat16}
    assert all(param.dtype == torch.float32 for param in net.parameters())
    assert close(
        net, reference(images, labels, epochs=1, seed=5, dtype=torch.bfloat16)[0]
    )
    plain = started()
    with Outputs(plain) as outputs:
        train(plain, images, labels, seed=5)
    assert outputs.dtypes == {torch.float32}


@pytest.mark.id("tst_ptahuy")
def test_predict():
    """Predictions in evaluation mode, without gradients"""
    images, _ = shop("test", 2_500)
    torch.manual_seed(6)
    net = nn.Sequential(
        nn.Conv2d(1, 4, 3), nn.BatchNorm2d(4), nn.Flatten(), nn.Linear(4 * 26 * 26, 10)
    )
    kinds = predict(net, images, batch=1_000)
    assert not net.training
    # In evaluation mode, the norm reads its running estimates and leaves them alone.
    assert torch.equal(net[1].running_mean, torch.zeros(4))
    assert kinds.dtype == torch.int64 and not kinds.requires_grad
    with torch.no_grad():
        expected = torch.cat([net(X).argmax(dim=1) for X in images.split(1_000)])
    assert torch.equal(kinds, expected)


@pytest.mark.id("tst_2jjoky")
def test_any_device():
    """Predictions on the device they're asked for"""
    images, _ = shop("test", 2_500)
    # The meta device holds shapes and dtypes but no data: a tensor made on the CPU by
    # mistake can't meet it.
    kinds = predict(Net(), images, "meta", batch=1_000)
    assert kinds.device.type == "meta"
    assert kinds.shape == (2_500,) and kinds.dtype == torch.int64
