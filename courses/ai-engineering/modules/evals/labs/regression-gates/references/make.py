# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.5.4", "statsmodels==0.15.0"]
# [tool.uv]
# exclude-newer = "2026-10-19T00:00:00Z"
# ///
"""Records statsmodels' standard errors of two releases' scores and of their difference, and
the smallest effect a one-sided test finds, for the lab's tests. statsmodels' dependencies are
those released before 19 October 2026.

changes.json holds, for made-up scores of two releases on the same questions, several samples a
question, in made-up pages, each case's scores and pages; the standard error of each release's
mean question score, clustered by page as statsmodels clusters an ordinary least squares fit of a
constant by default; and the same for the questions' differences.

power.json holds, for made-up numbers of questions, levels and effect sizes, the power
statsmodels' NormalIndPower gives a one-sample, one-sided test.

    uv run make.py <folder to write in>
"""

import json
import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.power import NormalIndPower

CASES = 30


def clustered(values: np.ndarray, pages: list[str]) -> float:
    constant = np.ones((len(values), 1))
    fit = sm.OLS(values, constant).fit(
        cov_type="cluster",
        cov_kwds={"groups": np.unique(pages, return_inverse=True)[1]},
    )
    return float(fit.bse[0])


def changes() -> list[dict[str, object]]:
    rng = np.random.default_rng(8)
    cases = []
    for _ in range(CASES):
        groups = int(rng.integers(3, 30))
        sizes = rng.integers(1, 8, size=groups)
        pages = [
            f"page-{group}" for group, size in enumerate(sizes) for _ in range(size)
        ]
        pages = [pages[i] for i in rng.permutation(len(pages))]
        samples = int(rng.integers(1, 11))
        lean = {page: rng.random() for page in sorted(set(pages))}
        ease = np.array([lean[page] for page in pages])[:, None]
        drop = rng.random() * 0.2
        baseline = (rng.random((len(pages), samples)) < ease).astype(float)
        candidate = (rng.random((len(pages), samples)) < ease - drop).astype(float)
        cases.append(
            {
                "baseline": baseline.tolist(),
                "candidate": candidate.tolist(),
                "pages": pages,
                "baseline_error": clustered(baseline.mean(axis=1), pages),
                "candidate_error": clustered(candidate.mean(axis=1), pages),
                "change_error": clustered(
                    candidate.mean(axis=1) - baseline.mean(axis=1), pages
                ),
            }
        )
    return cases


def power() -> list[dict[str, float]]:
    rng = np.random.default_rng(9)
    cases = []
    for _ in range(CASES):
        questions = int(rng.integers(20, 2000))
        alpha = float(rng.choice([0.01, 0.05, 0.1]))
        effect = float(rng.uniform(0.5, 4) / np.sqrt(questions))
        found = NormalIndPower().power(
            effect_size=effect,
            nobs1=questions,
            alpha=alpha,
            ratio=0,
            alternative="larger",
        )
        cases.append(
            {
                "questions": questions,
                "alpha": alpha,
                "effect": effect,
                "power": float(found),
            }
        )
    return cases


def make(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, cases in (("changes.json", changes()), ("power.json", power())):
        with open(folder / name, "w", encoding="utf-8", newline="\n") as file:
            json.dump({"cases": cases}, file, indent=1)
            file.write("\n")


if __name__ == "__main__":
    make(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
