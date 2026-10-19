"""A linear probe on the backbone's features: the kinds it gives tiles, and how often it's
right."""

import math

import torch
import torch.nn.functional as F
from torch import nn


class Probe(nn.Module):
    """A linear layer on features standardized as the labelled tiles' were: each feature less
    its mean over them, divided by its standard deviation. It starts from zero weights."""

    def __init__(self, mean, std, kinds):
        super().__init__()
        self.register_buffer("mean", mean.to(torch.float64))
        self.register_buffer("std", std.to(torch.float64))
        self.linear = nn.Linear(len(mean), kinds, dtype=torch.float64)
        nn.init.zeros_(self.linear.weight)
        nn.init.zeros_(self.linear.bias)

    def forward(self, features):
        """Each kind's score for each row of features, float64 (N, kinds)."""
        return self.linear((features.to(torch.float64) - self.mean) / self.std)


def fit_probe(features, kinds, decay=1e-3):
    """A Probe on the labelled tiles' features and their kinds' numbers that minimizes their
    mean cross-entropy plus decay times the sum of its weights' squares, with L-BFGS."""
    features = features.to(torch.float64)
    probe = Probe(features.mean(0), features.std(0), int(kinds.max()) + 1)
    optimizer = torch.optim.LBFGS(
        probe.parameters(),
        max_iter=1000,
        tolerance_grad=1e-9,
        tolerance_change=0,
        line_search_fn="strong_wolfe",
    )

    def closure():
        optimizer.zero_grad()
        loss = F.cross_entropy(probe(features), kinds)
        loss = loss + decay * probe.linear.weight.square().sum()
        loss.backward()
        return loss

    optimizer.step(closure)
    return probe


def accuracy(probe, features, kinds):
    """The share of the tiles whose kind the probe gives right, and its standard error."""
    with torch.no_grad():
        right = (probe(features).argmax(1) == kinds).to(torch.float64).mean().item()
    return right, math.sqrt(right * (1 - right) / len(kinds))


def confusion(probe, features, kinds):
    """How many tiles of each kind, by row, the probe gives each kind, by column, as int64."""
    count = probe.linear.out_features
    with torch.no_grad():
        given = probe(features).argmax(1)
    pairs = torch.bincount(kinds * count + given, minlength=count * count)
    return pairs.reshape(count, count)
