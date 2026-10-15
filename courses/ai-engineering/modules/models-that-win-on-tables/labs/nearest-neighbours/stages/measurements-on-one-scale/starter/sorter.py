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
    raise NotImplementedError
