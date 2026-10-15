"""The new supplier's harvest: the two directions of the inspectors' plot, the groups of the
training beans and their names, and the name of each bean of the harvest."""

import numpy as np
from sklearn.cluster import KMeans

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
# The groups, the k-means++ starts k-means takes the best of, and the seed of the starts.
K, STARTS, SEED = 9, 10, 0


def scale(train, other):
    """train and other, each measurement standardized by train's mean and standard
    deviation."""
    mean = np.mean(train, axis=0)
    sd = np.std(train, axis=0)
    return (train - mean) / sd, (other - mean) / sd


def plot_axes(Z):
    """The two directions along which the rows of Z vary most, one to a row, and the share of
    the variance they carry."""
    variances, vectors = np.linalg.eigh(np.cov(Z, rowvar=False))
    return vectors[:, [-1, -2]].T, variances[-2:].sum() / variances.sum()


def fit_groups(train):
    """k-means on the training beans' scaled measurements, the best of STARTS starts."""
    Z, _ = scale(train, train)
    return KMeans(K, n_init=STARTS, random_state=SEED).fit(Z)


def group_names(labels, varieties):
    """Each group's name: the commonest variety among its training beans."""
    names = []
    for group in range(labels.max() + 1):
        found = varieties[labels == group]
        names.append(max(set(found), key=list(found).count))
    return names


def harvest_groups(model, train, harvest):
    """Each harvest bean's group: the group whose centre is nearest it."""
    _, H = scale(train, harvest)
    return model.predict(H)


def run(train, varieties, harvest):
    """The plot's directions and the share of the variance they carry, and the name of each
    harvest bean's group."""
    Z, _ = scale(train, train)
    directions, share = plot_axes(Z)
    model = fit_groups(train)
    names = group_names(model.labels_, varieties)
    groups = harvest_groups(model, train, harvest)
    return directions, share, [names[group] for group in groups]
