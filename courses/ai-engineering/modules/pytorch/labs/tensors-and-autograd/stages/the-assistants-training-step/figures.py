import numpy as np
import torch
import torch.nn.functional as F

# The NumPy reader's network and training.
HIDDEN, EPOCHS, BATCH, LR = 32, 20, 64, 0.1
DIGITS = 10
# The epochs the gradients that added up are trained for: past a few, the loss grows so large
# that rounding, which differs from one machine to another, decides where training ends.
ACCUMULATED_EPOCHS = 3


def office():
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    train, test = table[table[:, 0] == 0], table[table[:, 0] == 2]
    as_tensors = [np.ascontiguousarray(part[:, 2:]) for part in (train, test)]
    pixels, test_pixels = (torch.from_numpy(part) for part in as_tensors)
    digits = torch.from_numpy(train[:, 1].astype(np.int64))
    return pixels, digits, test_pixels, torch.from_numpy(test[:, 1].astype(np.int64))


def scaled(batch, train, correction):
    spread = train.std(dim=0, correction=correction)
    return (batch - train.mean(dim=0)) / torch.where(spread > 0, spread, 1.0)


def trained(pixels, digits, mistake=None, epochs=EPOCHS):
    """The reader trained as the NumPy reader trains, from default_rng(0), with one of the
    assistant's mistakes or none: how it reads, how far training moved the start it was given,
    and each batch's loss."""
    rng = np.random.default_rng(0)
    begun = {}
    for layer, (inputs, outputs) in enumerate(
        [(pixels.shape[1], HIDDEN), (HIDDEN, DIGITS)], 1
    ):
        bound = 1 / np.sqrt(inputs)
        begun[f"w{layer}"] = rng.uniform(-bound, bound, size=(outputs, inputs))
        begun[f"b{layer}"] = rng.uniform(-bound, bound, size=outputs)
    kept = {name: array.copy() for name, array in begun.items()}
    params = {
        name: torch.from_numpy(array).requires_grad_() for name, array in begun.items()
    }
    correction = 1 if mistake == "spread" else 0
    X = scaled(pixels, pixels, correction)

    def forward(batch):
        hidden = torch.relu(batch @ params["w1"].T + params["b1"])
        if mistake == "detached":
            hidden = hidden.detach()
        return hidden @ params["w2"].T + params["b2"]

    losses = []
    for _ in range(epochs):
        order = torch.from_numpy(rng.permutation(len(digits)))
        for start in range(0, len(order), BATCH):
            rows = order[start : start + BATCH]
            loss = F.cross_entropy(forward(X[rows]), digits[rows])
            loss.backward()
            losses.append(loss.item())
            with torch.no_grad():
                for param in params.values():
                    if param.grad is not None:
                        param -= LR * param.grad
                        if mistake != "accumulated":
                            param.grad = None

    def read(batch):
        """Each digit read, and the probability the reader gives it."""
        with torch.no_grad():
            probabilities = forward(scaled(batch, pixels, correction)).softmax(dim=1)
        return probabilities.max(dim=1)

    moved = max(float(np.abs(begun[name] - kept[name]).max()) for name in kept)
    return read, moved, losses


def figures():
    pixels, digits, test_pixels, test_digits = office()
    read, moved, losses = trained(pixels, digits)
    sure, reads = read(test_pixels)
    # The prose says the NumPy reader's loss on a batch never rises above its first.
    assert max(losses) == losses[0]
    accumulated = trained(pixels, digits, "accumulated", ACCUMULATED_EPOCHS)[2]
    frozen = trained(pixels, digits, "detached")[0](test_pixels)[1]
    spread_sure, spread_reads = trained(pixels, digits, "spread")[0](test_pixels)
    # The prose says the spread's mistake reads every test digit as the NumPy reader does.
    assert torch.equal(spread_reads, reads)
    shift = (
        (scaled(test_pixels, pixels, 1) - scaled(test_pixels, pixels, 0)).abs().max()
    )
    n = len(digits)
    return {
        "epoch": str(ACCUMULATED_EPOCHS),
        "peak": f"{max(accumulated):.1f}",
        "first_loss": f"{losses[0]:.2f}",
        "frozen": f"{(frozen == test_digits).double().mean().item():.1%}",
        "n": f"{n:,}",
        "n_less": f"{n - 1:,}",
        "shift": f"{shift.item():.4f}",
        "surer": f"{(spread_sure - sure).abs().max().item() * 100:.2f}",
        "test": f"{len(test_digits):,}",
        "moved": f"{moved:.2f}",
    }
