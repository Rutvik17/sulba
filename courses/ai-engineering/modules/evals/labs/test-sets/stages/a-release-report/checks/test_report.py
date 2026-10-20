import math

import numpy as np
import pytest

from margin import clustered_standard_error, margin
from release import line, report

RNG = np.random.default_rng(11)
NAMES = [f"q{number}" for number in range(1, 121)]
PAGES = {
    name: f"{('dmv', 'ssa', 'va')[i % 3]}-{i // 9}" for i, name in enumerate(NAMES)
}
SERVICES = {name: page.split("-")[0] for name, page in PAGES.items()}
LEAN = {page: RNG.random() for page in sorted(set(PAGES.values()))}
RESULTS = {
    name: {
        "cites": bool(RNG.random() < 0.9),
        "cites_answer": bool(RNG.random() < LEAN[PAGES[name]]),
        "finished": bool(RNG.random() < 0.95),
    }
    for name in NAMES
}


def scores(names):
    return np.array([float(all(RESULTS[name].values())) for name in names])


@pytest.mark.id("tst_hgqcf9")
def test_every_check():
    """Counts a reply as passing only when it passes every check"""
    lines = report(RESULTS, PAGES, SERVICES, 0.05, 0.95)
    assert lines["all"].rate == pytest.approx(scores(NAMES).mean())


@pytest.mark.id("tst_sshiza")
def test_pages_together():
    """Counts each page's questions together in each margin"""
    lines = report(RESULTS, PAGES, SERVICES, 0.05, 0.95)
    error = clustered_standard_error(scores(NAMES), [PAGES[name] for name in NAMES])
    assert lines["all"].margin == pytest.approx(margin(error, 0.95))


@pytest.mark.id("tst_e8a81a")
def test_services_alone():
    """Gives each service the rate and margin of its own questions"""
    lines = report(RESULTS, PAGES, SERVICES, 0.05, 0.9)
    for service in ("dmv", "ssa", "va"):
        theirs = [name for name in NAMES if SERVICES[name] == service]
        error = clustered_standard_error(
            scores(theirs), [PAGES[name] for name in theirs]
        )
        assert lines[service].rate == pytest.approx(scores(theirs).mean())
        assert lines[service].margin == pytest.approx(margin(error, 0.9))
        assert lines[service].questions == len(theirs)


@pytest.mark.id("tst_xwc75g")
def test_enough_questions():
    """Asks for the fewest questions whose margin, at the same spread, is within the target"""
    for target in (0.03, 0.05, 0.12, 0.4):
        found = line(scores(NAMES), [PAGES[name] for name in NAMES], target, 0.95)
        n = len(NAMES)
        assert found.margin * math.sqrt(n / found.needed) <= target
        assert (
            found.needed == 1
            or found.margin * math.sqrt(n / (found.needed - 1)) > target
        )
