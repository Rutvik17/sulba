# 21. Test asyncio code on an event loop with a virtual clock

- Status: accepted
- Date: 2026-10-16

## Context

Python for programmers teaches asyncio: lookups made a few at a time, timeouts and task groups. A stage's tests have to run the learner's coroutines in Pyodide, in the browser, and in CPython, give the same results in each, and finish well inside a browser run's time limit even when the code waits on a timeout of a minute. The runner calls pytest from a synchronous function in both runtimes (decision record 17).

## Decision

- **The loop:** the runner's pytest plugin (`packages/lab/python/sulba_runner.py`) holds `VirtualClockLoop`, a subclass of asyncio's `BaseEventLoop` whose clock jumps to its next timer instead of waiting for it. It waits on no I/O, and sets Pyodide's own loop aside while it runs.
- **In a test:** the plugin gives each test that asks for it a `loop` fixture, a new `VirtualClockLoop` whose time starts at 0. A test runs a coroutine with `loop.run_until_complete(...)` and reads the seconds that passed with `loop.time()`. After the test, the tasks left waiting are cancelled, as `asyncio.run` does, and the loop is closed.
- **Code that waits forever:** when every task is waiting and no timer is left, the loop raises `RuntimeError: Every task is waiting on something that never happens.`, where a real loop would wait until the run's time limit.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A loop with a virtual clock, given as a fixture (chosen) | The same times in Pyodide and CPython; a minute's timeout takes no time; code that waits forever fails at once, with a message | Sets the running loop with asyncio's private `_get_running_loop` and `_set_running_loop`, as Pyodide's own loop does; code under test can't wait on sockets or threads |
| `asyncio.run`, on Pyodide's own loop | The loop a learner's code would run on in Pyodide | Fails in a synchronous run: Pyodide's loop can't block, and needs stack switching from an asynchronous entry point; real sleeps count against the time limit |
| pytest-asyncio 0.25.3, which Pyodide ships | Tests written as `async def`, as many projects write them | Fails in Pyodide the same way, since it runs Pyodide's own loop; runs on real time; uses asyncio's policy functions, deprecated for removal in Python 3.16 |
| asyncio's `SelectorEventLoop` with a fake selector | A documented loop class to build on | Its constructor makes a socket pair to wake itself, and Pyodide ends with a fatal error trying to open one |

## Evidence

- In CPython 3.14.2, `BaseEventLoop._run_once` waits for its next timer by calling `self._selector.select(timeout)`, with `None` for the timeout when nothing is scheduled, and `run_until_complete` refuses to start while another loop is running ([base_events.py](https://github.com/python/cpython/blob/v3.14.2/Lib/asyncio/base_events.py)).
- `loop.time()` returns the time "according to the event loop's internal monotonic clock" ([event loop](https://docs.python.org/3.14/library/asyncio-eventloop.html)), and `asyncio.sleep` and `asyncio.timeout` schedule their timers from it with `loop.call_later` and `loop.call_at` ([tasks.py](https://github.com/python/cpython/blob/v3.14.2/Lib/asyncio/tasks.py), [timeouts.py](https://github.com/python/cpython/blob/v3.14.2/Lib/asyncio/timeouts.py)).
- Pyodide 314.0.7's `WebLoop` sets itself as the running loop when it's made, always reports itself running, and can't block in `run_until_complete` (`pyodide/webloop.py` in its `python_stdlib.zip`).
- Run from a synchronous call in Pyodide 314.0.7 under Node: `asyncio.run(asyncio.sleep(0))` and a new loop's `run_until_complete` raise `RuntimeError: Cannot stack switch because the Python entrypoint was a synchronous function`; a test marked for pytest-asyncio 0.25.3 fails with the same error, with warnings that `asyncio.set_event_loop_policy` is deprecated; and `asyncio.SelectorEventLoop()` ends Pyodide with a fatal error from `socket.socketpair`. The same calls succeed in CPython 3.14.2.
- A `VirtualClockLoop` runs a hundred lookups behind a semaphore of eight, a timeout and a task group to the same results and times in Pyodide and CPython (`packages/lab/fixtures/uses-asyncio`).

## Why

Only a loop of the runner's own runs coroutines from a synchronous test in Pyodide, and once the runner has its own loop, a virtual clock costs a few lines and makes the tests exact: a stage can say that a hundred lookups took 3.25 seconds, and check it, in both runtimes. The strongest case against: the loop relies on two private asyncio functions, which a new Python could change, and stages can't teach asyncio code that waits on sockets or threads.

## Consequences

The fixture's tests in both runtimes fail if a Pyodide or Python update breaks the private functions, before any stage does. Stages that need real network I/O, or `asyncio.to_thread`, run on the learner's machine through the `sulba` command, with a record of their own when the first one comes.

## Revisit when

asyncio gains a public way to run a loop of one's own while another is running, or Pyodide can run a coroutine to completion from a synchronous call.
