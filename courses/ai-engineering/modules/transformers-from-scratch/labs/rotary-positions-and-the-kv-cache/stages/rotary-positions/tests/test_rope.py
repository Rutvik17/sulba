import json
import math
from pathlib import Path

import pytest
import torch

from rope import frequencies, rotate

RECORDED = json.loads(Path("references/rotary.json").read_text())


def made(heads, length, dim, shift):
    """Numbers for heads of length positions, dim wide, from the formula the recording used."""
    return torch.tensor(
        [
            [
                [math.sin(shift + 0.3 * h + 0.7 * t + 0.11 * d) for d in range(dim)]
                for t in range(length)
            ]
            for h in range(heads)
        ],
        dtype=torch.float64,
    )


@pytest.mark.id("tst_2q9g04")
def test_frequencies():
    """Each pair's angle a position, theta to the power -2i / dim"""
    found = frequencies(64, 100000.0)
    assert found.dtype == torch.float64
    expected = torch.tensor(
        [100000.0 ** (-2 * i / 64) for i in range(32)], dtype=torch.float64
    )
    assert torch.allclose(found, expected, rtol=1e-14, atol=0)
    assert frequencies(8, 10.0).tolist() == pytest.approx(
        [1, 10**-0.25, 10**-0.5, 10**-0.75]
    )


@pytest.mark.id("tst_b3yc5h")
def test_transformers():
    """Queries and keys turned as transformers' Llama turns them, up to position 8,191"""
    positions = torch.tensor(RECORDED["positions"])
    for name, made_as in [
        ("q", made(2, len(positions), 64, 0.0)),
        ("k", made(1, len(positions), 64, 1.0)),
    ]:
        expected = torch.tensor(RECORDED[name], dtype=torch.float64)
        found = rotate(made_as, positions, RECORDED["theta"])
        assert torch.allclose(found, expected, rtol=0, atol=1e-9)


@pytest.mark.id("tst_b8sor6")
def test_distance():
    """Scores that depend only on how far apart a query and a key are"""
    q, k = made(1, 1, 64, 2.0)[0], made(1, 1, 64, 3.0)[0]

    def score(m, n):
        turned_q = rotate(q, torch.tensor([m]), 100000.0)
        turned_k = rotate(k, torch.tensor([n]), 100000.0)
        return (turned_q @ turned_k.T).item()

    for m, n in [(5, 2), (2, 5), (100, 40), (8000, 7000)]:
        for shift in [1, 37, 1000]:
            expected = pytest.approx(score(m, n), rel=1e-9, abs=1e-9)
            assert score(m + shift, n + shift) == expected
    assert score(5, 2) != pytest.approx(score(6, 2), rel=1e-6)


@pytest.mark.id("tst_447rc2")
def test_shapes():
    """Any leading dimensions, a batch's own positions, lengths kept and x's dtype"""
    x = made(6, 5, 8, 0.5).view(2, 3, 5, 8).float()
    turned = rotate(x, torch.arange(5), 10000.0)
    assert turned.shape == x.shape and turned.dtype == torch.float32
    assert torch.allclose(turned.norm(dim=-1), x.norm(dim=-1), rtol=1e-5)
    assert torch.equal(rotate(x, torch.zeros(5, dtype=torch.long), 10000.0), x)
    positions = torch.tensor([[0, 1, 2, 3, 4], [7, 8, 9, 10, 11]])
    batched = rotate(x, positions[:, None, :], 10000.0)
    for row in range(2):
        alone = rotate(x[row], positions[row], 10000.0)
        assert torch.allclose(batched[row], alone, rtol=0, atol=1e-6)
