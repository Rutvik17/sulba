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
