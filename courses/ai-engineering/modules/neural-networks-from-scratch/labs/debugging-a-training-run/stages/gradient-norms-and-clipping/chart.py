import numpy as np

from clipping import clip_grad_norm_
from network import forward, loss_and_grads, network

# Training at a learning rate too high for the office's network: STEPS steps of SGD on
# batches of BATCH training digits, its loss averaged over each EVERY steps.
LR, STEPS, BATCH, EVERY = 3.0, 300, 64, 10


def office():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    return table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]


def run(X, digits, sets, max_norm):
    """The loss of each batch, and the share of validation digits read after the run."""
    rng = np.random.default_rng(0)
    params = network(rng)
    training, losses = np.flatnonzero(sets == 0), []
    for _ in range(STEPS):
        rows = rng.choice(training, size=BATCH, replace=False)
        loss, grads = loss_and_grads(params, X[rows], digits[rows])
        losses.append(loss)
        if max_norm is not None:
            clip_grad_norm_(grads, max_norm)
        for param, grad in zip(params, grads, strict=True):
            param -= LR * grad
    validation = sets == 1
    read = forward(params, X[validation])[2].argmax(axis=1)
    averaged = np.array(losses).reshape(-1, EVERY).mean(axis=1)
    return averaged, np.mean(read == digits[validation])


def chart(max_norm):
    X, digits, sets = office()
    clipped, read = run(X, digits, sets, max_norm)
    unclipped, _ = run(X, digits, sets, None)
    steps = np.arange(EVERY, STEPS + 1, EVERY)
    top = 4.0
    return {
        "x": {"min": 0, "max": STEPS, "step": 50, "label": "step"},
        "y": {
            "min": 0,
            "max": top,
            "step": 0.5,
            "label": f"loss, the mean of {EVERY} steps",
        },
        "lines": [
            {
                "style": "base",
                "label": "Without clipping",
                "x": steps,
                "y": [float(v) if v <= top else None for v in unclipped],
            },
            {
                "style": "main",
                "label": "Your clipping",
                "x": steps,
                "y": [float(v) if v <= top else None for v in clipped],
            },
        ],
        "points": [],
        "readouts": [
            {"label": "Validation digits read after it", "value": f"{read:.1%}"},
        ],
        "description": (
            f"The office's network trained at a learning rate of {LR:g} for {STEPS} steps, "
            f"with its gradients clipped to a total norm of {max_norm:g} and without"
        ),
    }
