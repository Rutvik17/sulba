import warnings

import numpy as np

PATH = "data/breast-cancer.csv"
K = 5


def scaled(X, reference):
    """X on the reference's scale, a column with no spread divided by 1."""
    mean, std = reference.mean(axis=0), reference.std(axis=0)
    return (X - mean) / np.where(std == 0, 1, std)


def nearest(A, B):
    """The K nearest rows of B to each row of A, nearest first."""
    D = np.sqrt(np.sum((A[:, None, :] - B[None, :, :]) ** 2, axis=-1))
    return np.argsort(D, axis=1, kind="stable")[:, :K]


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        names = file.readline().strip().split(",")[2:]
    is_new = table[:, 0] == 1
    records, diagnoses = table[~is_new, 2:], table[~is_new, 1]
    new, own = table[is_new, 2:], table[is_new, 1]
    right = nearest(scaled(new, records), scaled(records, records))
    share = diagnoses[right].mean(axis=1)

    # Each problem on its own, with the rest of the code right.
    in_batch = nearest(scaled(new, new), scaled(records, records))
    batch_wrong = sum(set(a) != set(b) for a, b in zip(in_batch, right, strict=True))
    alone = [
        nearest(scaled(new[[i]], new[[i]]), scaled(records, records))[0]
        for i in range(len(new))
    ]
    # Alone, a sample has no spread, so every one lands on the records' mean.
    assert len({tuple(found) for found in alone}) == 1
    centre = nearest(np.zeros((1, records.shape[1])), scaled(records, records))[0]
    assert np.array_equal(alone[0], centre)

    constant = np.full((len(records), 1), 7.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with_it = np.hstack([records, constant])
        mean, std = with_it.mean(axis=0), with_it.std(axis=0)
        standardized = (with_it - mean) / std
    # Dividing by a standard deviation of 0 makes every distance nan.
    assert np.all(np.isnan(standardized[:, -1]))

    worst_area = names.index("worst_area")
    before = records[0, worst_area]
    after = (before - records[:, worst_area].mean()) / records[:, worst_area].std()

    malignant = own == 1
    return {
        "k": str(K),
        "new": str(len(new)),
        "batch_wrong": str(batch_wrong),
        "worst_area_before": f"{before:,.0f}",
        "worst_area_after": f"{after:.2f}",
        "batch_share": f"{share.mean():.1%}",
        "all_malignant": str(int(np.sum(malignant & (share == 1)))),
        "none_malignant": str(int(np.sum(~malignant & (share == 0)))),
    }
