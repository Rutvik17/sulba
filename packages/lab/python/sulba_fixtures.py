"""The fixtures a session's tests can ask for: `loop`, an event loop on a virtual clock (decision
record 21), and `typecheck`, mypy's errors in the session's files (decision record 22).

The runner loads this module as a pytest plugin. A test that runs the learner's own tests with
pytest's pytester loads it in that run too, so their tests can ask for the same fixtures:
`pytester.runpytest("-p", "sulba_fixtures")`.
"""

from __future__ import annotations

import asyncio
import functools
import gc
import sys
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import pytest

# mypy's options for a session's files: --strict, with no config file, as if on Linux, so the
# browser, a learner's machine and CI report the same errors (decision record 22).
MYPY_OPTIONS = ["--strict", "--config-file=", "--platform", "linux", "--no-error-summary"]


@functools.cache
def mypy_cache() -> str:
    """A folder for mypy's cache that lasts as long as the runner, so a check after the first
    reads what hasn't changed from it."""
    return tempfile.mkdtemp(prefix="sulba-mypy-")


def check_types(*files: str) -> list[str]:
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


@contextmanager
def threads_on_the_loop() -> Iterator[None]:
    """While a test runs, the work anyio would hand to a worker thread runs on the loop instead.

    Starlette, and so FastAPI, run a `def` endpoint or dependency in anyio's worker threads.
    A VirtualClockLoop waits on no thread, and Pyodide has none, so the work runs where the
    test's coroutine runs, with the same result. anyio is imported by then, by the app the test
    imports, or not used at all."""
    to_thread = sys.modules.get("anyio.to_thread")
    if to_thread is None:
        yield
        return
    in_a_thread = to_thread.run_sync

    async def run_sync(func: Callable[..., Any], *args: Any, **_: Any) -> Any:
        return func(*args)

    to_thread.run_sync = run_sync
    try:
        yield
    finally:
        to_thread.run_sync = in_a_thread


@pytest.fixture
def loop() -> Iterator[VirtualClockLoop]:
    """A new VirtualClockLoop for the test, whose time starts at 0. Afterwards, as asyncio.run
    does, the tasks left waiting are cancelled before the loop closes."""
    loop = VirtualClockLoop()
    with threads_on_the_loop():
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
def typecheck() -> Callable[..., list[str]]:
    """typecheck("shapes.py") gives mypy's errors in the session's file under --strict, one line
    each, the same in Pyodide and CPython."""
    return check_types
