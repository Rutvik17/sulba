"""A release's score on the test set when each question is answered several times."""

import re

import numpy as np

CITED = re.compile(r"\[(p\d+)\]")


def cites_answer(reply: str, relevant: set[str]) -> float:
    """1 if the reply cites a passage that holds the answer, and 0 if not."""
    raise NotImplementedError


def scores(
    replies: list[dict[str, str]],
    relevant: dict[str, set[str]],
    questions: list[str],
    release: str,
    samples: list[int],
) -> np.ndarray:
    """Each reply of the release scored, a row for each question and a column for each
    sample, in their orders."""
    raise NotImplementedError


def standard_error(scores: np.ndarray, pages: list[str]) -> float:
    """The standard error of the release's score, the mean of its questions' means, with
    each page's questions counted together."""
    raise NotImplementedError


def sampling_variance(scores: np.ndarray) -> float:
    """What sampling adds to the variance of a question's mean: the mean over the questions
    of their samples' variance, over the number of samples."""
    raise NotImplementedError
