import json

import numpy as np

# PyTorch's default betas.
BETA1, BETA2 = 0.9, 0.999


def figures():
    cases = json.loads(open("references/steps.json").read())["adam"]
    t = np.arange(1, 1001)
    # A steady gradient's step without the bias correction, in learning rates.
    uncorrected = (1 - BETA1**t) / np.sqrt(1 - BETA2**t)
    peak = int(np.argmax(uncorrected))
    return {
        "cases": str(len(cases)),
        "beta1": f"{BETA1:g}",
        "beta2": f"{BETA2:g}",
        "first": f"{uncorrected[0]:.2f}",
        "peak": f"{uncorrected[peak]:.1f}",
        "peak_step": str(peak + 1),
    }
