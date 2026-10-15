import numpy as np
from scipy.spatial.distance import cdist

PATH = "data/breast-cancer.csv"
# The checks' sizes: the shift far from 0, the records found, new samples looked up at
# once, records, and the memory allowed.
SHIFT, K, LOOKUPS, RECORDS, BUDGET = 100_000_000, 5, 50, 10_000, 32_000_000


def power_of_ten(value, digits):
    """A number in TeX, as a multiple of a power of 10."""
    mantissa, exponent = f"{value:.{digits}e}".split("e")
    return f"{mantissa} \\times 10^{{{int(exponent)}}}"


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    X = table[~new, 2:]
    mean, std = X.mean(axis=0), X.std(axis=0)
    Z, Zn = (X - mean) / std, (table[new, 2:] - mean) / std
    d = X.shape[1]
    # Standardized, a record's squared length averages the number of measurements.
    average = np.mean(np.sum(Z**2, axis=1))
    assert np.isclose(average, d, rtol=1e-12)
    lengths = d * float(SHIFT) ** 2
    far_spacing = np.spacing(lengths)
    ulp = np.spacing(2 * average)
    return {
        "new": str(len(Zn)),
        "records": str(len(Z)),
        "measurements": str(d),
        "k": str(K),
        "shift": f"{SHIFT:,}",
        "lengths": power_of_ten(lengths, 0),
        "far_spacing": f"{far_spacing:.0f}",
        "share_below": f"{np.mean(cdist(Zn, Z) ** 2 < far_spacing):.0%}",
        "average_length": f"{average:.0f}",
        "twice": f"{2 * average:.0f}",
        "ulp": power_of_ten(ulp, 1),
        "ulp_root": power_of_ten(np.sqrt(ulp), 1),
        "lookups": str(LOOKUPS),
        "big_records": f"{RECORDS:,}",
        "budget_mb": f"{BUDGET / 1e6:.0f}",
        "matrix_mb": f"{LOOKUPS * RECORDS * 8 / 1e6:.0f}",
        "full_mb": f"{LOOKUPS * RECORDS * d * 8 / 1e6:.0f}",
    }
