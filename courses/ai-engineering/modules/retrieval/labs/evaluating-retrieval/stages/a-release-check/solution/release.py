"""The help desk's release check: whether a new search may replace the current one."""

from dataclasses import dataclass

import numpy as np

from compare import randomization_test
from measures import Measure, hit_rate, ndcg
from texts import as_seen, relevant_texts

K = 5
DEPTH = 10
REPEATS = 10_000
LEVEL = 0.05
# The most a service's hit rate may fall.
FALL = 0.03


@dataclass
class Release:
    """What a release check found: each search's hit rate at K and nDCG at DEPTH over every
    question, the current search's first; the p-value of the difference in hit rate; each
    service's two hit rates; the services whose hit rate falls by more than FALL; and
    whether the candidate ships."""

    hit_rate: tuple[float, float]
    ndcg: tuple[float, float]
    p: float
    services: dict[str, tuple[float, float]]
    held: list[str]
    ship: bool


def check(
    current: dict[str, list[str]],
    candidate: dict[str, list[str]],
    judgments: dict[str, set[str]],
    first: dict[str, str],
    services: dict[str, str],
    rng: np.random.Generator,
) -> Release:
    """Whether the candidate search may replace the current one, by their passages for the
    questions judged, as a reader sees them."""
    questions = list(judgments)
    answers = [relevant_texts(judgments[question], first) for question in questions]

    def values(run: dict[str, list[str]], measure: Measure, k: int) -> np.ndarray:
        return np.array(
            [
                measure(as_seen(run.get(question, []), first), relevant, k)
                for question, relevant in zip(questions, answers, strict=True)
            ]
        )

    now, new = values(current, hit_rate, K), values(candidate, hit_rate, K)
    p = randomization_test(new, now, REPEATS, rng)
    by_service = {}
    for service in sorted({services[question] for question in questions}):
        rows = [
            at for at, question in enumerate(questions) if services[question] == service
        ]
        by_service[service] = (float(now[rows].mean()), float(new[rows].mean()))
    held = [service for service, (was, will) in by_service.items() if was - will > FALL]
    hit = (float(now.mean()), float(new.mean()))
    return Release(
        hit_rate=hit,
        ndcg=(
            float(values(current, ndcg, DEPTH).mean()),
            float(values(candidate, ndcg, DEPTH).mean()),
        ),
        p=p,
        services=by_service,
        held=held,
        ship=hit[1] > hit[0] and p < LEVEL and not held,
    )
