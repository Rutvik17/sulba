import json

import numpy as np

STEPS = json.loads(open("references/steps.json").read())
# The network check's training: its hidden units, steps, batch and learning rate.
HIDDEN, TRAINING, BATCH, LR = 32, 100, 64, 0.5
# PyTorch's default betas.
BETA1, BETA2 = 0.9, 0.999


def momentum_steps(case, pytorch):
    """The size of each step of SGD with momentum through the case's schedule, with the
    velocity in the gradient's units, as PyTorch keeps it, or in the step's, as the
    assistant kept it."""
    mu = case["settings"]["momentum"]
    velocity = [np.zeros_like(np.array(p)) for p in case["params"]]
    sizes = []
    for lr, grads in zip(case["lrs"], case["grads"], strict=True):
        steps = []
        for number, grad in enumerate(grads):
            if pytorch:
                velocity[number] = mu * velocity[number] + np.array(grad)
                steps.append(lr * velocity[number])
            else:
                velocity[number] = mu * velocity[number] + lr * np.array(grad)
                steps.append(velocity[number])
        sizes.append(np.sqrt(sum(np.sum(step**2) for step in steps)))
    return np.array(sizes)


def decayed(case, assistant):
    """The parameters after the case's steps of AdamW with gradients of 0: decayed directly,
    as PyTorch decays them, or with the decay added to the gradient, as the assistant
    added it."""
    lr, decay = case["settings"]["lr"], case["settings"]["weight_decay"]
    params = [np.array(p) for p in case["params"]]
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    for t in range(1, len(case["grads"]) + 1):
        for number, param in enumerate(params):
            if not assistant:
                params[number] = param - lr * decay * param
                continue
            grad = decay * param
            m[number] = BETA1 * m[number] + (1 - BETA1) * grad
            v[number] = BETA2 * v[number] + (1 - BETA2) * grad**2
            m_hat, v_hat = m[number] / (1 - BETA1**t), v[number] / (1 - BETA2**t)
            params[number] = param - lr * m_hat / (np.sqrt(v_hat) + 1e-8)
    return np.concatenate([p.ravel() for p in params])


def network_accuracy(trains):
    """The share of the validation digits the network check's network reads right, after
    its training, or with its weights as they started, as the assistant's left them."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, X = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:] / 16
    rng = np.random.default_rng(0)
    params = []
    for inputs, outputs in [(64, HIDDEN), (HIDDEN, 10)]:
        bound = 1 / np.sqrt(inputs)
        params.append(rng.uniform(-bound, bound, size=(outputs, inputs)))
        params.append(rng.uniform(-bound, bound, size=outputs))
    W1, b1, W2, b2 = params
    training = np.flatnonzero(sets == 0)
    for _ in range(TRAINING if trains else 0):
        rows = rng.choice(training, size=BATCH, replace=False)
        hidden = X[rows] @ W1.T + b1
        relu = np.maximum(hidden, 0.0)
        logits = relu @ W2.T + b2
        exps = np.exp(logits - logits.max(axis=1, keepdims=True))
        dlogits = exps / exps.sum(axis=1, keepdims=True)
        dlogits[np.arange(BATCH), digits[rows]] -= 1
        dlogits /= BATCH
        dhidden = (dlogits @ W2) * (hidden > 0)
        grads = [dhidden.T @ X[rows], dhidden.sum(axis=0), dlogits.T @ relu]
        grads.append(dlogits.sum(axis=0))
        for param, grad in zip(params, grads, strict=True):
            param -= LR * grad
    validation = sets == 1
    read = (np.maximum(X[validation] @ W1.T + b1, 0.0) @ W2.T + b2).argmax(axis=1)
    return np.mean(read == digits[validation])


def figures():
    schedule = STEPS["sgd"][5]
    drop = schedule["lrs"].index(schedule["lrs"][-1])
    ratio = momentum_steps(schedule, False) / momentum_steps(schedule, True)
    t = np.arange(1, 1001)
    uncorrected = (1 - BETA1**t) / np.sqrt(1 - BETA2**t)
    peak = int(np.argmax(uncorrected))
    zero = STEPS["adamw"][2]
    start = np.concatenate([np.array(p).ravel() for p in zero["params"]])
    pytorch, assistant = decayed(zero, False), decayed(zero, True)
    return {
        "high": f"{schedule['lrs'][0]:g}",
        "low": f"{schedule['lrs'][-1]:g}",
        "drop": str(drop),
        "after_drop": f"{ratio[drop]:.1f}",
        "last": str(len(ratio)),
        "at_last": f"{ratio[-1]:.1f}",
        "first": f"{uncorrected[0]:.2f}",
        "peak": f"{uncorrected[peak]:.1f}",
        "peak_step": str(peak + 1),
        "zero_lr": f"{zero['settings']['lr']:g}",
        "zero_decay": f"{zero['settings']['weight_decay']:g}",
        "zero_steps": str(len(zero["grads"])),
        "pytorch_share": f"{np.mean(1 - pytorch / start):.1%}",
        "assistant_move": f"{np.median(np.abs(assistant - start)):.2f}",
        "crossed": str(int(np.sum(np.sign(assistant) != np.sign(start)))),
        "weights": str(len(start)),
        "steps": str(TRAINING),
        "untrained": f"{network_accuracy(False):.1%}",
        "trained": f"{network_accuracy(True):.1%}",
    }
