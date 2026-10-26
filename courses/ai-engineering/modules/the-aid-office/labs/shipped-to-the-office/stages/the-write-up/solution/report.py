import csv
from dataclasses import dataclass
from pathlib import Path

from capacity import busy, per_hour, percentile, read
from evals import RELEASES, Change, change, outcomes, shares

# The questions the office's chat had in its busiest hour last term.
PEAK = 240
CONFIDENCE = 0.95
# The share of replies the times cover.
SLOWEST = 0.95


@dataclass(frozen=True)
class Release:
    name: str
    right: float
    wrong: float
    staff: float
    first: float
    whole: float
    hourly: float
    busy: float


@dataclass(frozen=True)
class Report:
    questions: int
    releases: list[Release]
    wrong: Change
    chosen: str


def rows(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def to_run(wrong):
    """The release the office should run, given three's share wrong less five's: three, the
    faster, unless its interval lies wholly above 0."""
    return "five" if wrong.change - wrong.margin > 0 else "three"


def report(data=Path("data")):
    """The figures the write-up gives, from the recorded replies and their timings."""
    replies = rows(data / "replies.csv")
    shown = rows(data / "shown.csv")
    questions = rows(data / "questions.csv")
    timings = read(data / "timings.csv")
    found = {name: outcomes(replies, shown, questions, name) for name in RELEASES}
    releases = []
    for name in RELEASES:
        share = shares(found[name])
        times = [each for each in timings if each.release == name]
        hourly = per_hour([each.whole for each in times])
        releases.append(
            Release(
                name,
                share["right"],
                share["wrong"],
                share["staff"],
                percentile([each.first for each in times], SLOWEST),
                percentile([each.whole for each in times], SLOWEST),
                hourly,
                busy(PEAK, hourly),
            )
        )
    pages = [row["page"] for row in questions]
    wrong = change(found["five"], found["three"], pages, "wrong", CONFIDENCE)
    return Report(len(questions), releases, wrong, to_run(wrong))


def markdown(report):
    """The write-up for the office, in Markdown."""
    table = [
        "| Release | Right | Wrong | To staff | First piece | Whole reply | Replies an hour "
        "| Busiest hour |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for each in report.releases:
        table.append(
            f"| {each.name} | {each.right:.0%} | {each.wrong:.0%} | {each.staff:.0%} "
            f"| {each.first:.1f} s | {each.whole:.1f} s | {each.hourly:,.0f} "
            f"| {each.busy:.0%} |"
        )
    return "\n".join(
        [
            "# The aid desk, measured",
            "",
            f"Each release answered the office's {report.questions} questions. Right cites "
            "the question's page, wrong cites only other pages, and to staff goes to the "
            "office's staff. The times are for 95% of replies, one at a time on the office's "
            f"server, and the busiest hour has {PEAK} questions.",
            "",
            *table,
            "",
            f"With three passages, the share of answers that cite only other pages changes by "
            f"{report.wrong.change * 100:+.1f} points, with a margin of "
            f"{report.wrong.margin * 100:.1f} points at {CONFIDENCE:.0%}. The office should "
            f"run {report.chosen} passages.",
        ]
    )
