import math

# Signing callers in through the office's directory, as tests/test_estimates.py and the brief
# give it.
LOW, LIKELY, HIGH = 3, 5, 12


def figures():
    p80 = HIGH - math.sqrt(0.2 * (HIGH - LOW) * (HIGH - LIKELY))
    return {
        "low": f"{LOW}",
        "likely": f"{LIKELY}",
        "high": f"{HIGH}",
        "mean": f"{(LOW + LIKELY + HIGH) / 3:.2f}",
        "p80": f"{p80:.2f}",
    }
