"""Naming each bean's variety from the beans most like it."""

import numpy as np

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


def nearest(train, batch, k):
    """For each bean of batch, the rows of train of its k nearest beans, nearest first, a tie
    in distance going to the earlier row."""
    rows = []
    for bean in batch:
        distances = ((train - bean) ** 2).sum(axis=1)
        rows.append(np.argsort(distances, kind="stable")[:k])
    return np.array(rows)


def vote(varieties, neighbours):
    """Each bean's variety: the most common among its neighbours, a tie going to the variety
    of the nearest of the tied beans."""
    chosen = []
    for named in varieties[neighbours]:
        names, counts = np.unique(named, return_counts=True)
        tied = names[counts == counts.max()]
        chosen.append(next(name for name in named if name in tied))
    return np.array(chosen)


def sort_beans(train, varieties, batch, k):
    """Each bean of batch named by its k nearest training beans, scaled by the training beans'
    statistics."""
    train_scaled, batch_scaled = scale(train, batch)
    return vote(varieties, nearest(train_scaled, batch_scaled, k))


def choose_k(train, varieties, validation, validation_varieties, ks):
    """The share of the validation beans each k of ks names right, and the k that names the
    most, the smallest of any tied."""
    train_scaled, validation_scaled = scale(train, validation)
    neighbours = nearest(train_scaled, validation_scaled, max(ks))
    shares = [
        (vote(varieties, neighbours[:, :k]) == validation_varieties).mean() for k in ks
    ]
    best = max(shares)
    return shares, min(k for k, share in zip(ks, shares) if share == best)


class Line:
    """The sorting line, set up once from the training beans and their varieties, with k
    neighbours voting on each bean."""

    def __init__(self, train, varieties, k):
        self.mean, self.sd = np.mean(train, axis=0), np.std(train, axis=0)
        self.train = (train - self.mean) / self.sd
        self.varieties, self.k = varieties, k
        # The reach, squared: the farthest any training bean is from its nearest other.
        nearest_other = []
        for i, bean in enumerate(self.train):
            distances = ((self.train - bean) ** 2).sum(axis=1)
            distances[i] = np.inf
            nearest_other.append(distances.min())
        self.reach = max(nearest_other)

    def sort(self, batch):
        """Each bean of batch named by its k nearest training beans: UNKNOWN when it is
        farther from its nearest training bean than any training bean is from its nearest
        other, UNSURE when no variety has more than half the votes."""
        named = []
        for bean in (batch - self.mean) / self.sd:
            distances = ((self.train - bean) ** 2).sum(axis=1)
            nearest_k = np.argsort(distances, kind="stable")[: self.k]
            names, counts = np.unique(self.varieties[nearest_k], return_counts=True)
            if distances.min() > self.reach:
                named.append("UNKNOWN")
            elif counts.max() * 2 <= self.k:
                named.append("UNSURE")
            else:
                named.append(names[np.argmax(counts)])
        return np.array(named, dtype=object)
