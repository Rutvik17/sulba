def match_probability(pairs, temperature=1.0, shift=0.0):
    """Each pair's probability of an exact match, from its Yes and No logits."""
    raise NotImplementedError


def calibrate(pairs):
    """The temperature and shift that give match_probability the least log loss on the
    pairs' labels."""
    raise NotImplementedError
