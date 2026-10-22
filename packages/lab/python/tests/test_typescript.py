"""The runner's TypeScript runs (decision record 39). The first fetches Node.js and the packages
the session's package-lock.json pins into the cache folder, where later runs find them."""

import hashlib
import http.server
import json
import platform
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import sulba_runner
from sulba_fixtures import cache_folder
from sulba_runner import run

SESSION = Path(__file__).with_name("typescript")
TESTS = ["tests/totals.test.ts"]
ADDS = {
    "id": "tst_ts0001",
    "name": "Adds the amounts",
    "status": "pass",
    "message": None,
    "expected": None,
    "actual": None,
    "location": None,
    "output": "",
    "note": None,
}
WITHOUT_ID = {**ADDS, "id": None, "name": "A test without an id"}


def session() -> dict[str, str]:
    return {
        path.relative_to(SESSION).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(SESSION.rglob("*"))
        if path.is_file()
    }


def ran(files: dict[str, str], tests: list[str]) -> dict[str, Any]:
    result = json.loads(run(json.dumps(files), json.dumps(tests)))
    assert result.pop("durationMs") >= 0
    for test in result["tests"]:
        assert test.pop("durationMs") >= 0
    return result


def test_each_test_gives_its_result() -> None:
    assert ran(session(), TESTS) == {
        "tests": [
            ADDS,
            {
                **ADDS,
                "id": "tst_ts0002",
                "name": "Shows dollars and cents",
                "status": "fail",
                "message": "Expected values to be strictly deep-equal:",
                "expected": "[ '15.50', '0.5' ]",
                "actual": "[ '15.50', '0.05' ]",
            },
            {
                **ADDS,
                "id": "tst_ts0003",
                "name": "Rounds part of a cent",
                "status": "error",
                "message": "RangeError: 0.5 isn't a whole number of cents.",
                "location": {"file": "totals.ts", "line": 9},
            },
            WITHOUT_ID,
        ],
        "problem": None,
        "output": "Adding 2 amounts.\n",
    }


def test_a_type_error_stops_the_run_before_its_tests() -> None:
    files = session()
    files["totals.ts"] = files["totals.ts"].replace("): string {", "): number {")
    result = ran(files, TESTS)
    assert result["tests"] == []
    assert result["problem"] == {
        "kind": "TS2322",
        "message": "Type 'string' is not assignable to type 'number'.",
        "location": {"file": "totals.ts", "line": 11},
    }
    assert result["output"].startswith("totals.ts(11,3): error TS2322:")


def test_a_file_that_stops_as_it_loads_is_the_runs_problem() -> None:
    files = session()
    files["totals.ts"] += "\nthrow new Error('The totals are closed.');\n"
    result = ran(files, TESTS)
    assert result["tests"] == []
    assert result["problem"] == {
        "kind": "Error",
        "message": "The totals are closed.",
        "location": {"file": "totals.ts", "line": 14},
    }
    # Node's own account of the error, with the session's paths as the learner sees them.
    assert "totals.ts:14" in result["output"]
    assert "file://" not in result["output"]


def test_a_run_with_python_and_typescript_tests_gives_each_result() -> None:
    files = session()
    files["tests/test_totals.py"] = (
        "import pytest\n\n\n"
        '@pytest.mark.id("tst_ts0005")\n'
        "def test_in_python():\n"
        '    """Runs beside the TypeScript tests"""\n'
        "    assert 1 + 1 == 2\n"
    )
    result = ran(files, [*TESTS, "tests/test_totals.py"])
    assert [(test["id"], test["status"]) for test in result["tests"]] == [
        ("tst_ts0005", "pass"),
        ("tst_ts0001", "pass"),
        ("tst_ts0002", "fail"),
        ("tst_ts0003", "error"),
        (None, "pass"),
    ]


def test_the_packages_are_installed_once_and_runs_leave_nothing_behind() -> None:
    files = session()
    ran(files, TESTS)
    pinned = f"{sulba_runner.NODE}\0{files['package.json']}\0{files['package-lock.json']}"
    folder = cache_folder() / "npm" / hashlib.sha256(pinned.encode()).hexdigest()
    installed = (folder / "node_modules" / "typescript" / "package.json").stat().st_mtime_ns
    ran(files, TESTS)
    assert (folder / "node_modules" / "typescript" / "package.json").stat().st_mtime_ns == installed
    assert list((folder / "runs").iterdir()) == []


def test_a_run_says_whether_it_fetches_node_or_the_packages_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ran(session(), TESTS)
    assert not sulba_runner.fetches_first(session())
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert sulba_runner.fetches_first(session())


def test_a_run_without_the_labs_packages_says_so() -> None:
    files = session()
    del files["package-lock.json"]
    assert ran(files, TESTS)["problem"] == {
        "kind": "RunError",
        "message": "A TypeScript run needs the lab's package.json and package-lock.json.",
        "location": None,
    }


@pytest.fixture
def publisher(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """A publisher of Node.js on this machine, which sends something other than the build the
    runner pins, with the cache folder in tmp_path."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Length", "4")
            self.end_headers()
            self.wfile.write(b"node")

        def log_message(self, *args: Any) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    system = (platform.system(), platform.machine())
    monkeypatch.setattr(sulba_runner, "NODE_RELEASES", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setattr(sulba_runner, "NODE_BUILDS", {system: ("linux-x64.tar.xz", 4, "0" * 64)})
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    yield
    server.shutdown()


def test_a_node_other_than_the_pinned_one_is_refused(publisher: None, tmp_path: Path) -> None:
    assert ran(session(), TESTS)["problem"] == {
        "kind": "RunError",
        "message": "127.0.0.1 sent a different Node.js from the one the lab was made with.",
        "location": None,
    }
    assert not (tmp_path / "sulba" / "node").exists()


def test_a_system_without_a_build_of_node_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.machine", lambda: "riscv64")
    assert ran(session(), TESTS)["problem"] == {
        "kind": "RunError",
        "message": f"Node.js {sulba_runner.NODE} has no build for Linux on riscv64.",
        "location": None,
    }
