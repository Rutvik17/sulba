import numpy as np
from scipy.spatial.distance import cdist

PATH = "data/breast-cancer.csv"
# The search of the last stage: new samples looked up at once, among this many records.
LATER_NEW, LATER_RECORDS = 50, 10_000


def shares(A, B):
    """Each column's share of the squared distances from the rows of A to the rows of B."""
    by_column = np.array(
        [np.sum(cdist(A[:, [j]], B[:, [j]]) ** 2) for j in range(A.shape[1])]
    )
    return by_column / by_column.sum()


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        names = [
            name.replace("_", " ") for name in file.readline().strip().split(",")[2:]
        ]
    new = table[:, 0] == 1
    records, samples = table[~new, 2:], table[new, 2:]
    mean, std = records.mean(axis=0), records.std(axis=0)
    raw = shares(samples, records)
    standard = shares((samples - mean) / std, (records - mean) / std)
    areas = [names.index("mean area"), names.index("worst area")]
    top = np.argsort(-raw)[:2]
    # The two columns that make up most of the raw distance are the two area columns.
    assert sorted(top.tolist()) == sorted(areas)
    m, n, d = len(samples), len(records), records.shape[1]
    return {
        "new": str(m),
        "records": str(n),
        "measurements": str(d),
        "pairs": f"{m * n:,}",
        "worst_area_share": f"{raw[names.index('worst area')]:.1%}",
        "mean_area_share": f"{raw[names.index('mean area')]:.1%}",
        "area_share": f"{raw[areas].sum():.1%}",
        "high_name": names[int(np.argmax(standard))],
        "high_share": f"{standard.max():.1%}",
        "low_name": names[int(np.argmin(standard))],
        "low_share": f"{standard.min():.1%}",
        "even_share": f"{1 / d:.1%}",
        "middle_numbers": f"{m * n * d:,}",
        "middle_mb": f"{m * n * d * 8 / 1e6:.1f}",
        "later_new": str(LATER_NEW),
        "later_records": f"{LATER_RECORDS:,}",
        "later_mb": f"{LATER_NEW * LATER_RECORDS * d * 8 / 1e6:,.0f}",
    }
