# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6", "scipy==1.18.0"]
# [tool.uv]
# exclude-newer = "2026-10-21T00:00:00Z"
# ///
"""Records how NumPy and SciPy put a percentile and its interval on a set of values, for the
lab's tests.

quantiles.json holds, for each case, its values, the quantile asked for and the confidence, with
NumPy's quantile of the values, as its default method gives it, and SciPy's interval for the
quantile from quantile_test's confidence_interval, an end SciPy leaves nan as null. The values
are drawn from an exponential distribution, rounded to three places, a few cases with ties, for
from 1 to 120 values.

    uv run make.py <folder to write in>
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

SIZES = (1, 2, 3, 5, 8, 13, 20, 50, 120)
QUANTILES = (0.5, 0.9, 0.99)
CONFIDENCES = (0.9, 0.95)


def number(value: float) -> float | None:
    return None if math.isnan(value) else float(value)


def cases() -> list[dict]:
    rng = np.random.default_rng(20261022)
    out = []
    for size in SIZES:
        for tied in (False, True):
            values = np.round(rng.exponential(60, size), 3)
            if tied:
                values = np.round(values / 20) * 20
            for p in QUANTILES:
                for confidence in CONFIDENCES:
                    test = stats.quantile_test(values, q=0, p=p)
                    interval = test.confidence_interval(confidence)
                    out.append(
                        {
                            "values": values.tolist(),
                            "p": p,
                            "confidence": confidence,
                            "quantile": float(np.quantile(values, p)),
                            "low": number(interval.low),
                            "high": number(interval.high),
                        }
                    )
    return out


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    (folder / "quantiles.json").write_text(
        json.dumps({"cases": cases()}) + "\n", encoding="utf-8"
    )
