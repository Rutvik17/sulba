import numpy as np
from scipy.spatial.distance import cdist

PATH = "data/breast-cancer.csv"
# The steps tried, from 10 to the power -16 to 1 in half powers. They are written as
# decimals, which every runtime reads as the same numbers.
POWERS = np.arange(-16, 0.001, 0.5)
STEPS = np.array(
    [float(f"{m}e{e}") for e in range(-16, 0) for m in ("1", "3.1622776601683795")]
    + [1.0]
)
# PyTorch 2.14's torch.autograd.gradcheck takes central differences, with eps=1e-06.
TORCH_STEP = 1e-6
# x³ at a million, by a central difference with a fixed step and with one scaled to x.
FAR = 1e6


def tex(value, digits):
    """A number in TeX, as a multiple of a power of 10."""
    mantissa, exponent = f"{value:.{digits}e}".split("e")
    return f"{mantissa} \\times 10^{{{int(exponent)}}}"


def texture_distance():
    """The distance from the first new sample to its nearest record as the sample's worst
    texture moves by t standard deviations, and the gap in worst texture between them."""
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        j = file.readline().strip().split(",")[2:].index("worst_texture")
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    records, sample = (X - mean) / std, (table[new, 2:][0] - mean) / std
    gap = sample - records[np.argmin(cdist(sample[None, :], records)[0])]
    rest = np.sum(np.delete(gap, j) ** 2)

    def distance(t):
        moved = gap[j] + t
        return float(np.sqrt(rest + moved * moved))

    return distance, gap[j]


def power(value):
    """An exact power of 10 in TeX."""
    return f"10^{{{round(np.log10(value))}}}"


def cube_error(h):
    """The relative error of a central difference of x³ at FAR with step h."""
    up, down = FAR + h, FAR - h
    estimate = (up * up * up - down * down * down) / (2 * h)
    return abs(estimate - 3 * FAR * FAR) / (3 * FAR * FAR)


def figures():
    distance, gap = texture_distance()
    exact = gap / distance(0.0)
    forward = np.array([abs((distance(h) - distance(0.0)) / h - exact) for h in STEPS])
    central = np.array(
        [abs((distance(h) - distance(-h)) / (2 * h) - exact) for h in STEPS]
    )
    eps = np.finfo(np.float64).eps
    return {
        "eps": tex(eps, 1),
        "sqrt_eps": tex(np.sqrt(eps), 1),
        "cbrt_eps": tex(np.cbrt(eps), 1),
        "torch_step": power(TORCH_STEP),
        "exact": f"{exact:.3f}",
        "gap": f"{abs(gap):.2f}",
        "distance": f"{distance(0.0):.2f}",
        "fwd_power": f"{POWERS[np.argmin(forward)]:g}",
        "fwd_best": tex(forward.min(), 1),
        "cen_power": f"{POWERS[np.argmin(central)]:g}",
        "cen_best": tex(central.min(), 1),
        "far": power(FAR),
        "fixed_error": tex(cube_error(TORCH_STEP), 1),
        "scaled_error": tex(cube_error(np.cbrt(eps) * FAR), 1),
    }
