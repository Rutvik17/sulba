import base64
import json
import random
import shutil
import subprocess
import sys
import uuid
import zlib
from pathlib import Path
from typing import Any

import pytest

import sulba

PYTHON = Path(__file__).parents[1]

COUNT_TEST = '''import json

import pytest
from tally import count


@pytest.mark.id("tst_aaaaaa")
def test_count():
    """Counts the votes for each choice"""
    with open("data/votes.csv", encoding="utf-8") as file:
        votes = file.read().split()
    assert count(votes, "yes") == 2


@pytest.mark.id("tst_bbbbbb")
def test_reference():
    """Gives the recorded count"""
    with open("references/counts.json", encoding="utf-8") as file:
        assert count(["no"], "no") == json.load(file)["no"]
'''

SHARE_TEST = '''import pytest
from tally import share


@pytest.mark.id("tst_cccccc")
def test_share():
    """Gives each choice's share"""
    assert share(["yes", "no"], "yes") == 0.5
'''

REPORT = """def total(counts):
    return sum(counts.values())


def top(counts):
    return min(counts, key=counts.get)


def shares(counts):
    return {name: count / 10 for name, count in counts.items()}
"""

FIXED = REPORT.replace("min(counts", "max(counts").replace("count / 10", "count / total(counts)")

ASSISTANT_TEST = '''import pytest
from report import total


@pytest.mark.id("tst_dddddd")
def test_total():
    """Adds up every count"""
    assert total({"yes": 2, "no": 1}) == 3
'''

REPORT_CHECKS = """import pytest
from report import shares, top


@pytest.mark.id("tst_eeeeee")
def test_top():
    assert top({"yes": 2, "no": 1}) == "yes"


@pytest.mark.id("tst_ffffff")
def test_shares():
    assert shares({"yes": 1, "no": 1}) == {"yes": 0.5, "no": 0.5}
"""

SHIP_TEST = '''import pytest
from ship import winner


@pytest.mark.id("tst_gggggg")
def test_winner():
    """Names a choice"""
    assert winner(["yes"]) in {"yes"}
'''

SHIP_CHECKS = """import pytest
from ship import winner


@pytest.mark.id("tst_hhhhhh")
def test_majority(record_property):
    found = winner(["no", "yes", "yes"])
    record_property("note", f"named {found}")
    assert found == "yes"
"""


def stage(**fields: Any) -> dict[str, Any]:
    tests = {
        name: base64.b64encode(text.encode()).decode() for name, text in fields["tests"].items()
    }
    fixed = fields.get("fixed")
    return {
        "id": fields["id"],
        "version": f"v-{fields['id']}",
        "slug": fields["slug"],
        "title": fields["title"],
        "kind": fields.get("kind", "build"),
        "file": fields["file"],
        "starter": fields["starter"],
        "tests": tests,
        "checks": fields.get("checks", []),
        "fixed": None if fixed is None else base64.b64encode(fixed.encode()).decode(),
    }


STAGES = [
    stage(
        id="stg_count1",
        slug="count",
        title="Count",
        file="tally.py",
        starter="def count(votes, choice):\n    return 0\n",
        tests={"tests/test_count.py": COUNT_TEST},
    ),
    stage(
        id="stg_share1",
        slug="share",
        title="Share",
        file="tally.py",
        starter="def share(votes, choice):\n    return 0.0\n",
        tests={"tests/test_share.py": SHARE_TEST},
    ),
    stage(
        id="stg_review",
        slug="review",
        title="The assistant's report",
        kind="catch",
        file="report.py",
        starter=REPORT,
        tests={
            "tests/test_report.py": ASSISTANT_TEST,
            "tests/checks/test_report.py": REPORT_CHECKS,
        },
        checks=[
            {"id": "tst_eeeeee", "title": "Its top was the least", "requires": "", "failure": ""},
            {"id": "tst_ffffff", "title": "Its shares were of 10", "requires": "", "failure": ""},
        ],
        fixed=FIXED,
    ),
    stage(
        id="stg_ship01",
        slug="ship",
        title="Ship",
        kind="ship",
        file="ship.py",
        starter="def winner(votes):\n    return votes[0]\n",
        tests={"tests/test_ship.py": SHIP_TEST, "tests/checks/test_ship.py": SHIP_CHECKS},
        checks=[
            {
                "id": "tst_hhhhhh",
                "title": "The majority wins",
                "requires": "The choice with the most votes must win.",
                "failure": "Another choice won.",
            }
        ],
    ),
]

SOLUTIONS = {
    "stg_count1": "def count(votes, choice):\n    return votes.count(choice)\n",
    "stg_share1": (
        "def count(votes, choice):\n    return votes.count(choice)\n\n\n"
        "def share(votes, choice):\n    return count(votes, choice) / len(votes)\n"
    ),
    "stg_ship01": "def winner(votes):\n    return max(set(votes), key=votes.count)\n",
}


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    """A lab's download, as the lab's page makes it, starting at its first stage."""
    runner = tmp_path / ".sulba"
    (runner / "references").mkdir(parents=True)
    shutil.copy(PYTHON / "sulba.py", tmp_path / "sulba.py")
    for name in ["sulba_runner.py", "sulba_fixtures.py"]:
        shutil.copy(PYTHON / name, runner / name)
    lab = {
        "format": 1,
        "id": "lab_tally1",
        "title": "Tallies",
        "page": "https://sulba.dev/demo/counting/tallies/",
        "start": 0,
        "stages": STAGES,
    }
    (runner / "lab.json").write_text(json.dumps(lab), encoding="utf-8")
    (runner / "references" / "counts.json").write_text('{"no": 1}', encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "votes.csv").write_text("yes\nno\nyes\n", encoding="utf-8")
    (tmp_path / "tally.py").write_text(STAGES[0]["starter"], encoding="utf-8")
    return tmp_path


def command(folder: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(folder / "sulba.py"), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def progress(folder: Path) -> dict[str, Any]:
    return json.loads((folder / ".sulba" / "progress.json").read_text(encoding="utf-8"))


def carried(address: str) -> dict[str, Any]:
    """What a link carries."""
    code = address.split("#run=")[1]
    packed = base64.urlsafe_b64decode(code + "=" * (-len(code) % 4))
    return json.loads(zlib.decompress(packed, wbits=-15))


def payload(output: str) -> dict[str, Any]:
    """What the link a run printed carries."""
    return carried(next(line for line in output.splitlines() if "#run=" in line))


def solve(folder: Path, stage_id: str) -> None:
    file = next(each["file"] for each in STAGES if each["id"] == stage_id)
    (folder / file).write_text(SOLUTIONS[stage_id], encoding="utf-8")


def test_a_starter_fails_its_tests(folder: Path) -> None:
    ran = command(folder)
    assert ran.returncode == 1
    assert "Stage 1 of 4: Count" in ran.stdout
    assert "0 of 2 tests passed." in ran.stdout
    assert "✗ Counts the votes for each choice" in ran.stdout
    assert "Expected: 2" in ran.stdout
    assert "#run=" not in ran.stdout
    assert [attempt[3] for attempt in progress(folder)["attempts"]] == ["run"]


def test_a_stage_done_prints_a_link_with_its_attempts(folder: Path) -> None:
    command(folder)
    solve(folder, "stg_count1")
    ran = command(folder)
    assert ran.returncode == 0
    assert "Both tests passed." in ran.stdout
    assert "Stage 1 done." in ran.stdout
    assert "uv run sulba.py next" in ran.stdout
    sent = payload(ran.stdout)
    assert sent["format"] == 1
    assert sent["lab"] == "lab_tally1"
    assert sent["passed"] == {"stg_count1": None}
    kinds = [(attempt[1], attempt[2], attempt[3]) for attempt in sent["attempts"]]
    assert kinds == [
        ("stg_count1", "v-stg_count1", "run"),
        ("stg_count1", "v-stg_count1", "run"),
        ("stg_count1", "v-stg_count1", "pass"),
    ]
    assert [attempt[4] for attempt in sent["attempts"]] == [[0, 2], [2, 2], None]
    assert all(0 <= attempt[7] <= 3600 for attempt in sent["attempts"])
    # The link carries each attempt once: the next link starts after it.
    assert progress(folder)["attempts"] == []


def test_the_next_stage_goes_below_the_learners_code(folder: Path) -> None:
    assert command(folder, "next").returncode == 1
    solve(folder, "stg_count1")
    command(folder)
    ran = command(folder, "next")
    assert ran.returncode == 0
    assert "Stage 2 of 4: Share" in ran.stdout
    assert "https://sulba.dev/demo/counting/tallies/?stage=share" in ran.stdout
    expected = SOLUTIONS["stg_count1"].rstrip() + "\n\n\n" + STAGES[1]["starter"]
    assert (folder / "tally.py").read_text(encoding="utf-8") == expected
    assert progress(folder)["stage"] == 1


def test_a_catch_review_finishes_with_the_problems_caught(folder: Path) -> None:
    for each in ["stg_count1", "stg_share1"]:
        solve(folder, each)
        command(folder)
        command(folder, "next")
    ran = command(folder)
    assert ran.returncode == 1
    assert "0 of 2 production checks passed. The assistant's test passed." in ran.stdout
    assert "Its top was the least" not in ran.stdout
    fixed = (folder / "report.py").read_text(encoding="utf-8").replace("min(counts", "max(counts")
    (folder / "report.py").write_text(fixed, encoding="utf-8")
    ran = command(folder, "finish")
    assert ran.returncode == 0
    assert "Review finished. You caught 1 of 2 problems." in ran.stdout
    review = {"caught": ["tst_eeeeee"], "problems": 2}
    assert payload(ran.stdout)["passed"]["stg_review"] == review
    assert payload(ran.stdout)["attempts"][-1][6] == review
    # The review missed a problem, so the lab goes on from the fixed code.
    ran = command(folder, "next")
    assert "Yours is in report.yours.py." in ran.stdout
    assert (folder / "report.py").read_text(encoding="utf-8") == FIXED
    assert (folder / "report.yours.py").read_text(encoding="utf-8") == fixed
    assert (folder / "ship.py").read_text(encoding="utf-8") == STAGES[3]["starter"]


def test_a_ship_stage_shows_its_checks_before_it_ships(folder: Path) -> None:
    progress_file = folder / ".sulba" / "progress.json"
    passed = {"stg_count1": None, "stg_share1": None, "stg_review": None}
    state = {"stage": 3, "passed": passed, "attempts": [], "last": None}
    progress_file.write_text(json.dumps(state), encoding="utf-8")
    (folder / "ship.py").write_text(STAGES[3]["starter"], encoding="utf-8")
    ran = command(folder)
    assert ran.returncode == 1
    assert "The test passed. The check failed." in ran.stdout
    assert "Before it ships" in ran.stdout
    assert "✗ The majority wins" in ran.stdout
    assert "The choice with the most votes must win." in ran.stdout
    assert "Another choice won." in ran.stdout
    solve(folder, "stg_ship01")
    ran = command(folder)
    assert ran.returncode == 0
    assert "✓ The majority wins" in ran.stdout
    assert "named yes" in ran.stdout
    assert "That was the lab's last stage." in ran.stdout


def test_an_error_in_the_code_shows_where_it_is(folder: Path) -> None:
    (folder / "tally.py").write_text("def count(votes, choice)\n    return 0\n", encoding="utf-8")
    ran = command(folder)
    assert ran.returncode == 1
    assert "SyntaxError" in ran.stdout
    assert "tally.py, line 1" in ran.stdout
    assert "Your code has an error." in ran.stdout


def test_only_a_catch_stage_has_a_review_to_finish(folder: Path) -> None:
    ran = command(folder, "finish")
    assert ran.returncode == 1
    assert "Only a Catch stage has a review to finish." in ran.stdout


def test_a_folder_without_a_lab_says_so(tmp_path: Path) -> None:
    shutil.copy(PYTHON / "sulba.py", tmp_path / "sulba.py")
    ran = command(tmp_path)
    assert ran.returncode == 1
    assert "it has no .sulba/lab.json" in ran.stdout


# A link from the runner, which the lab's page reads in its own tests
# (apps/web/src/workspace/link.test.ts).
LINK = (
    "https://sulba.dev/demo/counting/tallies/"
    "#run=jZDPasMwDMbfRWd7WK7zz8-x00IIsmN3AycpidNRSt69dnbpIYcJ8YEk0PeTnuDnZaQIGhkEMqCz9pFCeCAwuNG6ugH0E9Z47e28TRFBT1sI7Ogs7v7jfvPc0nb9TntaiGvs3RHQpQ3LbIIbV9By3xlQjG68xVS2LQhTeemV48VwsVw5JN5QIXllSy-cHGqDGeLNiME9d5ZtAtYiwy6r7NhBpCQDKWTJUXCsP7HUQqT8EEJ8wfsocbVQkLDVIA1vnEKufEm8tpeBS4NO-IYShDo1zz-BP8dD_nc7q8_g6jO4bn8B"
)


def test_a_link_holds_what_the_page_reads() -> None:
    lab = {"id": "lab_tally1", "page": "https://sulba.dev/demo/counting/tallies/"}
    attempts = [
        [
            "0b7f2f4e-5d3c-4e1a-9a52-7c6f0e2d8b11",
            "stg_review",
            "v1",
            "run",
            [1, 1],
            [1, 2],
            None,
            42,
            "2026-10-18T16:00:00.000Z",
            "2026-10-18",
        ],
        [
            "5a0c7d2b-9e41-4f6a-8c3d-2b1e0f9a7c64",
            "stg_review",
            "v1",
            "pass",
            None,
            None,
            {"caught": ["tst_eeeeee"], "problems": 2},
            8,
            "2026-10-18T16:00:08.000Z",
            "2026-10-18",
        ],
    ]
    state = {
        "passed": {"stg_count1": None, "stg_review": {"caught": ["tst_eeeeee"], "problems": 2}},
        "attempts": attempts,
    }
    # DEFLATE's bytes can differ from one build of zlib to another, so the links match in what they
    # carry.
    address = sulba.link(lab, state)
    assert address.startswith("https://sulba.dev/demo/counting/tallies/#run=")
    assert carried(address) == carried(LINK)
    assert carried(LINK) == {"format": 1, "lab": "lab_tally1", **state}


def test_a_link_holds_the_newest_attempts_that_fit() -> None:
    lab = {"id": "lab_tally1", "page": "https://sulba.dev/demo/counting/tallies/"}
    ids = random.Random(0)
    runs = [
        [
            str(uuid.UUID(int=ids.getrandbits(128), version=4)),
            "stg_count1",
            "v1",
            "run",
            [0, 2],
            None,
            None,
            30,
            f"2026-10-18T16:{index // 60:02d}:{index % 60:02d}.000Z",
            "2026-10-18",
        ]
        for index in range(150)
    ]
    state = {"passed": {"stg_count1": None}, "attempts": runs}
    address = sulba.link(lab, state)
    assert len(address) <= sulba.MAX_LINK
    sent = carried(address)["attempts"]
    assert 1 < len(sent) < len(runs)
    assert sent == runs[-len(sent) :]
