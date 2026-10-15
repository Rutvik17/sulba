import numpy as np

PATH = "data/breast-cancer.csv"


def figures():
    table = np.loadtxt(PATH, delimiter=",", skiprows=1)
    with open(PATH) as file:
        names = [
            name.replace("_", " ") for name in file.readline().strip().split(",")[2:]
        ]
    in_records = table[:, 0] == 0
    X, y = table[in_records, 2:], table[in_records, 1]
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    mu0, mu1 = Z[y == 0].mean(axis=0), Z[y == 1].mean(axis=0)
    length0, length1 = np.linalg.norm(mu0), np.linalg.norm(mu1)
    cosine = mu0 @ mu1 / (length0 * length1)
    gap = np.abs(mu1 - mu0)
    order = np.argsort(-gap)
    malignant, benign = int(y.sum()), int((y == 0).sum())
    # Standardized records average 0, so the two class means balance, weighted by their counts.
    assert np.allclose(malignant * mu1 + benign * mu0, 0, atol=1e-9)
    return {
        "records": str(len(y)),
        "measurements": str(Z.shape[1]),
        "malignant": str(malignant),
        "benign": str(benign),
        "length1": f"{length1:.2f}",
        "length0": f"{length0:.2f}",
        "cosine": f"{cosine:.3f}",
        "ratio": f"{length0 / length1:.3f}",
        "count_ratio": f"{malignant / benign:.3f}",
        "gap1_name": names[order[0]],
        "gap1": f"{gap[order[0]]:.3f}",
        "gap2_name": names[order[1]],
        "gap2": f"{gap[order[1]]:.3f}",
        "gap3_name": names[order[2]],
        "gap3": f"{gap[order[2]]:.3f}",
        "least_name": names[order[-1]],
        "least": f"{gap[order[-1]]:.3f}",
    }
