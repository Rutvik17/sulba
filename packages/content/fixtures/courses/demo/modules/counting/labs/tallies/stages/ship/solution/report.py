# Written by the assistant, then fixed in review. The request: "Report each choice
# with its share of the votes, the most votes first, and leave our list of votes as
# it was."
from tally import share


def report(choices):
    """Each choice with its share of the votes, the most votes first."""
    shares = [(choice, share(choices, choice)) for choice in set(choices)]
    return sorted(shares, key=lambda pair: (-pair[1], pair[0]))


def leader(choices):
    """The choice with the most votes."""
    return max(set(choices), key=choices.count)
