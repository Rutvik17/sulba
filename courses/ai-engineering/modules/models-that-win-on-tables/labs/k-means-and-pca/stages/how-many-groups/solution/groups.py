"""Finding the groups in the beans' shapes."""

import numpy as np
from scipy.spatial.distance import cdist

# The measurements of each bean's shape, in the columns of data/beans.csv.
MEASUREMENTS = [
    "Area",
    "Perimeter",
    "MajorAxisLength",
    "MinorAxisLength",
    "AspectRatio",
    "Eccentricity",
    "ConvexArea",
    "EquivDiameter",
    "Extent",
    "Solidity",
    "Roundness",
    "Compactness",
    "ShapeFactor1",
    "ShapeFactor2",
    "ShapeFactor3",
    "ShapeFactor4",
]


def scale(train, other):
    """train and other, each measurement standardized by train's mean and standard
    deviation."""
    mean = np.mean(train, axis=0)
    sd = np.std(train, axis=0)
    return (train - mean) / sd, (other - mean) / sd


def components(Z):
    """The variances along the principal components of the rows of Z, from the largest down,
    and the components, one to a row."""
    variances, vectors = np.linalg.eigh(np.cov(Z, rowvar=False))
    variances, directions = variances[::-1], vectors[:, ::-1].T
    rows = np.arange(len(directions))
    signs = np.sign(directions[rows, np.abs(directions).argmax(axis=1)])
    return variances, directions * signs[:, np.newaxis]


def project(Z, directions):
    """Each row's score on each direction."""
    return Z @ directions.T


def assign(Z, centres):
    """Each row's nearest centre, as the index of its row in centres."""
    distances = ((Z[:, np.newaxis, :] - centres[np.newaxis, :, :]) ** 2).sum(axis=2)
    return distances.argmin(axis=1)


def k_means(Z, centres):
    """The groups k-means finds from these centres: each row's group, the groups' centres
    and their inertia."""
    labels = assign(Z, centres)
    groups = range(len(centres))
    while True:
        centres = np.array([Z[labels == group].mean(axis=0) for group in groups])
        moved = assign(Z, centres)
        if np.array_equal(moved, labels):
            break
        labels = moved
    inertia = float(((Z - centres[labels]) ** 2).sum())
    return labels, centres, inertia


def plus_plus(Z, k, rng):
    """k starting centres drawn from the rows of Z by k-means++, one to a row."""
    centres = [Z[rng.integers(len(Z))]]
    nearest = ((Z - centres[0]) ** 2).sum(axis=1)
    while len(centres) < k:
        centres.append(Z[rng.choice(len(Z), p=nearest / nearest.sum())])
        nearest = np.minimum(nearest, ((Z - centres[-1]) ** 2).sum(axis=1))
    return np.array(centres)


def best_of(Z, k, starts, rng):
    """k-means from this many k-means++ starts: the groups of the one with the least
    inertia."""
    best = None
    for _ in range(starts):
        found = k_means(Z, plus_plus(Z, k, rng))
        if best is None or found[2] < best[2]:
            best = found
    return best


def silhouette(Z, labels):
    """The mean silhouette of the rows of Z in these groups."""
    members = labels[:, np.newaxis] == np.arange(labels.max() + 1)
    sums = cdist(Z, Z) @ members
    sizes = members.sum(axis=0)
    rows = np.arange(len(Z))
    within = sums[rows, labels] / (sizes[labels] - 1)
    means = sums / sizes
    means[rows, labels] = np.inf
    nearest = means.min(axis=1)
    return float(np.mean((nearest - within) / np.maximum(within, nearest)))
