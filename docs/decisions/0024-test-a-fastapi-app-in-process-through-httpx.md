# 24. Test a FastAPI app in process, through httpx on the test's loop

- Status: accepted
- Date: 2026-10-16

## Context

The Beginner level ends in a prediction service: a model served from a FastAPI endpoint. Its code is built and checked like a lab's, so its tests have to run in the browser and give the same result in Pyodide and CPython (record 17). Pyodide 314.0.7 ships FastAPI and httpx but no server, and a browser can't open a socket. Pyodide has no threads either. Asyncio code in a test already runs on a loop with a virtual clock (record 21).

## Decision

- **Packages:** `fastapi` and `httpx` join the packages a stage can load, pinned for CPython at the versions Pyodide ships.
- **Requests:** a test sends each request in process, with an `httpx.AsyncClient` over `ASGITransport(app=app)`, run on the `loop` fixture. No server, socket or thread is involved.
- **`def` endpoints:** while a test uses the `loop`, the work Starlette hands to anyio's worker threads, a `def` endpoint or dependency, runs on the loop instead, with the same result.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| httpx's ASGITransport on the `loop` fixture, with anyio's thread work run on the loop (chosen) | The same result in Pyodide and CPython; the form FastAPI documents for tests with async code; `def` and `async def` endpoints both work | Each request is a coroutine the test runs on the loop; an app's lifespan events don't run |
| The same, with `async def` endpoints only | No change to the runner | A `def` endpoint, which FastAPI recommends for blocking calls, fails: "can't start new thread" in Pyodide, and in CPython the loop can't wait for the thread |
| FastAPI's `TestClient` | The usual way to test a FastAPI app, from plain test functions | Runs the app on a second thread: in Pyodide it fails with "can't start new thread" |
| Async tests under anyio's `@pytest.mark.anyio`, as FastAPI's page writes them | Exactly the documented form | In Pyodide anyio's runner fails: "Cannot stack switch because the Python entrypoint was a synchronous function" |
| A server on the learner's machine | Requests over real HTTP | Every run leaves the browser, for the command record 17 plans but hasn't built |

## Evidence

- Pyodide 314.0.7's lock file lists fastapi 0.136.1, starlette 1.0.0, pydantic 2.12.5, pydantic-core 2.41.5, httpx 0.28.1 and anyio 4.13.0, and no ASGI server.
- FastAPI's [Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/) sends requests with `AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`, and says that the TestClient's "magic doesn't work anymore when we're using it inside asynchronous functions", and that "If your application relies on lifespan events, the AsyncClient won't trigger these events."
- FastAPI's [Concurrency and async / await](https://fastapi.tiangolo.com/async/): a path operation declared with `def` "is run in an external threadpool that is then awaited", and so is a `def` dependency; for code that doesn't wait on anything else, "use `async def`".
- In Starlette 1.0.0's `starlette/concurrency.py`, `run_in_threadpool`, which FastAPI's routing and dependencies call for `def` functions, awaits `anyio.to_thread.run_sync(func)`, looked up when it's called.
- Run through Sulba's runner, `TestClient` and `@pytest.mark.anyio` pass in CPython and fail in Pyodide with the errors above. Without this change, a `def` endpoint on the `loop` fails in both: in Pyodide with "can't start new thread", and in CPython with "Every task is waiting on something that never happens." The `uses-fastapi` fixture, with a GET, a body read into a pydantic model, a 422, a `def` endpoint with a dependency and the OpenAPI schema, gives the same results in both.

## Why

Requests in process are the only form that runs in both runtimes, and it's FastAPI's own form for async tests, so a learner meets it in FastAPI's documentation too. Running anyio's thread work on the loop keeps `def` endpoints, the form FastAPI recommends for blocking calls, from failing on an error about threads that a learner can't fix. The strongest case against: a learner who writes their own tests with `TestClient`, as FastAPI's own Testing tutorial does, sees them fail in the browser.

## Consequences

A stage's tests say how to send a request, since the usual `TestClient` doesn't work in the browser. On the `loop`, a `def` endpoint runs on the loop rather than beside it, which only a test of concurrency could tell. An app whose setup is in a lifespan handler needs the test to enter it, so a stage's app loads what it needs when it's imported. FastAPI's first import takes seconds in a browser, and is made before a run's time starts, as for every package.

## Revisit when

Pyodide gains threads, or FastAPI's `TestClient` runs without a second thread.
