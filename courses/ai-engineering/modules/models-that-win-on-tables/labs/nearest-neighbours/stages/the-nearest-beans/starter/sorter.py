def nearest(train, batch, k):
    """For each bean of batch, the rows of train of its k nearest beans, nearest first, a tie
    in distance going to the earlier row."""
    raise NotImplementedError


def vote(varieties, neighbours):
    """Each bean's variety: the most common among its neighbours, a tie going to the variety
    of the nearest of the tied beans."""
    raise NotImplementedError
