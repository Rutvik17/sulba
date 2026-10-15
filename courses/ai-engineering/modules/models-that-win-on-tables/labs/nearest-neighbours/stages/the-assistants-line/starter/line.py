"""The sorting line: each bean named by the training beans most like it."""

import numpy as np

# The neighbours that vote on each bean, as chosen on the validation beans.
K = 12


def named_by(varieties, nearest):
    """The variety most of the nearest beans have, a tie going to the nearest of the tied."""
    names, counts = np.unique(varieties[nearest], return_counts=True)
    return names[np.argmax(counts)]


def sort_batch(train, varieties, batch, k=K):
    """Each bean of batch named by its k nearest training beans, or None for a bean the camera
    measured only in part."""
    train_scaled = (train - train.mean(axis=0)) / train.std(axis=0)
    batch_scaled = (batch - batch.mean(axis=0)) / batch.std(axis=0)
    named = []
    for bean in batch_scaled:
        distances = ((train_scaled - bean) ** 2).sum(axis=1)
        named.append(named_by(varieties, np.argsort(distances, kind="stable")[:k]))
    return np.array(named, dtype=object)


def estimated_accuracy(train, varieties, k=K):
    """The share of the training beans named right, each by its k nearest other training
    beans: the line's expected accuracy on beans it hasn't seen."""
    mean, sd = train.mean(axis=0), train.std(axis=0)
    scaled = (train - mean) / sd
    right = 0
    for i, bean in enumerate(scaled):
        distances = ((scaled - bean) ** 2).sum(axis=1)
        nearest = np.argsort(distances, kind="stable")[:k]
        right += named_by(varieties, nearest) == varieties[i]
    return right / len(train)
