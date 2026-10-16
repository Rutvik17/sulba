"""Runs a session's tests and reports one result per test.

The browser calls run() in Pyodide and the sulba command calls it in CPython, so a test reports
the same way wherever it runs. Arguments and the result are JSON text, which crosses from
JavaScript into Python without conversion.
"""

from __future__ import annotations

import ast
import asyncio
import functools
import gc
import importlib
import io
import json
import math
import os
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import chdir, contextmanager, redirect_stderr, redirect_stdout, suppress
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

# The longest value or message a result carries. A failed check on a large array would
# otherwise send all of it.
LIMIT = 1000

# mypy's options for a session's files: --strict, with no config file, as if on Linux, so the
# browser, a learner's machine and CI report the same errors (decision record 22).
MYPY_OPTIONS = ["--strict", "--config-file=", "--platform", "linux", "--no-error-summary"]


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
        write(root, files)
        report = Report(root)
        started = time.perf_counter()
        exit_code = within(root, lambda: pytest.main(arguments(tests, config), plugins=[report]))
        result = report.result(int(exit_code))
        result["durationMs"] = round((time.perf_counter() - started) * 1000)
    return json.dumps(result)


def prepare(files_json: str, packages_json: str) -> None:
    """Import the modules that the session's Python files import from these packages, and with
    mypy among them, check the session's files with it once.

    The first import of a module such as scipy.stats can take seconds in a browser, as can
    mypy's first check, and the browser times a run from after this, so a run's time goes on
    the session's own code. Only the packages' modules are imported, never the session's files.
    """
    files: dict[str, str] = json.loads(files_json)
    packages = set(json.loads(packages_json))
    for name in imported(files):
        if name.split(".")[0] in packages:
            # A module that isn't there fails again in the run, which reports it.
            with suppress(Exception):
                importlib.import_module(name)
    if "mypy" in packages:
        # A problem here shows again in the run, which reports it.
        with suppress(Exception):
            warm(files)


def warm(files: dict[str, str]) -> None:
    """Check the session's own Python files with mypy, in a folder of their own, so that the
    types of what they import are in mypy's cache before a run's time starts. mypy's first check
    reads the standard library's types, which takes seconds in a browser.

    mypy keeps a file's errors in its cache with the path it was given, and gives them again
    while the file is unchanged, so the files are checked from their folder by name, as a test
    checks them."""
    sources = [name for name in files if name.endswith(".py") and not name.startswith("tests/")]
    with tempfile.TemporaryDirectory(prefix="sulba-") as folder, chdir(folder):
        write(Path(folder), {name: files[name] for name in sources})
        typecheck(*sources)
    # mypy keeps the types it has read for as long as Python runs. Frozen, they're left out of
    # every later garbage collection, which would otherwise take twice as long.
    gc.collect()
    gc.freeze()


@functools.cache
def mypy_cache() -> str:
    """A folder for mypy's cache that lasts as long as the runner, so a check after the first
    reads what hasn't changed from it."""
    return tempfile.mkdtemp(prefix="sulba-mypy-")


def typecheck(*files: str) -> list[str]:
    """mypy's errors in these files, each line as mypy prints it, such as
    `shapes.py:4: error: Function is missing a type annotation  [no-untyped-def]`."""
    from mypy import api

    # mypy raises the recursion limit and the garbage collector's thresholds for its own work,
    # and leaves them so. The session's code runs with Python's own.
    limit, thresholds = sys.getrecursionlimit(), gc.get_threshold()
    try:
        report, errors, _ = api.run([*MYPY_OPTIONS, "--cache-dir", mypy_cache(), *files])
    finally:
        sys.setrecursionlimit(limit)
        gc.set_threshold(*thresholds)
    if errors:
        raise RuntimeError(errors.strip())
    return report.splitlines()


def imported(files: dict[str, str]) -> list[str]:
    """Every module the Python files import, first to last. A name a from-import takes may be
    a module too, as in `from scipy import stats`, so it is listed under the module's name."""
    found: dict[str, None] = {}
    for name, text in files.items():
        if not name.endswith(".py"):
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(dict.fromkeys(alias.name for alias in node.names))
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                found[node.module] = None
                found.update(dict.fromkeys(f"{node.module}.{alias.name}" for alias in node.names))
    return list(found)


def figures(files_json: str) -> str:
    """Call figures() in the session's figures.py, and return the numbers it gives or its error.

    A stage's prose shows numbers from its figures.py rather than typing them, so every number a
    learner reads is computed, the same way in the browser's Python and in CPython.
    """
    files: dict[str, str] = json.loads(files_json)
    with tempfile.TemporaryDirectory(prefix="sulba-") as folder:
        root = Path(folder).resolve()
        write(root, files)
        try:
            values = within(root, lambda: importlib.import_module("figures").figures())
        except Exception as error:
            return json.dumps({"figures": None, "problem": f"{type(error).__name__}: {error}"})
    named = isinstance(values, dict) and all(
        isinstance(name, str) and isinstance(value, str) for name, value in values.items()
    )
    if not named:
        return json.dumps({"figures": None, "problem": "figures() must return names and strings."})
    return json.dumps({"figures": values, "problem": None})


def chart(files_json: str, values_json: str) -> str:
    """Call chart() in the session's chart.py with the sliders' values, and return what it draws
    or its error.

    A chart draws the learner's own functions: chart.py imports them from the session's files,
    and each slider's value arrives as a keyword argument.
    """
    files: dict[str, str] = json.loads(files_json)
    values: dict[str, float] = json.loads(values_json)
    with tempfile.TemporaryDirectory(prefix="sulba-") as folder:
        root = Path(folder).resolve()
        write(root, files)
        try:
            drawing = within(root, lambda: plain(importlib.import_module("chart").chart(**values)))
            return json.dumps({"chart": drawing, "problem": None}, allow_nan=False)
        # A learner's sys.exit() is an error in their code, not a reason to stop the runner.
        except (Exception, SystemExit) as error:
            message = clip(str(error).replace(f"{root}{os.sep}", ""))
            return json.dumps(
                {"chart": None, "problem": {"kind": type(error).__name__, "message": message}}
            )


def plain(value: object) -> object:
    """value as JSON holds it: NumPy arrays and numbers become lists and Python numbers, and a
    number that isn't finite becomes None, since JSON can't write it."""
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write(root: Path, files: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        path = root / safe(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")


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


class VirtualClockLoop(asyncio.BaseEventLoop):
    """An event loop whose clock jumps to its next timer instead of waiting for it.

    A test of asyncio code takes only as long as the code's own work, however long it sleeps,
    and the loop's time is the same in Pyodide and CPython. Pyodide's own loop can't run a
    coroutine to completion from a test, and asyncio's selector loop needs sockets that Pyodide
    doesn't have, so this loop waits on no I/O at all.
    """

    def __init__(self) -> None:
        super().__init__()
        self._now = 0.0
        # BaseEventLoop waits for its next timer by calling self._selector.select(timeout).
        self._selector = self

    def time(self) -> float:
        return self._now

    def select(self, timeout: float | None) -> list[Any]:
        # No timer to wait for, and no I/O to wake a task: the code waits forever.
        if timeout is None:
            raise RuntimeError("Every task is waiting on something that never happens.")
        self._now += timeout
        return []

    def _process_events(self, event_list: list[Any]) -> None:
        pass

    def _write_to_self(self) -> None:
        pass

    def run_forever(self) -> None:
        with self._alone():
            super().run_forever()

    def run_until_complete(self, future: Any) -> Any:
        with self._alone():
            return super().run_until_complete(future)

    @contextmanager
    def _alone(self) -> Iterator[None]:
        """Pyodide's loop counts as running from the moment it's made, and asyncio refuses to
        run a loop while another one is running, so it's set aside until this one stops."""
        running = asyncio._get_running_loop()
        asyncio._set_running_loop(None)
        try:
            yield
        finally:
            asyncio._set_running_loop(running)


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

    @pytest.fixture
    def loop(self) -> Iterator[VirtualClockLoop]:
        """A new VirtualClockLoop for the test, whose time starts at 0. Afterwards, as
        asyncio.run does, the tasks left waiting are cancelled before the loop closes."""
        loop = VirtualClockLoop()
        try:
            yield loop
        finally:
            waiting = asyncio.all_tasks(loop)
            for task in waiting:
                task.cancel()
            if waiting:
                loop.run_until_complete(asyncio.gather(*waiting, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    @pytest.fixture
    def typecheck(self) -> Callable[..., list[str]]:
        """typecheck("shapes.py") gives mypy's errors in the session's file under --strict, one
        line each, the same in Pyodide and CPython."""
        return typecheck

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
        for name, value in report.user_properties:
            if name == "note":
                entry["note"] = clip(str(value))
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
            "note": None,
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
        """The first line of an assertion's message, or the error's type and any message."""
        if failed:
            lines = str(error).strip().splitlines()
            return self.clean(lines[0] if lines else "The check failed.")
        said = str(error)
        return self.clean(f"{type(error).__name__}: {said}" if said else type(error).__name__)

    def problem_message(self, error: BaseException) -> str:
        return self.clean(error.msg if isinstance(error, SyntaxError) else str(error))

    def clean(self, text: str) -> str:
        """Paths shown from the session's folder, as the learner sees their files."""
        return clip(text.replace(f"{self.root}{os.sep}", ""))


def clip(text: str) -> str:
    return text if len(text) <= LIMIT else f"{text[: LIMIT - 1]}…"


if __name__ == "__main__":
    # One request per line of standard input and its answer on one line of standard output, so
    # checks can run many sessions in one process. A run is {"files": {...}, "tests": [...]},
    # {"files": {...}, "figures": true} asks for figures.py's numbers, and
    # {"files": {...}, "chart": {...}} for what chart.py draws with those values.
    for line in sys.stdin:
        request = json.loads(line)
        files = json.dumps(request["files"])
        if request.get("figures"):
            print(figures(files), flush=True)
        elif "chart" in request:
            print(chart(files, json.dumps(request["chart"])), flush=True)
        else:
            print(run(files, json.dumps(request["tests"])), flush=True)
