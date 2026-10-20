import numpy as np
import pytest

from evalset import report
from margin import clustered_standard_error, margin


@pytest.mark.id("tst_9qibnm")
def test_pages_counted_together():
    """Counts each page's questions together in the margin of error"""
    passed = {f"q{n}": n % 4 != 0 for n in range(1, 25)}
    pages = {f"q{n}": f"dmv-{(n - 1) // 6}" for n in range(1, 25)}
    _, reach = report(passed, pages)
    scores = np.array([float(passed[name]) for name in passed])
    expected = margin(clustered_standard_error(scores, list(pages.values())), 0.95)
    assert reach == pytest.approx(expected)
