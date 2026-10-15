def standardize(X, mean, std):
    """X with each column less its mean and divided by its standard deviation, as
    StandardScaler's transform gives it: a column whose standard deviation is 0 is
    divided by 1."""
    raise NotImplementedError


def distances(A, B):
    """The Euclidean distance from each row of A to each row of B, as an array of shape
    (len(A), len(B))."""
    raise NotImplementedError
