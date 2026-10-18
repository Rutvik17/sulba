import torch

# The office's optimizer.
LR, MOMENTUM = 0.05, 0.9


def figures():
    state = torch.Generator().manual_seed(0).get_state()
    return {
        "lr": str(LR),
        "momentum": str(MOMENTUM),
        "generator": f"{state.numel():,}",
    }
