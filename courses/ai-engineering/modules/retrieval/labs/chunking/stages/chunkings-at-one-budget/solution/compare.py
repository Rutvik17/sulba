"""Chunkings compared by a search through each: the chunks most similar to a question,
taken until a budget of words, scored by the characters of its answer they hold."""

import numpy as np

from score import Place, iou, precision, recall


def ranked(question: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    """The rows of vectors, the most similar to the question first: by the dot product
    of their whole numbers, a tie going to the earlier row."""
    return np.argsort(-(vectors @ question), kind="stable")


def within(order: np.ndarray, words: list[int], budget: int) -> list[int]:
    """The rows in order, until the next would take their words past budget."""
    taken: list[int] = []
    total = 0
    for row in order.tolist():
        if total + words[row] > budget:
            break
        taken.append(row)
        total += words[row]
    return taken


def compared(
    questions: np.ndarray,
    answers: list[list[Place]],
    places: list[Place],
    vectors: np.ndarray,
    words: list[int],
    budget: int,
) -> tuple[float, float, float]:
    """The mean recall, precision and IoU over the questions of a search through the
    chunks: for each question, the chunks most similar to it, taken until budget
    words."""
    found = [
        [places[row] for row in within(ranked(question, vectors), words, budget)]
        for question in questions
    ]
    recalls, precisions, ious = zip(
        *(
            (recall(parts, chunks), precision(parts, chunks), iou(parts, chunks))
            for parts, chunks in zip(answers, found, strict=True)
        ),
        strict=True,
    )
    return float(np.mean(recalls)), float(np.mean(precisions)), float(np.mean(ious))
