def prune(tree, depth):
    """A copy of tree cut at depth, with each node that deep a leaf."""
    raise NotImplementedError


def choose_depth(train, said_yes, validation, validation_yes, depths, min_leaf):
    """The AUC of the tree at each of depths on the training calls and on the validation
    calls, and the smallest depth with the best validation AUC."""
    raise NotImplementedError
