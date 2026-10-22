import contextlib
import logging

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from main import config, production
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


@pytest.fixture(autouse=True)
def loggers():
    """Puts back what uvicorn's settings change in the loggers."""
    names = ["", "uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.asgi"]
    kept = {}
    for name in names:
        logger = logging.getLogger(name)
        kept[name] = (
            logger.handlers[:],
            logger.level,
            logger.propagate,
            logger.disabled,
        )
    yield
    for name, (handlers, level, propagate, disabled) in kept.items():
        logger = logging.getLogger(name)
        logger.handlers[:] = handlers
        logger.setLevel(level)
        logger.propagate = propagate
        logger.disabled = disabled


class Records(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def caller_seen(loop, settings, client, forwarded="203.0.113.7"):
    """The caller's address the desk sees, for a request from the client that says it's
    forwarding one from the address in X-Forwarded-For."""
    seen = {}

    async def app(scope, receive, send):
        seen["client"] = scope["client"][0]
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        pass

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"x-forwarded-for", forwarded.encode())],
        "client": (client, 50000),
        "server": ("10.0.0.2", 8000),
    }
    assert settings.proxy_headers
    proxy = ProxyHeadersMiddleware(app, trusted_hosts=settings.forwarded_allow_ips)
    loop.run_until_complete(proxy(scope, receive, send))
    return seen["client"]


class Pool:
    """A pool whose connections answer every query."""

    @contextlib.contextmanager
    def connection(self, timeout=None):
        class Connection:
            def execute(self, query):
                pass

        yield Connection()


def loaded_model():
    async def handle(request):
        return httpx.Response(200, json={"status": "ok"})

    return httpx.AsyncClient(
        transport=httpx.MockTransport(handle), base_url="http://127.0.0.1:9931/v1"
    )


@pytest.mark.id("tst_czuxgz")
def test_listens_on_every_address_on_port_8000_when_port_isnt_set():
    settings = config({})
    assert (settings.host, settings.port) == ("0.0.0.0", 8000)


@pytest.mark.id("tst_oxcpno")
def test_listens_on_the_port_in_port():
    assert config({"PORT": "10000"}).port == 10000


@pytest.mark.id("tst_trqpie")
@pytest.mark.parametrize("port", ["", "http", "0", "65536", "-1", "80.5"])
def test_refuses_a_port_that_isnt_one(port):
    with pytest.raises(ValueError, match="PORT"):
        config({"PORT": port})


@pytest.mark.id("tst_4drrnf")
def test_takes_the_callers_address_from_forwarded_headers_only_from_trusted_proxies(
    loop,
):
    alone = config({})
    assert caller_seen(loop, alone, "127.0.0.1") == "203.0.113.7"
    assert caller_seen(loop, alone, "198.51.100.9") == "198.51.100.9"
    behind = config({"FORWARDED_ALLOW_IPS": "10.0.0.0/8"})
    assert caller_seen(loop, behind, "10.1.2.3") == "203.0.113.7"
    assert caller_seen(loop, behind, "198.51.100.9") == "198.51.100.9"


@pytest.mark.id("tst_mek5d4")
def test_gives_open_requests_under_30_seconds_once_told_to_stop():
    seconds = config({}).timeout_graceful_shutdown
    assert seconds is not None
    assert 0 < seconds < 30


@pytest.mark.id("tst_xg3494")
def test_leaves_the_logs_to_the_desk():
    records = Records()
    logging.getLogger().addHandler(records)
    config({})
    logging.getLogger("uvicorn.error").warning("Shutting down")
    logging.getLogger("uvicorn.access").warning("GET / 200")
    assert [record.getMessage() for record in records.records] == ["Shutting down"]


@pytest.mark.id("tst_8pcxkd")
def test_answers_ready_and_gives_each_request_an_id(loop):
    app = FastAPI()

    @app.get("/health")
    def up():
        return {"status": "ok"}

    desk = production(app)
    desk.state.pool = Pool()

    async def calls():
        desk.state.client = loaded_model()
        transport = ASGITransport(app=desk)
        async with AsyncClient(transport=transport, base_url="http://desk") as client:
            return await client.get("/ready"), await client.get("/health")

    ready, alive = loop.run_until_complete(calls())
    assert ready.status_code == 200
    assert ready.json() == {"checks": {"database": "ok", "model": "ok"}}
    assert alive.json() == {"status": "ok"}
    assert ready.headers["x-request-id"] != alive.headers["x-request-id"]
