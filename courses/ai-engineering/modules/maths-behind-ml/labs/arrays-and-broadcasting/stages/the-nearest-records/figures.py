import numpy as np
from scipy.spatial.distance import cdist

K = 5


def nearest_shares(A, B, diagnoses):
    """For each row of A, its K nearest rows of B, and the share of them that are malignant."""
    near = np.argsort(cdist(A, B), axis=1, kind="stable")[:, :K]
    return near, diagnoses[near].mean(axis=1)


def figures():
    table = np.loadtxt("data/breast-cancer.csv", delimiter=",", skiprows=1)
    new = table[:, 0] == 1
    records, diagnoses = table[~new, 2:], table[~new, 1]
    samples, own = table[new, 2:], table[new, 1]
    mean, std = records.mean(axis=0), records.std(axis=0)
    near, share = nearest_shares(
        (samples - mean) / std, (records - mean) / std, diagnoses
    )
    raw_near, _ = nearest_shares(samples, records, diagnoses)
    malignant = own == 1
    return {
        "k": str(K),
        "new": str(len(samples)),
        "same": f"{np.mean(diagnoses[near] == own[:, None]):.1%}",
        "raw_same": f"{np.mean(diagnoses[raw_near] == own[:, None]):.1%}",
        "malignant": str(int(malignant.sum())),
        "malignant_mostly": str(int(np.sum(share[malignant] > 0.5))),
        "malignant_mean": f"{share[malignant].mean():.1%}",
        "benign": str(int((~malignant).sum())),
        "benign_mostly": str(int(np.sum(share[~malignant] < 0.5))),
        "benign_mean": f"{share[~malignant].mean():.1%}",
    }
