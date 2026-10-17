import json
from pathlib import Path

import numpy as np
import pytest

from optim import SGD, Adam, AdamW

STEPS = json.loads(Path("references/steps.json").read_text())
RTOL, ATOL = 1e-10, 1e-12


def matches(optimizer_class, case):
    """Whether the optimizer's parameters, as it holds them, are PyTorch's after every one
    of a recorded case's steps."""
    optimizer = optimizer_class(
        [np.array(p) for p in case["params"]], **case["settings"]
    )
    for number, (grads, expected) in enumerate(
        zip(case["grads"], case["after"], strict=True)
    ):
        if case["lrs"]:
            optimizer.lr = case["lrs"][number]
        optimizer.step([np.array(g) for g in grads])
        for param, want in zip(optimizer.params, expected, strict=True):
            if not np.allclose(param, want, rtol=RTOL, atol=ATOL):
                return False
    return True


@pytest.mark.id("tst_yspabs")
def test_schedule():
    """SGD with momentum through a drop in the learning rate, as PyTorch steps"""
    assert matches(SGD, STEPS["sgd"][5])


@pytest.mark.id("tst_quz5oa")
def test_adam_first_steps():
    """Adam's first steps, as PyTorch takes them"""
    assert matches(Adam, STEPS["adam"][0])


@pytest.mark.id("tst_8jxzyx")
def test_adamw_decay():
    """AdamW's weight decay alone, the loss's gradient at 0, as PyTorch takes it"""
    assert matches(AdamW, STEPS["adamw"][2])


@pytest.mark.id("tst_xe8fmx")
def test_network_learns():
    """The office's network, trained with SGD, reads digits it couldn't before"""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, X = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:] / 16
    rng = np.random.default_rng(0)
    params = []
    for inputs, outputs in [(64, 32), (32, 10)]:
        bound = 1 / np.sqrt(inputs)
        params.append(rng.uniform(-bound, bound, size=(outputs, inputs)))
        params.append(rng.uniform(-bound, bound, size=outputs))
    W1, b1, W2, b2 = params
    optimizer = SGD(params, lr=0.5)
    training = np.flatnonzero(sets == 0)
    for _ in range(100):
        rows = rng.choice(training, size=64, replace=False)
        hidden = X[rows] @ W1.T + b1
        relu = np.maximum(hidden, 0.0)
        logits = relu @ W2.T + b2
        exps = np.exp(logits - logits.max(axis=1, keepdims=True))
        dlogits = exps / exps.sum(axis=1, keepdims=True)
        dlogits[np.arange(64), digits[rows]] -= 1
        dlogits /= 64
        dhidden = (dlogits @ W2) * (hidden > 0)
        grads = [
            dhidden.T @ X[rows],
            dhidden.sum(axis=0),
            dlogits.T @ relu,
            dlogits.sum(axis=0),
        ]
        optimizer.step(grads)
    validation = sets == 1
    read = (np.maximum(X[validation] @ W1.T + b1, 0.0) @ W2.T + b2).argmax(axis=1)
    assert np.mean(read == digits[validation]) > 0.5
