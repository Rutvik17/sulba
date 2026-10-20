import csv
import os
import subprocess
import sys
from collections import Counter

import numpy as np
import pytest

from evalset import held_out
from testset import unique

with open("data/questions.csv", encoding="utf-8", newline="") as file:
    QUESTIONS = list(csv.DictReader(file))


@pytest.mark.id("tst_fkp7tp")
def test_pages_whole():
    """Moves each page whole"""
    questions = [
        {"question": f"q{n}", "page": f"va-{n // 3}", "domain": "va", "text": f"Q {n}"}
        for n in range(12)
    ]
    chosen = set(held_out(questions, 0.4, np.random.default_rng(0)))
    for page in {question["page"] for question in questions}:
        on_page = {q["question"] for q in questions if q["page"] == page}
        assert on_page <= chosen or not on_page & chosen


@pytest.mark.id("tst_xgq9ct")
def test_each_service():
    """Holds each service's share of its questions"""
    chosen = set(held_out(QUESTIONS, 0.5, np.random.default_rng(0)))
    kept = unique(QUESTIONS)
    for service, count in Counter(q["domain"] for q in kept).items():
        held = sum(q["question"] in chosen for q in kept if q["domain"] == service)
        assert 0.5 * count <= held < 0.5 * count + 10


@pytest.mark.id("tst_zcipf3")
def test_same_set_every_run():
    """Gives the same test set for the same seed in every run"""
    code = (
        "import csv, numpy as np\n"
        "from evalset import held_out\n"
        "rows = csv.DictReader(open('data/questions.csv', encoding='utf-8'))\n"
        "rows = [row for row in rows if row['domain'] == 'va']\n"
        "print(held_out(rows, 0.5, np.random.default_rng(0)))\n"
    )
    found = set()
    for seed in ("1", "2"):
        environment = {**os.environ, "PYTHONHASHSEED": seed}
        run = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=environment,
            check=True,
        )
        found.add(run.stdout)
    assert len(found) == 1
