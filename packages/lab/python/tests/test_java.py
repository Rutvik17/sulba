"""The runner's Java runs (decision record 45). The first fetches the JDK and the jars into the
cache folder, where later runs find them."""

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

SESSION = Path(__file__).with_name("java")
TESTS = ["tests/TotalsTest.java"]
ADDS = {
    "id": "tst_java01",
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
            "id": "tst_java02",
            "name": "Shows dollars and cents",
            "status": "fail",
            "message": "expected: <0.05> but was: <0.5>",
            "expected": "0.05",
            "actual": "0.5",
        },
        # Jackson is on every run's class path.
        {**ADDS, "id": "tst_java03", "name": "Writes a total as JSON"},
    ]
    assert result["problem"] is None
    assert "Adding 2 amounts." in result["output"]


def test_an_exception_is_an_error_at_the_line_of_the_code_that_threw() -> None:
    result = ran(session(), ["tests/errors/ErrorsTest.java"])
    assert result["tests"] == [
        {
            **ADDS,
            "id": "tst_java04",
            "name": "Takes the first of no amounts",
            "status": "error",
            "message": "ArrayIndexOutOfBoundsException: Index 0 out of bounds for length 0",
            "location": {"file": "Totals.java", "line": 23},
        },
        {**ADDS, "id": "tst_java05", "name": "Takes the first of two"},
    ]


def test_tests_in_several_folders_run_together() -> None:
    result = ran(session(), [*TESTS, "tests/errors/ErrorsTest.java"])
    assert [(test["id"], test["status"]) for test in result["tests"]] == [
        ("tst_java01", "pass"),
        ("tst_java02", "fail"),
        ("tst_java03", "pass"),
        ("tst_java04", "error"),
        ("tst_java05", "pass"),
    ]


def test_a_file_that_doesnt_compile_stops_the_run_before_its_tests() -> None:
    files = session()
    files["Totals.java"] = files["Totals.java"].replace("return total;", 'return "total";')
    result = ran(files, TESTS)
    assert result["tests"] == []
    assert result["problem"] == {
        "kind": "BuildError",
        "message": "incompatible types: String cannot be converted to int",
        "location": {"file": "Totals.java", "line": 15},
    }
    assert "Totals.java:15: error: incompatible types" in result["output"]


def test_tests_that_dont_compile_with_the_code_stop_the_run_too() -> None:
    files = session()
    files["Totals.java"] = files["Totals.java"].replace("String dollars(", "String inDollars(")
    assert ran(files, TESTS)["problem"] == {
        "kind": "BuildError",
        "message": "cannot find symbol",
        "location": {"file": "tests/TotalsTest.java", "line": 17},
    }


def test_a_test_file_the_run_leaves_out_isnt_compiled() -> None:
    files = session()
    files["tests/LaterTest.java"] = "class LaterTest { void later() { Totals.notWrittenYet(); } }\n"
    assert ran(files, TESTS)["problem"] is None


def test_a_run_with_python_and_java_tests_gives_each_result() -> None:
    files = session()
    files["tests/test_totals.py"] = (
        "import pytest\n\n\n"
        '@pytest.mark.id("tst_java06")\n'
        "def test_in_python():\n"
        '    """Runs beside the Java tests"""\n'
        "    assert 1 + 1 == 2\n"
    )
    result = ran(files, [*TESTS, "tests/test_totals.py"])
    assert [(test["id"], test["status"]) for test in result["tests"]] == [
        ("tst_java06", "pass"),
        ("tst_java01", "pass"),
        ("tst_java02", "fail"),
        ("tst_java03", "pass"),
    ]


def test_the_learners_own_java_settings_dont_reach_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", "-Xmx1k")
    monkeypatch.setenv("CLASSPATH", "nowhere")
    assert ran(session(), TESTS)["tests"][0] == ADDS


def test_a_run_says_whether_it_fetches_java_first(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ran(session(), TESTS)
    assert not sulba_runner.java_fetches_first()
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert sulba_runner.java_fetches_first()


@pytest.fixture
def publisher(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """A publisher of the JDK on this machine, which sends something other than the archive the
    runner pins, with the cache folder in tmp_path."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Length", "4")
            self.end_headers()
            self.wfile.write(b"java")

        def log_message(self, *args: Any) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    system = (platform.system(), platform.machine())
    monkeypatch.setattr(sulba_runner, "JAVA_RELEASES", f"http://127.0.0.1:{server.server_port}")
    monkeypatch.setattr(
        sulba_runner, "JAVA_BUILDS", {system: ("linux-amd64-lite.tar.gz", 4, "0" * 64)}
    )
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    yield
    server.shutdown()


def test_a_jdk_other_than_the_pinned_one_is_refused(publisher: None, tmp_path: Path) -> None:
    assert ran(session(), TESTS)["problem"] == {
        "kind": "RunError",
        "message": "127.0.0.1 sent a different JDK from the one the lab was made with.",
        "location": None,
    }
    assert not (tmp_path / "sulba" / "java").exists()


def test_a_system_without_a_build_of_the_jdk_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr("platform.machine", lambda: "riscv64")
    assert ran(session(), TESTS)["problem"] == {
        "kind": "RunError",
        "message": f"Liberica JDK {sulba_runner.JAVA} has no build for Linux on riscv64.",
        "location": None,
    }
