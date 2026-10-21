"""A release's score on the test set when each question is answered several times."""

import re

import numpy as np

CITED = re.compile(r"\[(p\d+)\]")


def cites_answer(reply: str, relevant: set[str]) -> float:
    """1 if the reply cites a passage that holds the answer, and 0 if not."""
    return float(any(name in relevant for name in CITED.findall(reply)))


def scores(
    replies: list[dict[str, str]],
    relevant: dict[str, set[str]],
    questions: list[str],
    release: str,
    samples: list[int],
) -> np.ndarray:
    """Each reply of the release scored, a row for each question and a column for each
    sample, in their orders."""
    found = {
        (row["question"], int(row["sample"])): row["reply"]
        for row in replies
        if row["release"] == release
    }
    return np.array(
        [
            [
                cites_answer(found[question, sample], relevant[question])
                for sample in samples
            ]
            for question in questions
        ]
    )


def standard_error(scores: np.ndarray, pages: list[str]) -> float:
    """The standard error of the release's score, the mean of its questions' means, with
    each page's questions counted together."""
    means = scores.mean(axis=1)
    sums: dict[str, float] = {}
    for page, residual in zip(pages, means - means.mean(), strict=True):
        sums[page] = sums.get(page, 0.0) + float(residual)
    groups = len(sums)
    spread = sum(total**2 for total in sums.values())
    return float(np.sqrt(groups / (groups - 1) * spread) / len(means))


def sampling_variance(scores: np.ndarray) -> float:
    """What sampling adds to the variance of a question's mean: the mean over the questions
    of their samples' variance, over the number of samples."""
    return float(scores.var(axis=1, ddof=1).mean() / scores.shape[1])
