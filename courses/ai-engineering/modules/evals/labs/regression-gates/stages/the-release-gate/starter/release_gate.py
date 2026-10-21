"""The help desk's release gate, as CI runs it on every release before it ships."""

import csv
import sys
from collections import defaultdict

import numpy as np

from gate import Verdict, gate
from samples import cites_answer

MOST = 100
SAMPLES = [1, 2, 3, 4, 5]


def scored(
    replies: list[dict[str, str]],
    relevant: dict[str, set[str]],
    questions: list[str],
    release: str,
    samples: list[int],
) -> dict[str, np.ndarray]:
    """Each of the release's scores, a row for each question and a column for each
    sample."""
    raise NotImplementedError


def check(
    baseline: dict[str, np.ndarray],
    candidate: dict[str, np.ndarray],
    pages: list[str],
    alpha: float,
) -> dict[str, Verdict]:
    """A verdict on each score, each at alpha over the number of scores."""
    raise NotImplementedError


def report(verdicts: dict[str, Verdict]) -> list[str]:
    """A line for each score, then the gate's decision."""
    raise NotImplementedError


def read(path: str) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def main(arguments: list[str]) -> int:
    """The gate on the candidate against the baseline, from a file of replies: prints the
    report and returns 1 when it stops the candidate and 0 when it ships."""
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
