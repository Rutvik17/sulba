import asyncio
import json
import logging

import httpx
import pytest
from desk_ops import JsonFormatter, config, model_check, production, readiness
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


class Lines(logging.Handler):
    """Keeps each of the desk's records as the line the desk's formatter writes."""

    def __init__(self):
        super().__init__()
        self.setFormatter(JsonFormatter())
        self.addFilter(lambda record: record.name.startswith("desk"))
        self.lines = []

    def emit(self, record):
        self.lines.append(self.format(record))


@pytest.fixture
def lines():
    handler = Lines()
    root = logging.getLogger()
    root.addHandler(handler)
    level = root.level
    root.setLevel(logging.INFO)
    yield handler
    root.removeHandler(handler)
    root.setLevel(level)


async def ok():
    pass


async def hangs():
    await asyncio.sleep(3600)


@pytest.mark.id("tst_bp8k8o")
def test_a_requests_line_leaves_out_its_query(loop, lines):
    app = FastAPI()

    @app.get("/auth/callback")
    def callback(code: str, state: str):
        return {}

    async def calls():
        transport = ASGITransport(app=production(app))
        async with AsyncClient(transport=transport, base_url="http://desk") as client:
            await client.get("/auth/callback?code=4/0AbCdEf&state=Qz9x")

    loop.run_until_complete(calls())
    request = json.loads(lines.lines[-1])
    assert request["path"] == "/auth/callback"
    assert "4/0AbCdEf" not in "".join(lines.lines)


@pytest.mark.id("tst_gjp2tx")
def test_readiness_asks_the_models_server_only_whether_the_model_is_loaded(loop):
    sent = []

    async def handle(request):
        sent.append((request.method, request.url.path))
        return httpx.Response(200, json={"status": "ok"})

    async def states():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handle), base_url="http://127.0.0.1:9931/v1"
        ) as client:
            return await readiness({"model": model_check(client)})

    assert loop.run_until_complete(states()) == {"model": "ok"}
    assert sent == [("GET", "/v1/health")]


@pytest.mark.id("tst_lh0vfw")
def test_a_check_that_hangs_is_given_two_seconds(loop):
    start = loop.time()
    states = loop.run_until_complete(readiness({"database": hangs, "model": ok}))
    assert loop.time() - start == pytest.approx(2.0)
    assert states == {"database": "No answer in 2 seconds.", "model": "ok"}


@pytest.mark.id("tst_cee6ch")
def test_listens_on_every_address():
    assert config({}).host == "0.0.0.0"
