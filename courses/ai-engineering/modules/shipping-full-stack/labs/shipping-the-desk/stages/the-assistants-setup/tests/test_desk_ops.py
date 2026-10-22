import contextlib
import json
import logging

import httpx
import pytest
from desk_ops import JsonFormatter, config, production
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


class Pool:
    """A pool whose connections answer every query."""

    @contextlib.contextmanager
    def connection(self, timeout=None):
        class Connection:
            def execute(self, query):
                pass

        yield Connection()


def model(status):
    """A client to a model's server that answers every request with the status."""

    async def handle(request):
        return httpx.Response(status, json={})

    return httpx.AsyncClient(
        transport=httpx.MockTransport(handle), base_url="http://127.0.0.1:9931/v1"
    )


def desk():
    app = FastAPI()
    log = logging.getLogger("desk.test")

    @app.get("/conversations")
    def conversations():
        log.info("listed", extra={"headers": {"authorization": "Bearer abc123"}})
        return []

    app = production(app)
    app.state.pool = Pool()
    return app


def call(loop, app, path, status=200, headers=None):
    async def calls():
        app.state.client = model(status)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://desk") as client:
            return await client.get(path, headers=headers)

    return loop.run_until_complete(calls())


@pytest.mark.id("tst_5ecarg")
def test_logs_a_line_for_each_request_with_its_id(loop, lines):
    answer = call(loop, desk(), "/conversations", headers={"X-Request-ID": "trace-7"})
    assert answer.headers["x-request-id"] == "trace-7"
    entries = [json.loads(line) for line in lines.lines]
    request = entries[-1]
    assert request["message"] == "request"
    assert request["request_id"] == "trace-7"
    assert (request["method"], request["path"], request["status"]) == (
        "GET",
        "/conversations",
        200,
    )


@pytest.mark.id("tst_w17s3g")
def test_hides_secrets_in_a_line(loop, lines):
    call(loop, desk(), "/conversations")
    listed = json.loads(lines.lines[0])
    assert listed["headers"] == {"authorization": "[hidden]"}
    assert "abc123" not in "".join(lines.lines)


@pytest.mark.id("tst_dxoyzm")
def test_is_ready_when_the_database_and_the_model_answer(loop):
    answer = call(loop, desk(), "/ready")
    assert answer.status_code == 200
    assert answer.json() == {"checks": {"database": "ok", "model": "ok"}}


@pytest.mark.id("tst_yo20vb")
def test_says_what_isnt_ready(loop):
    answer = call(loop, desk(), "/ready", status=500)
    assert answer.status_code == 503
    assert answer.headers["content-type"] == "application/problem+json"
    assert answer.json()["detail"] == "Not ready: model."


@pytest.mark.id("tst_64pmic")
def test_takes_its_port_from_port():
    assert config({}).port == 8000
    assert config({"PORT": "10000"}).port == 10000
    with pytest.raises(ValueError, match="PORT"):
        config({"PORT": "http"})
