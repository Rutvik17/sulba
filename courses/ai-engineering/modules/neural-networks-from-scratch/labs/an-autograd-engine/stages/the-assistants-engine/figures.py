import json

import numpy as np

MODELS = json.loads(open("references/models.json").read())
# A deeper network of the same blocks, for how the assistant's order grows with depth.
DEEPER = 30
# A point on tanh, where the assistant's slope and tanh's are compared.
X = 2.0


class Node:
    """A tensor as the engine records it: its value, its parents, and for each parent a
    function from this tensor's gradient to that parent's share of it."""

    def __init__(self, data, parents=(), shares=()):
        self.data, self._parents, self.shares = data, parents, shares
        self.grad = np.zeros_like(data)


def network(X, layers):
    """The check's network, with each operation's parents in the order the engine gives
    them: blocks of x + relu(x Wᵀ + b), then the mean of the last block's output, made as
    the engine makes a mean, a sum times one over the count."""
    x = Node(X)
    weights = []
    for weight, bias in layers:
        weight, bias = Node(weight), Node(bias)
        weights.append(weight)
        WT = Node(weight.data.T, (weight,), (lambda g: g.T,))
        product = Node(
            x.data @ WT.data,
            (x, WT),
            (lambda g, WT=WT: g @ WT.data.T, lambda g, x=x: x.data.T @ g),
        )
        z = Node(
            product.data + bias.data,
            (product, bias),
            (lambda g: g, lambda g: g.sum(axis=0)),
        )
        relu = Node(np.maximum(z.data, 0.0), (z,), (lambda g, z=z: g * (z.data > 0),))
        x = Node(x.data + relu.data, (x, relu), (lambda g: g, lambda g: g))
    total = Node(x.data.sum(), (x,), (lambda g, x=x: np.full(x.data.shape, g),))
    scale = Node(np.array(1.0 / x.data.size))
    out = Node(
        total.data * scale.data,
        (total, scale),
        (lambda g: g * scale.data, lambda g: g * total.data),
    )
    return out, weights


def order(output, visited):
    """A depth-first order: with a set of the tensors visited, as the fix makes it, and
    without, as the assistant's topological_order makes it."""
    found, seen = [], set()

    def visit(node):
        if visited and id(node) in seen:
            return
        seen.add(id(node))
        for parent in node._parents:
            visit(parent)
        found.append(node)

    visit(output)
    return found


def backward(output, listed):
    output.grad = np.ones_like(output.data)
    for node in reversed(listed):
        for parent, share in zip(node._parents, node.shares, strict=True):
            parent.grad = parent.grad + share(node.grad)


def entries(node, counted):
    """How many entries the assistant's order lists for node: itself, once it has listed
    each parent's in full."""
    if id(node) not in counted:
        counted[id(node)] = 1 + sum(
            entries(parent, counted) for parent in node._parents
        )
    return counted[id(node)]


def figures():
    case = MODELS["residual"]
    X0 = np.array(case["X"])
    layers = [
        (np.array(layer["weight"]), np.array(layer["bias"])) for layer in case["layers"]
    ]
    first = np.array(case["gradients"][0]["weight"])
    out, weights = network(X0, layers)
    right = order(out, visited=True)
    backward(out, right)
    assert np.allclose(weights[0].grad, first, rtol=1e-10, atol=1e-12)
    out, weights = network(X0, layers)
    wrong = order(out, visited=False)
    backward(out, wrong)
    assert entries(out, {}) == len(wrong)
    deeper, _ = network(np.zeros((1, 1)), [(np.zeros((1, 1)), np.zeros(1))] * DEEPER)
    logits = np.array(MODELS["log_sum_exp"]["logits"])
    tanh = MODELS["tanh"]
    inputs = np.array(tanh["X"]) @ np.array(tanh["weight"]).T + np.array(tanh["bias"])
    return {
        "blocks": str(len(layers)),
        "tensors": str(len(right)),
        "entries": str(len(wrong)),
        "ratio": f"{np.linalg.norm(weights[0].grad) / np.linalg.norm(first):,.0f}",
        "deeper": str(DEEPER),
        "deeper_entries": f"{entries(deeper, {}):,}",
        "rows": str(logits.shape[0]),
        "classes": str(logits.shape[1]),
        "beyond": f"{np.mean(np.abs(inputs) > 1):.0%}",
        "x": f"{X:g}",
        "wrong": f"{1 - X**2:g}".replace("-", "−"),
        "right": f"{1 - np.tanh(X) ** 2:.3f}",
    }
