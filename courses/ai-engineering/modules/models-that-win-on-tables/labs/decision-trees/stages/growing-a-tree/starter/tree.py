# The columns the tree reads of each call: these numbers as they are, and these categories, a
# column for each of their categories.
NUMBERS = ["age", "campaign", "pdays", "previous"]
CATEGORIES = [
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "poutcome",
]


def encode(calls, categories):
    """The calls as an array: the number columns as they are, then a column for each category
    in categories, 1 for the calls in it and 0 for the rest."""
    raise NotImplementedError


def grow(X, said_yes, depth, min_leaf):
    """A tree grown on the rows of X, with at most depth splits from its root to a leaf."""
    raise NotImplementedError


def score(tree, X):
    """For each row of X, the share of yes in the leaf it reaches."""
    raise NotImplementedError
