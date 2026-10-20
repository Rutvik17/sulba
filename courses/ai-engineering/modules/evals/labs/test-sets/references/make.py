# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.5.4", "statsmodels==0.15.0"]
# [tool.uv]
# exclude-newer = "2026-10-19T00:00:00Z"
# ///
"""Records statsmodels' standard errors of a mean score and its intervals, for the lab's tests.
statsmodels' dependencies are those released before 19 October 2026.

errors.json holds, for made-up scores in made-up clusters, each case's scores and clusters, the
standard error of their mean from an ordinary least squares fit of a constant, its standard
error clustered as statsmodels clusters it by default, and the 95% and 90% intervals each gives
from the normal distribution.

    uv run make.py <folder to write in>
"""

import json
import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm

CASES = 40


def recorded(scores: np.ndarray, clusters: list[str]) -> dict[str, object]:
    constant = np.ones((len(scores), 1))
    plain = sm.OLS(scores, constant).fit(use_t=False)
    grouped = sm.OLS(scores, constant).fit(
        cov_type="cluster",
        cov_kwds={"groups": np.unique(clusters, return_inverse=True)[1]},
    )
    out: dict[str, object] = {
        "scores": scores.tolist(),
        "clusters": clusters,
        "standard_error": float(plain.bse[0]),
        "clustered_standard_error": float(grouped.bse[0]),
    }
    for confidence in (0.95, 0.9):
        for name, fit in (("interval", plain), ("clustered_interval", grouped)):
            low, high = fit.conf_int(alpha=1 - confidence)[0]
            out[f"{name}_{round(confidence * 100)}"] = [float(low), float(high)]
    return out


def make(folder: Path) -> None:
    rng = np.random.default_rng(6)
    cases = []
    for number in range(CASES):
        groups = int(rng.integers(3, 40))
        sizes = rng.integers(1, 11, size=groups)
        clusters = [
            f"page-{group}" for group, size in enumerate(sizes) for _ in range(size)
        ]
        order = rng.permutation(len(clusters))
        clusters = [clusters[i] for i in order]
        lean = {name: rng.random() for name in sorted(set(clusters))}
        if number % 2:
            scores = np.array([float(rng.random() < lean[name]) for name in clusters])
        else:
            scores = np.array([rng.random() * lean[name] for name in clusters])
        if scores.std() == 0:
            scores[0] = 1 - scores[0]
        cases.append(recorded(scores, clusters))
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "errors.json", "w", encoding="utf-8", newline="\n") as file:
        json.dump({"cases": cases}, file, indent=1)
        file.write("\n")


if __name__ == "__main__":
    make(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent)
