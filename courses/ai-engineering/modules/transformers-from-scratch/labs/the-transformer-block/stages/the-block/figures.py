import torch
import torch.nn.functional as F

# GPT-2 small's blocks are 768 wide. GELU's two forms compared from -6 to 6.
WIDTH, LOW, HIGH, POINTS = 768, -6, 6, 120001


def figures():
    x = torch.linspace(LOW, HIGH, POINTS, dtype=torch.float64)
    gap = (F.gelu(x) - F.gelu(x, approximate="tanh")).abs().max().item()
    mlp = 8 * WIDTH**2 + 5 * WIDTH
    block = 12 * WIDTH**2 + 13 * WIDTH
    # The largest gap stands clear of the rounding to two significant figures.
    assert 0.000465 < gap < 0.000485
    return {
        "low": str(LOW),
        "high": str(HIGH),
        "gap": f"{gap:.5f}",
        "width": str(WIDTH),
        "mlp": f"{mlp:,}",
        "block": f"{block:,}",
        "share": f"{mlp / block:.0%}",
    }
