import base64
import hashlib
import http.client
import http.server
import json
import random
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import threading
import uuid
import zipfile
import zlib
from collections.abc import Iterator
from dataclasses import dataclass, field
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
    for name in ["sulba_runner.py", "sulba_fixtures.py", "sulba_reporter.mjs"]:
        shutil.copy(PYTHON / name, runner / name)
    lab = {
        "format": 1,
        "id": "lab_tally1",
        "title": "Tallies",
        "page": "https://sulba.dev/demo/counting/tallies/",
        "start": 0,
        "data": ["data/votes.csv"],
        "given": [],
        "fetch": [],
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


def test_a_run_reads_only_the_labs_own_datasets_in_data(folder: Path) -> None:
    (folder / "data" / "tile.jpg").write_bytes(b"\xff\xd8\xff\xe0")
    ran = command(folder)
    assert ran.returncode == 1
    assert "0 of 2 tests passed." in ran.stdout


GIVEN_TEST = '''from pathlib import Path

import pytest
from ballots import ballots
from tally import count


@pytest.mark.id("tst_gggggg")
def test_given():
    """Counts the ballots the lab gives, which sit beside the learner's files"""
    assert Path("ballots.py").is_file()
    assert count(ballots(), "yes") == 2
'''


def test_a_run_has_the_files_the_lab_gives(folder: Path) -> None:
    path = folder / ".sulba" / "lab.json"
    lab = json.loads(path.read_text(encoding="utf-8"))
    lab["given"] = ["ballots.py"]
    lab["stages"][0]["tests"] = {
        "tests/test_given.py": base64.b64encode(GIVEN_TEST.encode()).decode()
    }
    path.write_text(json.dumps(lab), encoding="utf-8")
    (folder / "ballots.py").write_text(
        'def ballots():\n    return ["yes", "no", "yes"]\n', encoding="utf-8"
    )
    solve(folder, "stg_count1")
    ran = command(folder)
    assert ran.returncode == 0, ran.stdout
    assert "Stage 1 done." in ran.stdout


TOTALS_TEST = """import assert from 'node:assert/strict';
import { test } from 'node:test';
import { total } from '#totals.ts';

test('tst_jjjjjj Adds the amounts', () => {
  assert.equal(total([1250, 300]), 1550);
});
"""


def test_a_typescript_stage_runs_with_the_projects_packages(folder: Path) -> None:
    path = folder / ".sulba" / "lab.json"
    lab = json.loads(path.read_text(encoding="utf-8"))
    lab["stages"][0]["file"] = "totals.ts"
    lab["stages"][0]["tests"] = {
        "tests/totals.test.ts": base64.b64encode(TOTALS_TEST.encode()).decode()
    }
    path.write_text(json.dumps(lab), encoding="utf-8")
    session = Path(__file__).with_name("typescript")
    for name in ["package.json", "package-lock.json", "tsconfig.json", "totals.ts"]:
        shutil.copy(session / name, folder / name)
    ran = command(folder)
    assert ran.returncode == 0, ran.stdout
    assert "✓ Adds the amounts" in ran.stdout
    assert "Stage 1 done." in ran.stdout


BUILD = """{
  "compilerOptions": {
    "target": "es2022",
    "module": "esnext",
    "moduleResolution": "bundler",
    "strict": true,
    "lib": ["es2022", "dom"],
    "types": [],
    "rootDir": ".",
    "outDir": "static"
  },
  "files": ["totals.ts"]
}
"""


def test_a_build_compiles_the_labs_typescript_for_the_browser(folder: Path) -> None:
    session = Path(__file__).with_name("typescript")
    for name in ["package.json", "package-lock.json", "tsconfig.json", "totals.ts"]:
        shutil.copy(session / name, folder / name)
    (folder / "tsconfig.build.json").write_text(BUILD, encoding="utf-8")
    built = command(folder, "build")
    assert built.returncode == 0, built.stdout
    assert "Built the lab's TypeScript for the browser." in built.stdout
    script = (folder / "static" / "totals.js").read_text(encoding="utf-8")
    assert "export function total(amounts) {" in script
    (folder / "totals.ts").write_text("export const total: number = 'none';\n", encoding="utf-8")
    broken = command(folder, "build")
    assert broken.returncode == 1
    assert "TS2322" in broken.stdout


def test_a_lab_without_typescript_for_the_browser_has_nothing_to_build(folder: Path) -> None:
    built = command(folder, "build")
    assert built.returncode == 1
    assert "This lab has no TypeScript to build for the browser." in built.stdout


# A file a lab fetches from its publisher (decision record 29): bytes, not text.
BALLOTS = bytes(range(256)) * 64

BALLOTS_TEST = '''import pytest


@pytest.mark.id("tst_iiiiii")
def test_ballots():
    """Reads the fetched ballots"""
    with open("data/ballots.bin", "rb") as file:
        assert len(file.read()) == 16384
'''


@dataclass
class Publisher:
    """A publisher's server: the files it sends, by path, whether it sends part of one when asked
    to, how many bytes it sends before it stops early, and each request's path and Range."""

    address: str = ""
    files: dict[str, bytes] = field(default_factory=dict)
    ranges: bool = True
    stops: int | None = None
    requests: list[tuple[str, str | None]] = field(default_factory=list)


@pytest.fixture
def publisher() -> Iterator[Publisher]:
    served = Publisher(files={"/ballots.bin": BALLOTS})

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            asked = self.headers.get("Range")
            served.requests.append((self.path, asked))
            body = served.files.get(self.path)
            if body is None:
                self.send_error(404)
                return
            part = bool(asked) and served.ranges
            start = int(asked.removeprefix("bytes=").removesuffix("-")) if asked and part else 0
            self.send_response(206 if part else 200)
            if part:
                self.send_header("Content-Range", f"bytes {start}-{len(body) - 1}/{len(body)}")
            self.send_header("Content-Length", str(len(body) - start))
            self.end_headers()
            end = len(body) if served.stops is None else start + served.stops
            self.wfile.write(body[start:end])

        def log_message(self, *args: Any) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    served.address = f"http://127.0.0.1:{server.server_port}"
    yield served
    server.shutdown()
    server.server_close()


def fetching(folder: Path, url: str) -> None:
    """The lab in folder fetches ballots.bin from url, and its first stage's tests read it."""
    path = folder / ".sulba" / "lab.json"
    lab = json.loads(path.read_text(encoding="utf-8"))
    sha256 = hashlib.sha256(BALLOTS).hexdigest()
    lab["fetch"] = [{"file": "ballots.bin", "url": url, "bytes": len(BALLOTS), "sha256": sha256}]
    test = base64.b64encode(BALLOTS_TEST.encode()).decode()
    lab["stages"][0]["tests"]["tests/test_ballots.py"] = test
    path.write_text(json.dumps(lab), encoding="utf-8")


def test_a_labs_files_are_fetched_before_its_first_run(folder: Path, publisher: Publisher) -> None:
    fetching(folder, f"{publisher.address}/ballots.bin")
    ran = command(folder)
    assert ran.returncode == 1
    assert "Fetching the lab's files into data:" in ran.stdout
    assert "ballots.bin, 16.4 kB, from 127.0.0.1" in ran.stdout
    assert "✓ Reads the fetched ballots" in ran.stdout
    assert "1 of 3 tests passed." in ran.stdout
    assert (folder / "data" / "ballots.bin").read_bytes() == BALLOTS
    assert not (folder / "data" / "ballots.bin.partial").exists()
    assert publisher.requests == [("/ballots.bin", None)]


def test_a_file_already_fetched_is_not_fetched_again(folder: Path, publisher: Publisher) -> None:
    fetching(folder, f"{publisher.address}/ballots.bin")
    command(folder)
    ran = command(folder)
    assert "Fetching" not in ran.stdout
    assert "✓ Reads the fetched ballots" in ran.stdout
    assert len(publisher.requests) == 1


def test_a_fetch_cut_short_goes_on_from_where_it_stopped(
    folder: Path, publisher: Publisher
) -> None:
    fetching(folder, f"{publisher.address}/ballots.bin")
    (folder / "data" / "ballots.bin.partial").write_bytes(BALLOTS[:1000])
    command(folder)
    assert publisher.requests == [("/ballots.bin", "bytes=1000-")]
    assert (folder / "data" / "ballots.bin").read_bytes() == BALLOTS


def test_a_fetch_the_publisher_stops_early_keeps_what_came(
    folder: Path, publisher: Publisher
) -> None:
    fetching(folder, f"{publisher.address}/ballots.bin")
    publisher.stops = 8000
    ran = command(folder)
    assert ran.returncode == 1
    assert "The fetch stopped: 127.0.0.1 stopped after 8.0 kB of 16.4 kB" in ran.stdout
    assert "Run uv run sulba.py again to go on from where it stopped." in ran.stdout
    assert (folder / "data" / "ballots.bin.partial").read_bytes() == BALLOTS[:8000]
    publisher.stops = None
    command(folder)
    assert publisher.requests == [("/ballots.bin", None), ("/ballots.bin", "bytes=8000-")]
    assert (folder / "data" / "ballots.bin").read_bytes() == BALLOTS


def test_a_publisher_that_sends_all_of_a_file_asked_for_in_part_is_heard(
    folder: Path, publisher: Publisher
) -> None:
    fetching(folder, f"{publisher.address}/ballots.bin")
    publisher.ranges = False
    (folder / "data" / "ballots.bin.partial").write_bytes(BALLOTS[:1000])
    command(folder)
    assert publisher.requests == [("/ballots.bin", "bytes=1000-")]
    assert (folder / "data" / "ballots.bin").read_bytes() == BALLOTS


def test_a_fetch_stopped_once_all_of_its_file_had_come_only_moves_it(
    folder: Path, publisher: Publisher
) -> None:
    fetching(folder, f"{publisher.address}/ballots.bin")
    (folder / "data" / "ballots.bin.partial").write_bytes(BALLOTS)
    command(folder)
    assert publisher.requests == []
    assert (folder / "data" / "ballots.bin").read_bytes() == BALLOTS
    assert not (folder / "data" / "ballots.bin.partial").exists()


def test_a_file_cut_short_that_does_not_go_on_is_fetched_again(
    folder: Path, publisher: Publisher
) -> None:
    fetching(folder, f"{publisher.address}/ballots.bin")
    (folder / "data" / "ballots.bin.partial").write_bytes(bytes(1000))
    command(folder)
    assert publisher.requests == [("/ballots.bin", "bytes=1000-"), ("/ballots.bin", None)]
    assert (folder / "data" / "ballots.bin").read_bytes() == BALLOTS


def test_a_file_changed_since_it_was_fetched_is_fetched_again(
    folder: Path, publisher: Publisher
) -> None:
    fetching(folder, f"{publisher.address}/ballots.bin")
    command(folder)
    (folder / "data" / "ballots.bin").write_bytes(bytes(len(BALLOTS)))
    ran = command(folder)
    assert "Fetching the lab's files into data:" in ran.stdout
    assert (folder / "data" / "ballots.bin").read_bytes() == BALLOTS


def test_a_file_other_than_the_labs_is_refused(folder: Path, publisher: Publisher) -> None:
    publisher.files["/ballots.bin"] = bytes(len(BALLOTS))
    fetching(folder, f"{publisher.address}/ballots.bin")
    ran = command(folder)
    assert ran.returncode == 1
    assert "127.0.0.1 sent a different file from the one the lab was made with." in ran.stdout
    assert "tests passed" not in ran.stdout
    assert list((folder / "data").iterdir()) == [folder / "data" / "votes.csv"]
    assert progress(folder)["attempts"] == []


def test_a_file_of_another_size_is_refused_before_it_comes(
    folder: Path, publisher: Publisher
) -> None:
    publisher.files["/ballots.bin"] = BALLOTS[:100]
    fetching(folder, f"{publisher.address}/ballots.bin")
    ran = command(folder)
    assert ran.returncode == 1
    assert "127.0.0.1 sent a different file from the one the lab was made with." in ran.stdout
    assert len(publisher.requests) == 1
    assert list((folder / "data").iterdir()) == [folder / "data" / "votes.csv"]


def test_a_file_the_publisher_does_not_have_is_said(folder: Path, publisher: Publisher) -> None:
    fetching(folder, f"{publisher.address}/gone.bin")
    ran = command(folder)
    assert ran.returncode == 1
    assert "127.0.0.1 answered 404 Not Found. Try again later." in ran.stdout


def test_a_publisher_out_of_reach_stops_the_run(folder: Path) -> None:
    with socket.socket() as unused:
        unused.bind(("127.0.0.1", 0))
        port = unused.getsockname()[1]
    fetching(folder, f"http://127.0.0.1:{port}/ballots.bin")
    ran = command(folder)
    assert ran.returncode == 1
    assert "The fetch stopped:" in ran.stdout
    assert "Run uv run sulba.py again to go on from where it stopped." in ran.stdout


def test_a_size_is_shown_in_decimal_units() -> None:
    assert [sulba.size(count) for count in [512, 5148, 26_421_880, 1_500_000_000]] == [
        "512 bytes",
        "5.1 kB",
        "26.4 MB",
        "1.5 GB",
    ]


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


# A stand-in for llama.cpp's server in router mode, at the port it's given: it reads the models in
# its preset file, lists them as loading at first, then as loaded, or as failed when their weights
# aren't where the preset says from the folder it runs in, and answers each request for a model by
# its name, as the model's kind allows. Told to stop at once, it says why.
FAKE_SERVER = """import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

if "--stop" in sys.argv:
    print(sys.argv[sys.argv.index("--stop") + 1])
    sys.exit(1)
port = int(sys.argv[sys.argv.index("--port") + 1])
models = {}
for line in Path(sys.argv[sys.argv.index("--models-preset") + 1]).read_text().splitlines():
    if line.startswith("["):
        options = models[line[1:-1]] = {}
    elif " = " in line and models:
        key, value = line.split(" = ")
        options[key] = value
for name, options in models.items():
    if not Path(options["model"]).is_file():
        print(f"[{name}] failed to load model {options['model']}", flush=True)
polls = []


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        polls.append(self.path)
        listed = []
        for name, options in models.items():
            if len(polls) == 1:
                status = {"value": "loading"}
            elif Path(options["model"]).is_file():
                status = {"value": "loaded"}
            else:
                status = {"value": "unloaded", "failed": True, "exit_code": 1}
            listed.append({"id": name, "status": status})
        self.answer(200, {"data": listed})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        options = models.get(body.get("model"))
        if options is None:
            self.answer(400, {"error": {"message": "model not found"}})
        elif options.get("embeddings"):
            self.served("/v1/embeddings", {"data": [{"index": 0, "embedding": [0.5] * 4}]})
        elif options.get("reranking"):
            scores = [(1, 0.0123), (0, 0.9876)]
            results = [{"index": index, "relevance_score": score} for index, score in scores]
            self.served("/v1/rerank", {"results": results})
        else:
            reply = {"content": f"Hello from {body['model']}."}
            usage = {"prompt_tokens": 9, "completion_tokens": 3}
            self.served("/v1/chat/completions", {"choices": [{"message": reply}], "usage": usage})

    def served(self, path, body):
        if self.path == path:
            self.answer(200, body)
        else:
            self.answer(501, {"error": {"message": "This model doesn't serve " + self.path}})

    def answer(self, status, body):
        self.send_response(status)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", port), Handler).serve_forever()
"""

# A chat model, an embedding model and a reranker, by title and kind.
KINDS = [("Tiny", "chat"), ("Tiny-Embed", "embedding"), ("Tiny-Rerank", "reranking")]


def model_lab(folder: Path, models: list[tuple[str, str, str, bytes]]) -> dict[str, Any]:
    """The lab in folder serving models, each a title, a kind, an address and the file there."""
    path = folder / ".sulba" / "lab.json"
    lab = json.loads(path.read_text(encoding="utf-8"))
    lab["models"] = [
        {
            "title": title,
            "kind": kind,
            "url": url,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
        for title, kind, url, body in models
    ]
    path.write_text(json.dumps(lab), encoding="utf-8")
    return lab


def build_archive(tmp_path: Path) -> bytes:
    """A build of the server as llama.cpp packs one for Linux and macOS: the stand-in, runnable, in
    a folder named for its release."""
    server = tmp_path / "llama-b0" / "llama-server"
    server.parent.mkdir()
    server.write_text(f"#!{sys.executable}\n{FAKE_SERVER}", encoding="utf-8")
    server.chmod(0o755)
    archive = tmp_path / "build.tar.gz"
    with tarfile.open(archive, "w:gz") as packed:
        packed.add(server.parent, arcname="llama-b0")
    return archive.read_bytes()


def fake_server(folder: Path, port: int, kinds: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """The models of these kinds in folder, with their weights and a preset there, and the stand-in
    beside them, to run at the port in folder."""
    models = [{"title": title, "kind": kind} for title, kind in kinds]
    weights = [Path("models", f"{title}.gguf") for title, _ in kinds]
    (folder / "models").mkdir()
    for path in weights:
        (folder / path).write_bytes(b"GGUF")
    preset = sulba.preset_of(models, weights, "Linux")
    (folder / f"models-{port}.ini").write_text(preset, encoding="utf-8")
    (folder / "server.py").write_text(FAKE_SERVER, encoding="utf-8")
    return models


def fake_command(folder: Path, port: int) -> list[str]:
    """The stand-in's command, with the preset fake_server wrote for the port."""
    return [sys.executable, str(folder / "server.py"), "--models-preset", f"models-{port}.ini"]


def test_a_lab_without_a_model_says_so(folder: Path) -> None:
    ran = command(folder, "model")
    assert ran.returncode == 1
    assert ran.stdout == "This lab has no model to run.\n"


def test_a_system_without_a_build_says_so(
    folder: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    lab = model_lab(folder, [("Tiny", "chat", "https://example.com/tiny.gguf", b"GGUF")])
    monkeypatch.setattr(sulba.platform, "system", lambda: "Plan9")
    monkeypatch.setattr(sulba.platform, "machine", lambda: "mips")
    assert sulba.serve_model(lab, sulba.free_port(), check=True) == 1
    assert capsys.readouterr().out == "llama.cpp has no build of its server for Plan9 on mips.\n"


def test_windows_without_the_runtime_is_told_where_to_get_it_before_any_fetch(
    folder: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    lab = model_lab(folder, [("Tiny", "chat", "https://example.com/tiny.gguf", b"GGUF")])
    monkeypatch.setattr(sulba.platform, "system", lambda: "Windows")
    monkeypatch.setattr(sulba.platform, "machine", lambda: "ARM64")
    (tmp_path / "windows" / "System32").mkdir(parents=True)
    (tmp_path / "windows" / "System32" / "vcruntime140.dll").touch()
    monkeypatch.setenv("SYSTEMROOT", str(tmp_path / "windows"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert sulba.serve_model(lab, sulba.free_port(), check=True) == 1
    said = capsys.readouterr().out
    assert "llama.cpp's server needs Microsoft's Visual C++ runtime" in said
    assert "Install it from https://aka.ms/vc14/vc_redist.arm64.exe, then run this again." in said
    assert not (tmp_path / "cache").exists()


def test_a_model_and_its_server_are_fetched_once_for_every_lab(
    folder: Path,
    tmp_path: Path,
    publisher: Publisher,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    build = build_archive(tmp_path)
    publisher.files["/b0/llama-b0-bin-test.tar.gz"] = build
    publisher.files["/tiny.gguf"] = b"GGUF" * 100
    lab = model_lab(folder, [("Tiny", "chat", f"{publisher.address}/tiny.gguf", b"GGUF" * 100)])
    system = (sulba.platform.system(), sulba.platform.machine())
    pinned = ("bin-test.tar.gz", len(build), hashlib.sha256(build).hexdigest())
    monkeypatch.setattr(sulba, "LLAMA", "b0")
    monkeypatch.setattr(sulba, "LLAMA_RELEASES", publisher.address)
    monkeypatch.setattr(sulba, "LLAMA_BUILDS", {system: pinned})
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    assert sulba.serve_model(lab, sulba.free_port(), check=True) == 0
    said = capsys.readouterr().out
    cache = tmp_path / "cache" / "sulba"
    assert f"Fetching the model and its server into {cache}:" in said
    assert "llama.cpp's server b0, " in said
    assert "Tiny, 400 bytes, from 127.0.0.1" in said
    assert said.endswith(
        "Loading Tiny...\nTiny said: 'Hello from Tiny.'\nIt read 9 tokens and wrote 3.\n"
    )
    assert (cache / "llama.cpp" / "b0" / "server" / "llama-b0" / "llama-server").is_file()
    assert sulba.serve_model(lab, sulba.free_port(), check=True) == 0
    assert "Fetching" not in capsys.readouterr().out
    assert len(publisher.requests) == 2


def test_a_labs_models_answer_each_by_its_name_and_kind(
    folder: Path,
    tmp_path: Path,
    publisher: Publisher,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    build = build_archive(tmp_path)
    publisher.files["/b0/llama-b0-bin-test.tar.gz"] = build
    models = []
    for title, kind in KINDS:
        body = title.encode() * 10
        publisher.files[f"/{title}.gguf"] = body
        models.append((title, kind, f"{publisher.address}/{title}.gguf", body))
    lab = model_lab(folder, models)
    system = (sulba.platform.system(), sulba.platform.machine())
    pinned = ("bin-test.tar.gz", len(build), hashlib.sha256(build).hexdigest())
    monkeypatch.setattr(sulba, "LLAMA", "b0")
    monkeypatch.setattr(sulba, "LLAMA_RELEASES", publisher.address)
    monkeypatch.setattr(sulba, "LLAMA_BUILDS", {system: pinned})
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    port = sulba.free_port()
    assert sulba.serve_model(lab, port, check=True) == 0
    said = capsys.readouterr().out
    cache = tmp_path / "cache" / "sulba"
    assert f"Fetching the models and their server into {cache}:" in said
    assert said.endswith(
        "Loading Tiny, Tiny-Embed and Tiny-Rerank...\n"
        "Tiny said: 'Hello from Tiny.'\n"
        "It read 9 tokens and wrote 3.\n"
        "Tiny-Embed embedded 'The brakes stop the wheels.' as 4 numbers.\n"
        "Tiny-Rerank scored two passages for 'Which part of a bicycle stops it?':\n"
        "  0.9876  The brakes stop the wheels.\n"
        "  0.0123  The saddle is where the rider sits.\n"
    )
    # The preset names each model's weights from the cache folder, where the server runs.
    preset = (cache / f"models-{port}.ini").read_text(encoding="utf-8")
    for title, _, _, body in models:
        sha256 = hashlib.sha256(body).hexdigest()
        assert f"[{title}]\nmodel = models/{sha256}/{title}.gguf\n" in preset


def test_each_kind_of_model_runs_with_its_options() -> None:
    models = [{"title": title, "kind": kind} for title, kind in KINDS]
    weights = [
        Path("models", "a", "chat.gguf"),
        Path("models", "b", "e.gguf"),
        Path("models", "c", "r.gguf"),
    ]
    linux = sulba.preset_of(models, weights, "Linux")
    assert linux == (
        "version = 1\n"
        "\n"
        "[Tiny]\n"
        "model = models/a/chat.gguf\n"
        "load-on-startup = true\n"
        "ctx-size = 4096\n"
        "reasoning = off\n"
        "\n"
        "[Tiny-Embed]\n"
        "model = models/b/e.gguf\n"
        "load-on-startup = true\n"
        "embeddings = true\n"
        "ctx-size = 2048\n"
        "batch-size = 2048\n"
        "ubatch-size = 2048\n"
        "\n"
        "[Tiny-Rerank]\n"
        "model = models/c/r.gguf\n"
        "load-on-startup = true\n"
        "reranking = true\n"
        "ctx-size = 4096\n"
        "batch-size = 2048\n"
        "ubatch-size = 2048\n"
    )
    # On macOS, only the chat model runs on the GPU.
    macos = sulba.preset_of(models, weights, "Darwin")
    assert macos == linux.replace("ubatch-size = 2048\n", "ubatch-size = 2048\ndevice = none\n")


def test_a_chat_model_reads_the_context_its_lab_gives() -> None:
    models = [{"title": "Tiny", "kind": "chat", "context": 16384}]
    preset = sulba.preset_of(models, [Path("models", "a", "chat.gguf")], "Linux")
    chat = "[Tiny]\nmodel = models/a/chat.gguf\nload-on-startup = true\nctx-size = 16384\n"
    assert chat in preset
    assert "ctx-size = 4096" not in preset


def test_a_build_is_unpacked_once_beside_its_archive(tmp_path: Path) -> None:
    archive = tmp_path / "bin-win-cpu-x64.zip"
    with zipfile.ZipFile(archive, "w") as packed:
        packed.writestr("llama-server.exe", "MZ")
        packed.writestr("ggml.dll", "MZ")
    server = sulba.unpacked(archive)
    assert server == tmp_path / "server" / "llama-server.exe"
    archive.unlink()
    assert sulba.unpacked(archive) == server


@pytest.mark.skipif(sys.platform == "win32", reason="Ctrl+C reaches a program as a POSIX signal")
def test_the_models_answer_once_loaded_until_ctrl_c(tmp_path: Path) -> None:
    port = sulba.free_port()
    models = fake_server(tmp_path, port, KINDS)
    serve = (
        "import json, sys, sulba; from pathlib import Path; "
        "sys.exit(sulba.serve(json.loads(sys.argv[1]), Path(sys.argv[2]), "
        "json.loads(sys.argv[3]), int(sys.argv[4]), check=False))"
    )
    arguments = [json.dumps(fake_command(tmp_path, port)), str(tmp_path), json.dumps(models)]
    running = subprocess.Popen(
        [sys.executable, "-c", serve, *arguments, str(port)],
        cwd=PYTHON,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    assert running.stdout is not None
    assert running.stdout.readline() == "Loading Tiny, Tiny-Embed and Tiny-Rerank...\n"
    assert running.stdout.readline() == (
        f"Tiny, Tiny-Embed and Tiny-Rerank answer at http://127.0.0.1:{port}/v1, each by its name. "
        "Press Ctrl+C to stop them.\n"
    )
    asked = sulba.posted(f"http://127.0.0.1:{port}", "embeddings", "Tiny-Embed", input="Hello.")
    assert len(asked["data"][0]["embedding"]) == 4
    running.send_signal(signal.SIGINT)
    assert running.communicate(timeout=60)[0] == "Stopped Tiny, Tiny-Embed and Tiny-Rerank.\n"
    assert running.returncode == 0
    assert not sulba.in_use(port)


def test_a_model_that_doesnt_load_is_named_with_why(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    port = sulba.free_port()
    models = fake_server(tmp_path, port, KINDS)
    (tmp_path / "models" / "Tiny-Rerank.gguf").unlink()
    assert sulba.serve(fake_command(tmp_path, port), tmp_path, models, port, check=True) == 1
    assert capsys.readouterr().out == (
        "Loading Tiny, Tiny-Embed and Tiny-Rerank...\n"
        "Tiny-Rerank didn't load. The last of what llama.cpp's server wrote:\n"
        "  [Tiny-Rerank] failed to load model models/Tiny-Rerank.gguf\n"
    )
    assert not sulba.in_use(port)


def test_a_server_that_stops_shows_why(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    port = sulba.free_port()
    models = fake_server(tmp_path, port, KINDS[:1])
    script = str(tmp_path / "server.py")
    stops = [sys.executable, script, "--stop", "error: failed to read the preset"]
    assert sulba.serve(stops, tmp_path, models, port, check=True) == 1
    said = capsys.readouterr().out
    assert "llama.cpp's server stopped. The last of what it wrote:\n" in said
    assert "  error: failed to read the preset\n" in said


def test_a_port_in_use_is_said_before_the_server_starts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    models = [{"title": "Tiny", "kind": "chat"}]
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        port = taken.getsockname()[1]
        started = [sys.executable, "-c", "raise SystemExit('started')"]
        assert sulba.serve(started, tmp_path, models, port, check=True) == 1
    assert capsys.readouterr().out == (
        f"Port {port} is in use, perhaps by llama.cpp's server already running. Stop that, or run "
        f"uv run sulba.py model --port {port + 1}.\n"
    )
    assert not (tmp_path / f"server-{port}.log").exists()


def test_a_port_held_without_answering_is_said(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    models = [{"title": "Tiny", "kind": "chat"}]
    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        port = held.getsockname()[1]
        started = [sys.executable, "-c", "raise SystemExit('started')"]
        assert sulba.serve(started, tmp_path, models, port, check=True) == 1
    assert capsys.readouterr().out == (
        f"Port {port} is in use, perhaps by llama.cpp's server already running. Stop that, or run "
        f"uv run sulba.py model --port {port + 1}.\n"
    )
    assert not (tmp_path / f"server-{port}.log").exists()


@dataclass
class Forwarding:
    """The forwarder's port, in front of a stand-in for the server in router mode, and what lets
    the stand-in send the rest of a stream."""

    port: int
    go: threading.Event


@pytest.fixture
def forwarding() -> Iterator[Forwarding]:
    go = threading.Event()

    class Router(http.server.BaseHTTPRequestHandler):
        """The server in router mode as it answers: in chunks, closing the connection after each
        answer without saying so. A POST gets its body's length, a stream an event and, once the
        test lets it, the rest, and any other path the server's 404."""

        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            error = {"code": 404, "message": "File Not Found", "type": "not_found_error"}
            self.start(404, "application/json; charset=utf-8")
            self.part(json.dumps({"error": error}))
            self.end()

        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers["Content-Length"]))
            if self.path == "/v1/chat/completions":
                self.start(200, "text/event-stream")
                self.part("data: 1\n\n")
                self.part("data: 2\n\n" if go.wait(10) else "data: late\n\n")
            else:
                self.start(200, "application/json; charset=utf-8")
                self.part(str(len(body)))
            self.end()

        def start(self, status: int, kind: str) -> None:
            self.send_response_only(status)
            self.send_header("Content-Type", kind)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

        def part(self, text: str) -> None:
            self.wfile.write(b"%X\r\n%s\r\n" % (len(text), text.encode()))

        def end(self) -> None:
            self.wfile.write(b"0\r\n\r\n")
            self.close_connection = True

        def log_message(self, *args: Any) -> None:
            pass

    forwarder = sulba.Forwarder(0)
    router = http.server.ThreadingHTTPServer(("127.0.0.1", forwarder.target), Router)
    for server in (forwarder, router):
        threading.Thread(target=server.serve_forever, daemon=True).start()
    yield Forwarding(forwarder.server_address[1], go)
    for server in (forwarder, router):
        server.shutdown()
        server.server_close()


def test_a_program_keeps_its_connection_from_request_to_request(forwarding: Forwarding) -> None:
    connection = http.client.HTTPConnection("127.0.0.1", forwarding.port, timeout=10)
    connection.connect()
    opened = connection.sock
    for count in range(1, 51):
        connection.request("POST", "/v1/embeddings", body=b"x" * count)
        answer = connection.getresponse()
        assert (answer.status, answer.read()) == (200, str(count).encode())
        assert connection.sock is opened
    connection.close()


def test_the_servers_answers_come_back_as_they_are(forwarding: Forwarding) -> None:
    connection = http.client.HTTPConnection("127.0.0.1", forwarding.port, timeout=10)
    connection.request("GET", "/v1/nothing")
    answer = connection.getresponse()
    assert answer.status == 404
    assert answer.getheader("Content-Type") == "application/json; charset=utf-8"
    assert json.loads(answer.read())["error"]["message"] == "File Not Found"
    connection.close()


def test_a_streamed_answer_comes_as_the_server_sends_it(forwarding: Forwarding) -> None:
    connection = http.client.HTTPConnection("127.0.0.1", forwarding.port, timeout=30)
    connection.request("POST", "/v1/chat/completions", body=b'{"stream": true}')
    answer = connection.getresponse()
    assert answer.getheader("Content-Type") == "text/event-stream"
    first = b""
    while len(first) < len(b"data: 1\n\n"):
        first += answer.read1()
    # The stand-in sends the rest only once the first event has come through the forwarder.
    forwarding.go.set()
    assert first + answer.read() == b"data: 1\n\ndata: 2\n\n"
    connection.close()


def test_a_request_sent_in_chunks_reaches_the_server_whole(forwarding: Forwarding) -> None:
    connection = http.client.HTTPConnection("127.0.0.1", forwarding.port, timeout=10)
    connection.request("POST", "/v1/embeddings", body=iter([b"abc", b"de"]))
    answer = connection.getresponse()
    assert (answer.status, answer.read()) == (200, b"5")
    connection.request("POST", "/v1/embeddings", body=b"abc")
    assert connection.getresponse().read() == b"3"
    connection.close()


def test_the_models_are_loading_until_the_server_listens() -> None:
    forwarder = sulba.Forwarder(0)
    threading.Thread(target=forwarder.serve_forever, daemon=True).start()
    connection = http.client.HTTPConnection("127.0.0.1", forwarder.server_address[1], timeout=10)
    try:
        for _ in range(2):
            connection.request("GET", "/v1/models")
            answer = connection.getresponse()
            assert answer.status == 503
            assert json.loads(answer.read()) == {
                "error": {"message": "Loading model", "type": "unavailable_error", "code": 503}
            }
    finally:
        connection.close()
        forwarder.shutdown()
        forwarder.server_close()
