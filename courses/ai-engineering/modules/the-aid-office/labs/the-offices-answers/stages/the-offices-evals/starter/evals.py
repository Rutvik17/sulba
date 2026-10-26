from dataclasses import dataclass

OUTCOMES = ("right", "wrong", "staff")
# Each release by name, with how many of a question's passages it gives the model.
RELEASES = {"five": 5, "three": 3}


@dataclass(frozen=True)
class Change:
    change: float
    margin: float


def outcome(reply, shown, page):
    """How a reply went, shown giving the page of each passage the model was given and page
    the question's own: "staff" when the answer would go to staff, "right" when it cites the
    question's page, and "wrong" when it cites only others."""
    raise NotImplementedError


def outcomes(replies, shown, questions, release):
    """Each question's outcome in the release, in the order of questions, from the rows of
    replies.csv, shown.csv and questions.csv."""
    raise NotImplementedError


def shares(found):
    """The share of the outcomes that are each of OUTCOMES."""
    raise NotImplementedError


def change(baseline, candidate, pages, name, confidence):
    """The candidate's share of the outcome name less the baseline's, on the same questions,
    from each question's difference, with its margin at the confidence given, each page's
    questions counted together."""
    raise NotImplementedError
