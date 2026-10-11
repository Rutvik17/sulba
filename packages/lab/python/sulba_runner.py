"""Runs a session's tests and reports one result per test.

The browser calls run() in Pyodide and the sulba command calls it in CPython, so a test reports
the same way wherever it runs. Arguments and the result are JSON text, which crosses from
JavaScript into Python without conversion.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import sys
import tempfile
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

# The longest value or message a result carries. A failed check on a large array would
# otherwise send all of it.
LIMIT = 1000


def run(files_json: str, tests_json: str) -> str:
    """Write the files to a new folder, run the test files there, and return the result."""
    files: dict[str, str] = json.loads(files_json)
    tests: list[str] = json.loads(tests_json)
    with tempfile.TemporaryDirectory(prefix="sulba-") as folder:
        # An empty config file beside the session, so pytest never picks up one from a folder
        # above it.
        config = Path(folder, "pytest.ini")
        config.write_text("[pytest]\n", encoding="utf-8")
        root = Path(folder, "session").resolve()
        for name, text in files.items():
            path = root / safe(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="")
        root.mkdir(exist_ok=True)
        report = Report(root)
        started = time.perf_counter()
        exit_code = within(root, lambda: pytest.main(arguments(tests, config), plugins=[report]))
        result = report.result(int(exit_code))
        result["durationMs"] = round((time.perf_counter() - started) * 1000)
    return json.dumps(result)


def arguments(tests: list[str], config: Path) -> list[str]:
    return [
        *tests,
        "-q",
        "--tb=no",
        "-p",
        "no:cacheprovider",
        "-c",
        str(config),
        "--rootdir",
        ".",
        # Print output is kept per test. Pyodide has no file descriptors to capture.
        "--capture=sys",
        # Test files are imported without changing sys.path, so the session's own modules are
        # found only in its folder.
        "--import-mode=importlib",
        "-W",
        "ignore",
    ]


def safe(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"A session file must sit inside the session: {name}")
    return path


def within(root: Path, action: Any) -> Any:
    """Run action from root, with root importable, then forget every module it loaded.

    pytest's own report is discarded: results come from the plugin. Its terminal plugin stays
    loaded, because pytest writes a failed assertion's explanation through it.
    """
    cwd = os.getcwd()
    path = sys.path[:]
    bytecode = sys.dont_write_bytecode
    os.chdir(root)
    sys.path.insert(0, str(root))
    sys.dont_write_bytecode = True
    importlib.invalidate_caches()
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return action()
    finally:
        os.chdir(cwd)
        sys.path[:] = path
        sys.dont_write_bytecode = bytecode
        for name, module in list(sys.modules.items()):
            file = getattr(module, "__file__", None)
            if file and Path(file).resolve().is_relative_to(root):
                del sys.modules[name]


def shown(value: object) -> str:
    text = repr(value)
    return text if len(text) <= LIMIT else f"{text[: LIMIT - 1]}…"


class Report:
    """A pytest plugin that keeps what a learner needs from each test."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.tests: dict[str, dict[str, Any]] = {}
        self.problem: dict[str, Any] | None = None
        self.output = ""
        self.compared: dict[str, tuple[str, str]] = {}
        self.current: str | None = None

    def pytest_configure(self, config: pytest.Config) -> None:
        config.addinivalue_line("markers", "id(value): the test's permanent id")

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_call(self, item: pytest.Item) -> Any:
        self.current = item.nodeid
        try:
            return (yield)
        finally:
            self.current = None

    # Tests are written `assert actual == expected`, so a failed comparison gives both sides.
    def pytest_assertrepr_compare(self, op: str, left: object, right: object) -> None:
        if self.current is not None and self.current not in self.compared:
            self.compared[self.current] = (shown(left), shown(right))

    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call: pytest.CallInfo[None]) -> Any:
        report: pytest.TestReport = yield
        entry = self.tests.setdefault(item.nodeid, self.entry(item))
        entry["durationMs"] += round(report.duration * 1000)
        # Each phase's report repeats the output of the phases before it.
        entry["output"] = report.capstdout + report.capstderr
        if report.failed and entry["status"] == "pass":
            excinfo = call.excinfo
            failed = excinfo is not None and excinfo.errisinstance(AssertionError)
            entry["status"] = "fail" if failed else "error"
            if excinfo is not None:
                entry["message"] = self.message(excinfo.value, failed)
                entry["location"] = self.location(excinfo)
            entry["actual"], entry["expected"] = self.compared.get(item.nodeid, (None, None))
        return report

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        self.output += report.capstdout + report.capstderr

    def pytest_exception_interact(
        self, node: pytest.Item | pytest.Collector, call: pytest.CallInfo[Any], report: Any
    ) -> None:
        if isinstance(node, pytest.Collector) and self.problem is None and call.excinfo:
            error = call.excinfo.value
            # pytest wraps an error raised while importing a test file. The learner needs the
            # error underneath, such as a syntax error in their own file.
            if isinstance(error, pytest.Collector.CollectError) and error.__cause__:
                error = error.__cause__
            self.problem = {
                "kind": type(error).__name__,
                "message": self.problem_message(error),
                "location": self.location(pytest.ExceptionInfo.from_exception(error)),
            }

    def entry(self, item: pytest.Item) -> dict[str, Any]:
        marker = item.get_closest_marker("id")
        doc = getattr(getattr(item, "function", None), "__doc__", None)
        return {
            "id": str(marker.args[0]) if marker and marker.args else None,
            "name": doc.strip().splitlines()[0] if doc and doc.strip() else item.name,
            "status": "pass",
            "message": None,
            "expected": None,
            "actual": None,
            "location": None,
            "output": "",
            "durationMs": 0,
        }

    def location(self, excinfo: pytest.ExceptionInfo[BaseException]) -> dict[str, Any] | None:
        """The deepest line of the session's own code, outside its tests, that the error passed."""
        error = excinfo.value
        if isinstance(error, SyntaxError) and error.filename and error.lineno:
            found = self.relative(error.filename)
            if found:
                return {"file": found, "line": error.lineno}
        place = None
        for entry in excinfo.traceback:
            found = self.relative(str(entry.path))
            if found and not found.startswith("tests/"):
                place = {"file": found, "line": entry.lineno + 1}
        return place

    def relative(self, file: str) -> str | None:
        path = Path(file).resolve()
        return path.relative_to(self.root).as_posix() if path.is_relative_to(self.root) else None

    def result(self, exit_code: int) -> dict[str, Any]:
        problem = self.problem
        # 0: every test passed. 1: some failed. 2: collection failed, which set the problem.
        if problem is None and exit_code not in (0, 1):
            ran = "No tests ran." if exit_code == 5 else f"pytest stopped with code {exit_code}."
            problem = {"kind": "RunError", "message": ran, "location": None}
        return {
            "tests": [] if problem else list(self.tests.values()),
            "problem": problem,
            "output": self.output,
        }

    def message(self, error: BaseException, failed: bool) -> str:
        """The first line of an assertion's message, or the error's type and message."""
        if failed:
            lines = str(error).strip().splitlines()
            return self.clean(lines[0] if lines else "The check failed.")
        return self.clean(f"{type(error).__name__}: {error}")

    def problem_message(self, error: BaseException) -> str:
        return self.clean(error.msg if isinstance(error, SyntaxError) else str(error))

    def clean(self, text: str) -> str:
        """Paths shown from the session's folder, as the learner sees their files."""
        return clip(text.replace(f"{self.root}{os.sep}", ""))


def clip(text: str) -> str:
    return text if len(text) <= LIMIT else f"{text[: LIMIT - 1]}…"


if __name__ == "__main__":
    # One request per line of standard input, as {"files": {...}, "tests": [...]}, and its result
    # on one line of standard output. Checks run many sessions in one process this way.
    for line in sys.stdin:
        request = json.loads(line)
        print(run(json.dumps(request["files"]), json.dumps(request["tests"])), flush=True)
