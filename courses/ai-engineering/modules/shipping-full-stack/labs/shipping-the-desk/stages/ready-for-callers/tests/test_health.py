import asyncio

import httpx
import pytest
from fastapi import FastAPI
from health import database_check, model_check, readiness, router
from httpx import ASGITransport, AsyncClient
from psycopg_pool import ConnectionPool


def answering(status, wait=0.0):
    """A client to a model's server whose /health answers with the status, after a wait."""

    async def handle(request):
        assert request.url.path.endswith("/health")
        await asyncio.sleep(wait)
        return httpx.Response(status, json={"status": "ok"} if status == 200 else {})

    return httpx.AsyncClient(
        transport=httpx.MockTransport(handle), base_url="http://127.0.0.1:9931/v1"
    )


async def ok():
    pass


async def hangs():
    await asyncio.sleep(3600)


async def fails():
    raise ConnectionError("Connection refused.")


@pytest.mark.id("tst_8n2dwf")
def test_each_check_gives_ok_or_what_went_wrong(loop):
    states = loop.run_until_complete(readiness({"database": ok, "model": fails}))
    assert states == {"database": "ok", "model": "Connection refused."}


@pytest.mark.id("tst_du84f5")
def test_a_check_that_hangs_is_given_two_seconds_and_the_checks_run_at_once(loop):
    start = loop.time()
    states = loop.run_until_complete(
        readiness({"database": hangs, "model": hangs, "search": ok})
    )
    assert loop.time() - start == pytest.approx(2.0)
    assert states == {
        "database": "No answer in 2 seconds.",
        "model": "No answer in 2 seconds.",
        "search": "ok",
    }


@pytest.mark.id("tst_xanqwg")
def test_the_model_is_ready_once_its_server_has_loaded_it(loop):
    async def states():
        found = []
        for status in (200, 503, 500):
            async with answering(status) as client:
                found.append(await readiness({"model": model_check(client)}))
        return found

    loaded, loading, broken = loop.run_until_complete(states())
    assert loaded == {"model": "ok"}
    assert loading == {"model": "The model is still loading."}
    assert broken["model"].startswith("Server error '500")


@pytest.mark.id("tst_uj3n1f")
def test_the_database_is_ready_when_it_answers_a_query(loop, database):
    pool = ConnectionPool(database, min_size=1, max_size=1, open=False)
    pool.open(wait=True, timeout=10)
    try:
        assert loop.run_until_complete(
            readiness({"database": database_check(pool)})
        ) == {"database": "ok"}
    finally:
        pool.close()
    state = loop.run_until_complete(readiness({"database": database_check(pool)}))
    assert state["database"] != "ok"


def serving(loop, pool, client):
    app = FastAPI()
    app.include_router(router)
    app.state.pool = pool
    app.state.client = client

    async def go():
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://desk.test"
        ) as desk:
            return await desk.get("/ready")

    return loop.run_until_complete(go())


@pytest.mark.id("tst_xvlcqz")
def test_ready_answers_200_with_each_check_when_all_are_ok(loop, database):
    with ConnectionPool(database, min_size=1, max_size=1) as pool:
        answer = serving(loop, pool, answering(200))
    assert answer.status_code == 200
    assert answer.json() == {"checks": {"database": "ok", "model": "ok"}}


@pytest.mark.id("tst_w6cebp")
def test_ready_answers_503_with_problem_details_while_the_model_loads(loop, database):
    with ConnectionPool(database, min_size=1, max_size=1) as pool:
        answer = serving(loop, pool, answering(503))
    assert answer.status_code == 503
    assert answer.headers["content-type"] == "application/problem+json"
    assert answer.json() == {
        "type": "about:blank",
        "title": "Service Unavailable",
        "status": 503,
        "detail": "Not ready: model.",
        "checks": {"database": "ok", "model": "The model is still loading."},
    }


@pytest.mark.id("tst_juaznp")
def test_a_model_that_doesnt_answer_keeps_the_desk_out_of_service_in_two_seconds(
    loop, database
):
    with ConnectionPool(database, min_size=1, max_size=1) as pool:
        start = loop.time()
        answer = serving(loop, pool, answering(200, wait=3600))
    assert answer.status_code == 503
    assert loop.time() - start == pytest.approx(2.0)
    assert answer.json()["checks"]["model"] == "No answer in 2 seconds."
