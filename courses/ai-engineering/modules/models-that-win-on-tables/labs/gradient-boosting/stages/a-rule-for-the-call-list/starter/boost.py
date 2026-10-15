# LightGBM's rounds at most, its learning rate and leaves a tree, and the rounds in a row
# without a lower validation log loss after which it stops.
ROUNDS, RATE, LEAVES, PATIENCE = 500, 0.05, 8, 30


def frame(calls):
    """The columns the model reads: the numbers as they are, then each category column as a
    pandas category."""
    raise NotImplementedError


def call_model(train, validation, rule):
    """LightGBM on the training calls, stopped early on the validation calls, and with rule, a
    chance that never rises with campaign."""
    raise NotImplementedError


def raised(model, clients, more):
    """How many clients the model would give a higher chance after up to more calls more."""
    raise NotImplementedError
