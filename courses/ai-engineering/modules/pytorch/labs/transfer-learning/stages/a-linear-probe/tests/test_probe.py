import math

import pytest
import torch
import torch.nn.functional as F

from backbone import features, load
from probe import Probe, accuracy, confusion, fit_probe
from tiles import read, split


def blobs(seed):
    """Features of 3 kinds, 20 rows each, in 8 dimensions on different scales."""
    generator = torch.Generator().manual_seed(seed)
    centres = torch.randn(3, 8, generator=generator)
    kinds = torch.arange(3).repeat_interleave(20)
    noise = torch.randn(60, 8, generator=generator)
    scales = torch.logspace(-2, 2, 8)
    return ((centres[kinds] + noise) * scales).to(torch.float32), kinds


def by_hand():
    """A probe that gives the kind of each row's largest feature, and 10 rows, 8 of them
    given their own kind."""
    probe = Probe(torch.zeros(3), torch.ones(3), 3)
    with torch.no_grad():
        probe.linear.weight.copy_(torch.eye(3, dtype=torch.float64))
    rows = torch.eye(3)[[0, 0, 0, 1, 1, 1, 2, 2, 1, 0]]
    kinds = torch.tensor([0, 0, 0, 1, 1, 1, 2, 2, 2, 2])
    return probe, rows, kinds


@pytest.mark.id("tst_0efesm")
def test_standardized():
    """Features standardized by the labelled tiles' own means and deviations"""
    rows, kinds = blobs(0)
    probe = fit_probe(rows, kinds)
    assert probe.mean.dtype == torch.float64
    torch.testing.assert_close(probe.mean, rows.to(torch.float64).mean(0))
    torch.testing.assert_close(probe.std, rows.to(torch.float64).std(0))


@pytest.mark.id("tst_e9eucr")
def test_optimum():
    """The weights where cross-entropy plus the decay is lowest"""
    rows, kinds = blobs(1)
    for decay in (1e-3, 1e-1):
        probe = fit_probe(rows, kinds, decay)
        probe.zero_grad()
        loss = F.cross_entropy(probe(rows), kinds)
        loss = loss + decay * probe.linear.weight.square().sum()
        loss.backward()
        gradients = [parameter.grad for parameter in probe.parameters()]
        assert max(gradient.abs().max().item() for gradient in gradients) < 1e-4


@pytest.mark.id("tst_7hygo7")
def test_accuracy():
    """The share given right, with its standard error"""
    probe, rows, kinds = by_hand()
    share, error = accuracy(probe, rows, kinds)
    assert math.isclose(share, 0.8) and math.isclose(error, math.sqrt(0.8 * 0.2 / 10))


@pytest.mark.id("tst_3gcrke")
def test_confusion():
    """Each kind's tiles counted by the kind the probe gives them"""
    probe, rows, kinds = by_hand()
    counts = confusion(probe, rows, kinds)
    assert counts.dtype == torch.int64
    assert counts.tolist() == [[3, 0, 0], [0, 3, 0], [1, 1, 2]]


@pytest.mark.id("tst_7e9rld")
def test_tiles():
    """A probe on the backbone's features of the survey's tiles"""
    (learn, learn_kinds), (test, test_kinds) = split(20, 30, seed=5)
    backbone = load()
    probe = fit_probe(features(backbone, read(learn), 112), learn_kinds)
    tested = features(backbone, read(test), 112)
    share, error = accuracy(probe, tested, test_kinds)
    counts = confusion(probe, tested, test_kinds)
    assert share > 0.75 and math.isclose(error, math.sqrt(share * (1 - share) / 300))
    assert counts.sum(1).tolist() == [30] * 10
    assert math.isclose(counts.trace().item() / 300, share)
