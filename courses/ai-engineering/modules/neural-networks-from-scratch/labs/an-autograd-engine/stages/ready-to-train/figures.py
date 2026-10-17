import json
import math
import sys

import numpy as np

# Residual networks have been trained this many layers deep (arXiv:1512.03385, 4.2).
RESNET_LAYERS = 1202
# The check's chain: this many steps of x + x * STEP.
DEPTH, STEP = 10_000, 1e-4


def figures():
    models = json.loads(open("references/models.json").read())
    confident = np.array(models["cross_entropy"][-1]["logits"])
    gradient = (1 + STEP) ** DEPTH
    return {
        "resnet": f"{RESNET_LAYERS:,}",
        "depth": f"{DEPTH:,}",
        "limit": f"{sys.getrecursionlimit():,}",
        "largest": f"{np.max(np.abs(confident)):,.0f}",
        "overflow": f"{np.log(np.finfo(np.float64).max):.1f}",
        "step": f"{STEP:g}",
        "gradient": f"{gradient:.5f}",
        "from_e": f"{math.e - gradient:.5f}",
    }
