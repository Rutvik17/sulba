# The k-means++ starts each grouping takes the best of.
STARTS = 10


def named_groups(train, varieties, k, seed):
    """k-means into k groups of the scaled training beans, the best of STARTS starts from
    seed, and each group's name: the commonest variety among its beans."""
    raise NotImplementedError


def fewest_groups(train, varieties, seed):
    """The named groups of the fewest k, from the number of varieties up, whose names take in
    every variety."""
    raise NotImplementedError


def name_beans(model, names, train, batch):
    """Each bean of batch named by the group whose centre is nearest it."""
    raise NotImplementedError


def make_up(model, names, train, harvest):
    """Each name's share of the harvest's beans, the names in alphabetical order."""
    raise NotImplementedError
