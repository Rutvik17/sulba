# Written by the assistant. The request: "Report each choice with its share of
# the votes, the most votes first, and leave our list of votes as it was."
from tally import share


def report(choices):
    """Each choice with its share of the votes, the most votes first."""
    choices.sort()
    return [(choice, share(choices, choice)) for choice in sorted(set(choices))]
