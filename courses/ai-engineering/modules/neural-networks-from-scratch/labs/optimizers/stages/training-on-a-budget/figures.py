import numpy as np

# The office's network and its training, and what it must read of new writers' digits.
WIDTHS, BATCH, BUDGET, TARGET = (64, 64, 10), 64, 300, 0.93
BETA1, BETA2 = 0.9, 0.999
# The candidates the solution compared: SGD's learning rate and momentum, PyTorch's
# default learning rate for Adam, and the learning rate the solution chose.
SGD_LR, MOMENTUM, ADAM_DEFAULT, ADAM_LR = 0.1, 0.9, 0.001, 0.01


def network(rng, widths):
    """A weight and a bias for each linear layer, drawn as torch.nn.Linear draws them."""
    params = []
    for inputs, outputs in zip(widths, widths[1:]):
        bound = 1 / np.sqrt(inputs)
        params.append(rng.uniform(-bound, bound, size=(outputs, inputs)))
        params.append(rng.uniform(-bound, bound, size=outputs))
    return params


def batches(rng, rows, steps):
    """steps batches of BATCH rows, in an order shuffled for each pass over them."""
    order = []
    while len(order) < steps * BATCH:
        order.extend(rng.permutation(rows))
    return [np.array(order[i * BATCH : (i + 1) * BATCH]) for i in range(steps)]


def forward(params, X):
    """Each layer's input, each ReLU's input, and the logits."""
    inputs, before = [X], []
    for number in range(0, len(params), 2):
        out = inputs[-1] @ params[number].T + params[number + 1]
        if number + 2 == len(params):
            return inputs, before, out
        before.append(out)
        inputs.append(np.maximum(out, 0.0))


def gradients(params, X, digits):
    """The mean cross-entropy's gradient with respect to each parameter."""
    inputs, before, logits = forward(params, X)
    exps = np.exp(logits - logits.max(axis=1, keepdims=True))
    d = exps / exps.sum(axis=1, keepdims=True)
    d[np.arange(len(digits)), digits] -= 1
    d /= len(digits)
    grads = [None] * len(params)
    for number in range(len(params) - 2, -1, -2):
        grads[number] = d.T @ inputs[number // 2]
        grads[number + 1] = d.sum(axis=0)
        if number:
            d = (d @ params[number]) * (before[number // 2 - 1] > 0)
    return grads


def sgd(lr, momentum=0.0):
    """A step of SGD with momentum, as PyTorch takes it, for each parameter."""
    buffers = {}

    def step(params, grads):
        for number, (param, grad) in enumerate(zip(params, grads, strict=True)):
            if momentum:
                buffers[number] = momentum * buffers.get(number, 0) + grad
                grad = buffers[number]
            param -= lr * grad

    return step


def adam(lr):
    """A step of Adam, as PyTorch takes it, for each parameter."""
    m, v, t = {}, {}, [0]

    def step(params, grads):
        t[0] += 1
        for number, (param, grad) in enumerate(zip(params, grads, strict=True)):
            m[number] = BETA1 * m.get(number, 0) + (1 - BETA1) * grad
            v[number] = BETA2 * v.get(number, 0) + (1 - BETA2) * grad**2
            m_hat = m[number] / (1 - BETA1 ** t[0])
            v_hat = v[number] / (1 - BETA2 ** t[0])
            param -= lr * m_hat / (np.sqrt(v_hat) + 1e-8)

    return step


def trained(step, X, digits, sets):
    """The office's network after the budget's steps, trained as the checks train it."""
    rng = np.random.default_rng(0)
    params = network(rng, WIDTHS)
    for rows in batches(rng, np.flatnonzero(sets == 0), BUDGET):
        step(params, gradients(params, X[rows], digits[rows]))
    return params


def figures():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    X, digits, sets = table[:, 2:] / 16, table[:, 1].astype(np.int64), table[:, 0]

    def share(params, number):
        rows = sets == number
        return (
            f"{np.mean(forward(params, X[rows])[2].argmax(axis=1) == digits[rows]):.1%}"
        )

    chosen = trained(adam(ADAM_LR), X, digits, sets)
    # A resumed Adam that starts its step count again: its averages are full, and its
    # correction treats them as new.
    t = np.arange(1, BUDGET // 2 + 1)
    shrink = np.sqrt(1 - BETA2**t) / (1 - BETA1**t)
    least = int(np.argmin(shrink))
    return {
        "target": f"{TARGET:.0%}",
        "hidden": str(WIDTHS[1]),
        "sgd_lr": f"{SGD_LR:g}",
        "mu": f"{MOMENTUM:g}",
        "default_lr": f"{ADAM_DEFAULT:g}",
        "chosen_lr": f"{ADAM_LR:g}",
        "budget": str(BUDGET),
        "batch": str(BATCH),
        "half": str(BUDGET // 2),
        "training": f"{np.sum(sets == 0):,}",
        "validation": str(int(np.sum(sets == 1))),
        "test": f"{np.sum(sets == 2):,}",
        "sgd": share(trained(sgd(SGD_LR), X, digits, sets), 1),
        "momentum": share(trained(sgd(SGD_LR, MOMENTUM), X, digits, sets), 1),
        "adam_default": share(trained(adam(ADAM_DEFAULT), X, digits, sets), 1),
        "adam": share(chosen, 1),
        "chosen_test": share(chosen, 2),
        "shrink": f"{shrink[least]:.0%}",
        "shrink_step": str(least + 1),
    }
