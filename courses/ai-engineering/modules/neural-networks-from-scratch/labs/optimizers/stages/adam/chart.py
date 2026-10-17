import numpy as np

from optimizers import Adam

STEPS = 100
BETA1 = 0.9
# The axis for the steps at each β2: its top and the gap between its ticks.
AXES = {0.99: (3, 0.5), 0.999: (8, 1), 0.9999: (24, 4)}


def chart(beta2):
    """Adam's step at each of STEPS steps for a gradient of 1, at a learning rate of 1, so
    that each step is in learning rates, and the steps without the bias correction."""
    w = np.zeros(1)
    optimizer = Adam([w], lr=1.0, betas=(BETA1, beta2))
    t = np.arange(1, STEPS + 1)
    steps = []
    for _ in t:
        before = w[0]
        optimizer.step([np.ones(1)])
        steps.append(before - w[0])
    # Without the correction the averages are 1 - β to the power t times the gradient.
    uncorrected = (1 - BETA1**t) / np.sqrt(1 - beta2**t)
    peak = int(np.argmax(uncorrected))
    top, gap = AXES[beta2]
    return {
        "x": {"min": 0, "max": STEPS, "step": 20, "label": "step"},
        "y": {"min": 0, "max": top, "step": gap, "label": "step, in learning rates"},
        "lines": [
            {
                "style": "dashed",
                "label": "Without the bias correction",
                "x": t,
                "y": uncorrected,
            },
            {"style": "main", "label": "Your Adam's step", "x": t, "y": steps},
        ],
        "points": [],
        "readouts": [
            {"label": "Your first step", "value": f"{steps[0]:.2f} learning rates"},
            {
                "label": "Largest without the correction",
                "value": f"{uncorrected[peak]:.1f} learning rates, at step {peak + 1}",
            },
        ],
        "description": (
            f"Adam's step at each step for a steady gradient, with β2 = {beta2:g}, and "
            "the steps it would take without the bias correction"
        ),
    }
