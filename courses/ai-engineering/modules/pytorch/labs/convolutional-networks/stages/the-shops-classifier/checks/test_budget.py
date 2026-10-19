import copy
import functools

import pytest
import torch
from torch import nn

from photos import photos
from shop import fit, make

BUDGET, EPOCHS, TARGET = 1_500_000, 3, 0.9


def multiply_adds(net):
    """The multiply-adds a forward pass of one photo takes in net's convolutions and linear
    layers, counted on a copy on the meta device."""
    total = 0

    def count(module, inputs, output):
        nonlocal total
        if isinstance(module, nn.Conv2d):
            kh, kw = module.kernel_size
            total += output.numel() * module.in_channels // module.groups * kh * kw
        elif isinstance(module, nn.Linear):
            total += output.numel() * module.in_features

    shadow = copy.deepcopy(net).to("meta").eval()
    for module in shadow.modules():
        module.register_forward_hook(count)
    shadow(torch.zeros(1, 1, 28, 28, device="meta"))
    return total


class Seen:
    """Counts the photos that go through a network in training mode while it's open."""

    def __init__(self, net):
        self.net = net

    def __enter__(self):
        self.count = 0
        self.hook = self.net.register_forward_pre_hook(self.see)
        return self

    def see(self, module, inputs):
        if module.training:
            self.count += len(inputs[0])

    def __exit__(self, *exception):
        self.hook.remove()


@functools.cache
def trained():
    """The classifier fit gives from seed 0 on every training photo, and how many photos
    went through it in training."""
    images, labels = photos("train")
    torch.manual_seed(0)
    net = make()
    with Seen(net) as seen:
        returned = fit(net, images, labels, seed=0)
    return returned, seen.count


def same(first, second):
    first, second = first.state_dict(), second.state_dict()
    return first.keys() == second.keys() and all(
        torch.equal(first[name], tensor) for name, tensor in second.items()
    )


@pytest.mark.id("tst_m5wdy2")
def test_budget(record_property):
    """At most the shop's multiply-adds a photo"""
    count = multiply_adds(make())
    record_property("note", f"It takes {count:,} multiply-adds a photo.")
    assert count <= BUDGET


@pytest.mark.id("tst_8e4fdj")
def test_target(record_property):
    """The shop's share of the test photos"""
    net, _ = trained()
    images, labels = photos("test")
    with torch.no_grad():
        right = sum(
            int((net(X).argmax(dim=1) == y).sum())
            for X, y in zip(images.split(1_000), labels.split(1_000), strict=True)
        )
    record_property(
        "note", f"It read {right:,} of the {len(labels):,} test photos right."
    )
    assert right >= TARGET * len(labels)


@pytest.mark.id("tst_1g4p37")
def test_epochs(record_property):
    """Within the shop's epochs"""
    _, seen = trained()
    images, _ = photos("train")
    record_property("note", f"It trained on {seen / len(images):.2f} epochs of photos.")
    assert seen <= EPOCHS * len(images)


@pytest.mark.id("tst_k17yx8")
def test_seed():
    """The seed decides the classifier"""
    images, labels = photos("train")
    nets = []
    for seed in (0, 0, 1):
        torch.manual_seed(0)
        nets.append(fit(make(), images[:2_000], labels[:2_000], seed=seed))
    assert same(nets[0], nets[1])
    assert not same(nets[0], nets[2])


@pytest.mark.id("tst_209ta9")
def test_alone():
    """A photo classified alone as among others"""
    net, _ = trained()
    images, _ = photos("test")
    with torch.no_grad():
        together = net(images[:100])
        alone = torch.cat([net(images[i : i + 1]) for i in range(100)])
    assert torch.allclose(alone, together, rtol=1e-4, atol=1e-5)
