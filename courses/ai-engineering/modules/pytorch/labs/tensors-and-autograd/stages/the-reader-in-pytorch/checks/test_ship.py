import numpy as np
import pytest
import torch

from reader import train

TARGET = 0.95
HIDDEN, EPOCHS, BATCH, LR = 32, 20, 64, 0.1
DIGITS = 10


@pytest.fixture(scope="module")
def office():
    """The training digits and the test digits, as NumPy arrays."""
    table = np.loadtxt("data/digits.csv", delimiter=",", skiprows=1)
    sets, digits, pixels = table[:, 0], table[:, 1].astype(np.int64), table[:, 2:]
    train_rows, test_rows = sets == 0, sets == 2
    return (
        np.ascontiguousarray(pixels[train_rows]),
        digits[train_rows],
        np.ascontiguousarray(pixels[test_rows]),
        digits[test_rows],
    )


def numpy_reader(pixels, digits, rng):
    """The NumPy reader, trained as it trains: the digits it reads for a batch of pixels."""
    mean, spread = pixels.mean(axis=0), pixels.std(axis=0)
    spread = np.where(spread > 0, spread, 1.0)
    X = (pixels - mean) / spread
    layers = []
    for inputs, outputs in [(X.shape[1], HIDDEN), (HIDDEN, DIGITS)]:
        bound = 1 / np.sqrt(inputs)
        weight = rng.uniform(-bound, bound, size=(outputs, inputs))
        layers.append([weight, rng.uniform(-bound, bound, size=outputs)])

    def forward(batch):
        hidden = batch @ layers[0][0].T + layers[0][1]
        relu = np.where(hidden > 0, hidden, 0.0)
        return relu @ layers[1][0].T + layers[1][1], hidden, relu

    for _ in range(EPOCHS):
        order = rng.permutation(len(digits))
        for start in range(0, len(order), BATCH):
            rows = order[start : start + BATCH]
            z, hidden, relu = forward(X[rows])
            shifted = z - z.max(axis=1, keepdims=True)
            dz = np.exp(shifted) / np.exp(shifted).sum(axis=1, keepdims=True)
            dz[np.arange(len(rows)), digits[rows]] -= 1
            dz /= len(rows)
            dhidden = np.where(hidden > 0, dz @ layers[1][0], 0.0)
            gradients = [
                (dhidden.T @ X[rows], dhidden.sum(axis=0)),
                (dz.T @ relu, dz.sum(axis=0)),
            ]
            for layer, (dW, db) in zip(layers, gradients, strict=True):
                layer[0] = layer[0] - LR * dW
                layer[1] = layer[1] - LR * db
    return lambda batch: forward((batch - mean) / spread)[0].argmax(axis=1)


@pytest.fixture(scope="module")
def trained(office):
    """The port trained on every training digit with seed 0, and copies of what it was given."""
    pixels, digits, _, _ = office
    given = torch.from_numpy(pixels.copy()), torch.from_numpy(digits.copy())
    read = train(*given, np.random.default_rng(0))
    return read, given


@pytest.mark.id("tst_umb8bl")
def test_as_the_numpy_reader(office, trained, record_property):
    """Every test digit read as the NumPy reader reads it"""
    pixels, digits, test_pixels, _ = office
    read, _ = trained
    expected = numpy_reader(pixels, digits, np.random.default_rng(0))(test_pixels)
    found = read(torch.from_numpy(test_pixels.copy())).numpy()
    record_property("note", f"{np.sum(found != expected)} read differently")
    assert np.array_equal(found, expected)


@pytest.mark.id("tst_ev8m8c")
def test_new_writers(office, trained, record_property):
    """95% of new writers' digits"""
    _, _, test_pixels, test_digits = office
    read, _ = trained
    share = np.mean(read(torch.from_numpy(test_pixels.copy())).numpy() == test_digits)
    record_property("note", f"{share:.1%} right")
    assert share >= TARGET


@pytest.mark.id("tst_ga7nmm")
def test_reads_without_a_graph(office, trained):
    """Reads without building a graph"""
    _, _, test_pixels, _ = office
    read, _ = trained
    saved = []
    with torch.autograd.graph.saved_tensors_hooks(
        lambda tensor: saved.append(1), lambda _: None
    ):
        read(torch.from_numpy(test_pixels.copy()))
    assert not saved


@pytest.mark.id("tst_t3aoih")
def test_inputs_kept(office, trained):
    """Its inputs left as they were"""
    pixels, digits, test_pixels, _ = office
    read, (given_pixels, given_digits) = trained
    assert np.array_equal(given_pixels.numpy(), pixels)
    assert np.array_equal(given_digits.numpy(), digits)
    batch = torch.from_numpy(test_pixels.copy())
    read(batch)
    assert np.array_equal(batch.numpy(), test_pixels)
