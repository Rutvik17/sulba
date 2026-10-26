import pytest
from evals import Change
from report import PEAK, Release, Report, markdown, to_run


@pytest.mark.id("tst_pmi9zc")
def test_to_run():
    """Runs three unless its interval of the change in the share wrong lies above 0"""
    assert to_run(Change(0.089, 0.067)) == "five"
    assert to_run(Change(0.02, 0.05)) == "three"
    assert to_run(Change(-0.03, 0.01)) == "three"


@pytest.mark.id("tst_9832ut")
def test_markdown():
    """Writes the figures in the office's form"""
    releases = [
        Release("five", 0.3, 0.12, 0.58, 2.04, 11.24, 432.4, 0.5551),
        Release("three", 0.29, 0.21, 0.5, 1.5, 9.96, 501.0, 0.479),
    ]
    text = markdown(Report(224, releases, Change(0.0893, 0.0671), "five"))
    assert text == "\n".join(
        [
            "# The aid desk, measured",
            "",
            "Each release answered the office's 224 questions. Right cites the question's "
            "page, wrong cites only other pages, and to staff goes to the office's staff. The "
            "times are for 95% of replies, one at a time on the office's server, and the "
            f"busiest hour has {PEAK} questions.",
            "",
            "| Release | Right | Wrong | To staff | First piece | Whole reply | Replies an hour "
            "| Busiest hour |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            "| five | 30% | 12% | 58% | 2.0 s | 11.2 s | 432 | 56% |",
            "| three | 29% | 21% | 50% | 1.5 s | 10.0 s | 501 | 48% |",
            "",
            "With three passages, the share of answers that cite only other pages changes by "
            "+8.9 points, with a margin of 6.7 points at 95%. The office should run five "
            "passages.",
        ]
    )
