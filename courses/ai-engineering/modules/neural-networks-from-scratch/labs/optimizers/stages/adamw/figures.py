import json

# PyTorch's default learning rate and AdamW's default weight decay, and a run's length.
LR, DECAY, STEPS = 0.001, 0.01, 10_000


def figures():
    cases = json.loads(open("references/steps.json").read())["adamw"]
    kept = 1 - LR * DECAY
    return {
        "cases": str(len(cases)),
        "lr": f"{LR:g}",
        "decay": f"{DECAY:g}",
        "kept": f"{kept:.5f}",
        "steps": f"{STEPS:,}",
        "after": f"{kept**STEPS:.3f}",
    }
