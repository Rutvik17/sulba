psycopg's pool is synchronous, so the query runs in a thread: `await run_in_threadpool(query)`, from `starlette.concurrency`, keeps the desk answering others meanwhile. `pool.connection(timeout=...)` limits the wait for a connection.

---

`asyncio.wait_for(check(), seconds)` raises `TimeoutError` when the check takes longer, and `asyncio.gather` runs every check at once.

---

`JSONResponse(content, status_code=..., media_type="application/problem+json")` answers with problem details. `HTTPStatus.SERVICE_UNAVAILABLE.phrase` is the title.
