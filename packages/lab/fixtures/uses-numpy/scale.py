import numpy as np


def standardize(values):
    return (values - values.mean()) / values.std(ddof=1)
