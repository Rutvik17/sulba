# /// script
# requires-python = "==3.14.2"
# dependencies = ["numpy==2.4.6"]
# ///
"""Writes `office_records.py`, Harbor College's aid office's records for the Intermediate
capstone: fictional students, each with whether the office has their FAFSA, and the federal aid
each with a FAFSA was awarded for 2026-27, all drawn at random (NumPy's default_rng, seed 0), and
each student's college email, in the domain RFC 2606 keeps for examples.

Each award holds the dollars offered, the dollars the student accepted, all of those offered
seven times in ten and otherwise half or none, and the dollars paid, none, half or all of those
accepted.

    uv run tools/datasets/aid_records.py <file to write>
"""

import sys
from pathlib import Path

import numpy as np

STUDENTS = 60
DOMAIN = "harbor.example"
# The awards, each with the dollars it may be offered in and the share of students with a FAFSA
# who are offered it.
AWARDS = {
    "Federal Pell Grant": (list(range(1500, 7001, 100)), 0.6),
    "Direct Subsidized Loan": ([3500, 4500, 5500], 0.7),
    "Direct Unsubsidized Loan": ([2000], 0.6),
    "Federal Work-Study": ([1500, 2000, 2500, 3000], 0.3),
}
SHARES = [0.0, 0.5, 1.0]
HEADER = '''"""The aid office's records for 2026-27, for fictional students, written by
tools/datasets/aid_records.py: each student's id and whether the office has their FAFSA, each
award with the dollars offered, accepted and paid, and each student's college email."""

'''


def build(out: Path) -> None:
    rng = np.random.default_rng(0)
    students, awards = [], []
    for number in range(1, STUDENTS + 1):
        student = f"S{1000 + number}"
        has_fafsa = bool(rng.random() < 0.9)
        students.append((student, has_fafsa))
        if not has_fafsa:
            continue
        for award, (amounts, share) in AWARDS.items():
            if rng.random() >= share:
                continue
            offered = int(rng.choice(amounts))
            accepted = offered if rng.random() < 0.7 else int(offered * rng.choice([0, 0.5]))
            paid = int(accepted * rng.choice(SHARES))
            awards.append((student, award, offered, accepted, paid))
    lines = [HEADER, "STUDENTS = [\n"]
    lines += [f'    ("{student}", {has_fafsa}),\n' for student, has_fafsa in students]
    lines += ["]\n", "AWARDS = [\n"]
    lines += [f'    ("{row[0]}", "{row[1]}", {row[2]}, {row[3]}, {row[4]}),\n' for row in awards]
    lines += ["]\n", "EMAILS = [\n"]
    lines += [f'    ("{student}", "{student.lower()}@{DOMAIN}"),\n' for student, _ in students]
    lines += ["]\n"]
    out.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    build(Path(sys.argv[1]))
