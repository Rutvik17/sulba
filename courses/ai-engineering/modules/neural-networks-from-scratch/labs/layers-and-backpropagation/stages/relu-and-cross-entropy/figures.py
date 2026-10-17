import json

import numpy as np


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1, dtype=np.int64)
    recorded = json.loads(open("references/activations.json").read())
    confident = recorded["cross_entropy"][-1]
    return {
        "classes": str(len(np.unique(table[:, 1]))),
        "log_ten": f"{np.log(10):.3f}",
        "overflow": f"{np.log(np.finfo(np.float64).max):.1f}",
        "largest": f"{np.max(np.abs(confident['logits'])):,.0f}",
        "confident_loss": f"{confident['loss']:.1f}",
    }
