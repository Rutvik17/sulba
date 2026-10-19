import base64
import hashlib
import http.server
import json
import random
import shutil
import socket
import subprocess
import sys
import threading
import uuid
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
    for name in ["sulba_runner.py", "sulba_fixtures.py"]:
        shutil.copy(PYTHON / name, runner / name)
    lab = {
        "format": 1,
        "id": "lab_tally1",
        "title": "Tallies",
        "page": "https://sulba.dev/demo/counting/tallies/",
        "start": 0,
        "data": ["data/votes.csv"],
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
