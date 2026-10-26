"""The runner's Go runs (decision record 43). The first fetches Go into the cache folder, where
later runs find it."""

import http.server
import json
import platform
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import sulba_runner
from sulba_runner import run

SESSION = Path(__file__).with_name("go")
TESTS = ["tests/totals_test.go"]
ADDS = {
    "id": "tst_go0001",
    "name": "Adds the amounts",
    "status": "pass",
    "message": None,
    "expected": None,
    "actual": None,
    "location": None,
    "output": "",
    "note": None,
}


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
    result = ran(session(), TESTS)
    assert result["tests"] == [
        ADDS,
        {
            **ADDS,
            "id": "tst_go0002",
            "name": "Shows dollars and cents",
            "status": "fail",
            "message": 'got "0.5", want "0.05"',
        },
        # A second's wait on the test's own clock, which moves only when the test waits.
        {**ADDS, "id": "tst_go0003", "name": "Waits a second for the till"},
    ]
    assert result["problem"] is None
    assert "Adding 2 amounts." in result["output"]


def test_a_panic_is_an_error_and_stops_the_tests_after_it() -> None:
    result = ran(session(), ["tests/panics/panics_test.go"])
    assert result["tests"] == [
        {
            **ADDS,
            "id": "tst_go0004",
            "name": "Takes the first of no amounts",
            "status": "error",
            "message": "panic: runtime error: index out of range [0] with length 0",
            "location": {"file": "totals.go", "line": 26},
        },
        {
            **ADDS,
            "id": "tst_go0005",
            "name": "Takes the first of two",
            "status": "error",
            "message": "Didn't run: a test before it in its package panicked.",
        },
    ]


def test_each_folder_of_tests_is_a_package_of_its_own() -> None:
    result = ran(session(), [*TESTS, "tests/panics/panics_test.go"])
    assert [(test["id"], test["status"]) for test in result["tests"]] == [
        ("tst_go0001", "pass"),
        ("tst_go0002", "fail"),
        ("tst_go0003", "pass"),
        ("tst_go0004", "error"),
        ("tst_go0005", "error"),
    ]


def test_a_file_that_doesnt_build_stops_the_run_before_its_tests() -> None:
    files = session()
    files["totals.go"] = files["totals.go"].replace("return total\n", 'return "total"\n')
    result = ran(files, TESTS)
    assert result["tests"] == []
    assert result["problem"] == {
        "kind": "BuildError",
        "message": 'cannot use "total" (untyped string constant) as int value in return statement',
        "location": {"file": "totals.go", "line": 16},
    }
    assert './totals.go:16:9: cannot use "total"' in result["output"]


def test_what_vet_finds_stops_the_run_too() -> None:
    files = session()
    files["totals.go"] = files["totals.go"].replace(
        '"%d.%d", cents/100, cents%100', '"%d.%d", cents/100, "cents"'
    )
    result = ran(files, TESTS)
    assert result["tests"] == []
    assert result["problem"] == {
        "kind": "VetError",
        "message": 'fmt.Sprintf format %d has arg "cents" of wrong type string',
        "location": {"file": "totals.go", "line": 21},
    }


def test_a_test_file_the_run_leaves_out_isnt_built() -> None:
    files = session()
    files["tests/later_test.go"] = (
        'package tests\n\nimport (\n\t"testing"\n\n\t"example/totals"\n)\n\n'
        "func TestLater(t *testing.T) { totals.NotWrittenYet() }\n"
    )
    assert ran(files, TESTS)["problem"] is None


def test_the_learners_own_tests_build_with_the_run_but_dont_count() -> None:
    files = session()
    files["totals_test.go"] = (
        'package totals\n\nimport "testing"\n\nfunc TestMine(t *testing.T) { t.Fatal(Sum(nil)) }\n'
    )
    result = ran(files, TESTS)
    assert [test["id"] for test in result["tests"]] == ["tst_go0001", "tst_go0002", "tst_go0003"]
    files["totals_test.go"] = files["totals_test.go"].replace("Sum(nil)", "Sum(nil, 1)")
    assert ran(files, TESTS)["problem"] == {
        "kind": "BuildError",
        "message": "too many arguments in call to Sum",
        "location": {"file": "totals_test.go", "line": 5},
    }


def test_a_run_with_python_and_go_tests_gives_each_result() -> None:
    files = session()
    files["tests/test_totals.py"] = (
        "import pytest\n\n\n"
        '@pytest.mark.id("tst_go0006")\n'
        "def test_in_python():\n"
        '    """Runs beside the Go tests"""\n'
        "    assert 1 + 1 == 2\n"
    )
    result = ran(files, [*TESTS, "tests/test_totals.py"])
    assert [(test["id"], test["status"]) for test in result["tests"]] == [
        ("tst_go0006", "pass"),
        ("tst_go0001", "pass"),
        ("tst_go0002", "fail"),
        ("tst_go0003", "pass"),
    ]


def test_a_run_says_whether_it_fetches_go_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ran(session(), TESTS)
    assert not sulba_runner.go_fetches_first()
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert sulba_runner.go_fetches_first()


def test_a_run_without_the_labs_go_mod_says_so() -> None:
    files = session()
    del files["go.mod"]
    assert ran(files, TESTS)["problem"] == {
        "kind": "RunError",
        "message": "A Go run needs the lab's go.mod.",
        "location": None,
    }


@pytest.fixture
def publisher(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """A publisher of Go on this machine, which sends something other than the archive the runner
    pins, with the cache folder in tmp_path."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"go")

        def log_message(self, *args: Any) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    system = (platform.system(), platform.machine())
    monkeypatch.setattr(sulba_runner, "GO_RELEASES", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setattr(sulba_runner, "GO_BUILDS", {system: ("linux-amd64.tar.gz", 2, "0" * 64)})
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    yield
    server.shutdown()


def test_a_go_other_than_the_pinned_one_is_refused(publisher: None, tmp_path: Path) -> None:
    assert ran(session(), TESTS)["problem"] == {
        "kind": "RunError",
        "message": "127.0.0.1 sent a different Go from the one the lab was made with.",
        "location": None,
    }
    assert not (tmp_path / "sulba" / "go").exists()


def test_a_system_without_a_build_of_go_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.machine", lambda: "riscv64")
    assert ran(session(), TESTS)["problem"] == {
        "kind": "RunError",
        "message": f"Go {sulba_runner.GO} has no build for Linux on riscv64.",
        "location": None,
    }
