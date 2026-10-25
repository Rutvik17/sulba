import asyncio
import json
import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from logs import JsonFormatter, RequestIds, configure, redacted, request_id


class Lines(logging.Handler):
    """Keeps each of the desk's records as the line the desk's formatter writes."""

    def __init__(self):
        super().__init__()
        self.setFormatter(JsonFormatter())
        self.addFilter(lambda record: record.name.startswith("desk"))
        self.lines = []

    def emit(self, record):
        self.lines.append(self.format(record))

    def entries(self):
        return [json.loads(line) for line in self.lines]


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


def desk():
    app = FastAPI()
    log = logging.getLogger("desk.test")

    @app.get("/hello")
    async def hello(name: str = "Ada"):
        log.info("greeted", extra={"greeted": name})
        await asyncio.sleep(0.25)
        log.info("done")
        return {"hello": name}

    @app.get("/fail")
    async def fail():
        raise RuntimeError("The model is down.")

    return RequestIds(app)


def call(loop, app, *requests):
    """Sends the requests at once, and gives the answers."""

    async def go():
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(
            transport=transport, base_url="http://desk.test"
        ) as client:
            return await asyncio.gather(
                *(client.get(path, headers=headers) for path, headers in requests)
            )

    return loop.run_until_complete(go())


@pytest.mark.id("tst_kkoh9v")
def test_a_record_is_one_line_of_json_with_its_extra_fields(lines):
    logging.getLogger("desk.store").warning(
        "slow query %s", "usage", extra={"ms": 812.5, "rows": 3}
    )
    [line] = lines.lines
    assert "\n" not in line
    entry = json.loads(line)
    assert entry["time"].endswith("+00:00")
    assert {
        key: entry[key] for key in ("level", "logger", "message", "ms", "rows")
    } == {
        "level": "WARNING",
        "logger": "desk.store",
        "message": "slow query usage",
        "ms": 812.5,
        "rows": 3,
    }
    assert "request_id" not in entry


@pytest.mark.id("tst_hlcct4")
def test_an_errors_traceback_stays_on_the_records_one_line(lines):
    try:
        raise ValueError("DESK_SECONDS should be a number.")
    except ValueError:
        logging.getLogger("desk").exception("These settings don't fit.")
    [line] = lines.lines
    assert "\n" not in line
    error = json.loads(line)["error"]
    assert error.startswith("Traceback") and "ValueError: DESK_SECONDS" in error


@pytest.mark.id("tst_kqmnjy")
def test_fields_named_for_secrets_are_hidden_at_any_depth(lines):
    headers = {"Authorization": "Bearer abc", "Accept": "text/html"}
    settings = {
        "client_secret": "s3cret",
        "database_url": "postgresql://x",
        "ids": [1, 2],
    }
    logging.getLogger("desk").info(
        "started",
        extra={"headers": headers, "settings": settings, "session_token": "t"},
    )
    entry = lines.entries()[0]
    assert entry["headers"] == {"Authorization": "[hidden]", "Accept": "text/html"}
    assert entry["settings"]["client_secret"] == "[hidden]"
    assert entry["settings"]["database_url"] == "[hidden]"
    assert entry["settings"]["ids"] == [1, 2]
    assert entry["session_token"] == "[hidden]"
    assert redacted({"Cookie": "a=b", "rows": [{"password": "p"}]}) == {
        "Cookie": "[hidden]",
        "rows": [{"password": "[hidden]"}],
    }


@pytest.mark.id("tst_h5ysgb")
def test_each_request_keeps_the_callers_id_and_sends_it_back(loop, lines):
    [answer] = call(loop, desk(), ("/hello", {"X-Request-ID": "req-7f3a.2"}))
    assert answer.headers["x-request-id"] == "req-7f3a.2"
    ids = {entry["request_id"] for entry in lines.entries()}
    assert ids == {"req-7f3a.2"}
    assert request_id.get() is None


@pytest.mark.id("tst_5kw105")
def test_a_request_without_a_fit_id_gets_a_new_one(loop, lines):
    unfit = ["", "x" * 65, "two words", "a\nb", "ünïcode"]
    answers = call(
        loop,
        desk(),
        *(("/hello", {"X-Request-ID": each} if each else {}) for each in unfit[:1]),
        *(("/hello", {"X-Request-ID": each.encode("utf-8")}) for each in unfit[1:]),
    )
    given = [answer.headers["x-request-id"] for answer in answers]
    assert len(set(given)) == len(unfit)
    for each in given:
        assert each not in unfit and 1 <= len(each) <= 64 and each.isalnum()


@pytest.mark.id("tst_13k10e")
def test_requests_answered_at_once_log_their_own_ids(loop, lines):
    call(
        loop,
        desk(),
        ("/hello?name=Ada", {"X-Request-ID": "one"}),
        ("/hello?name=Grace", {"X-Request-ID": "two"}),
    )
    greeted = {
        entry["greeted"]: entry["request_id"]
        for entry in lines.entries()
        if entry["message"] == "greeted"
    }
    assert greeted == {"Ada": "one", "Grace": "two"}


@pytest.mark.id("tst_4w0xgx")
def test_each_request_logs_one_line_of_its_method_path_status_and_time(loop, lines):
    call(loop, desk(), ("/hello?token=abc123", {"X-Request-ID": "one"}))
    [entry] = [each for each in lines.entries() if each["logger"] == "desk.requests"]
    assert {key: entry[key] for key in ("message", "method", "path", "status")} == {
        "message": "request",
        "method": "GET",
        "path": "/hello",
        "status": 200,
    }
    assert entry["request_id"] == "one"
    assert isinstance(entry["ms"], float | int) and entry["ms"] >= 0
    assert "abc123" not in "".join(lines.lines)


@pytest.mark.id("tst_8bv5oc")
def test_a_request_that_fails_is_logged_as_a_500(loop, lines):
    [answer] = call(loop, desk(), ("/fail", {}))
    assert answer.status_code == 500
    [entry] = [each for each in lines.entries() if each["logger"] == "desk.requests"]
    assert entry["status"] == 500 and entry["path"] == "/fail"


@pytest.mark.id("tst_i4dcfx")
def test_configure_sends_every_record_to_standard_output_as_json(capsys):
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    try:
        configure()
        logging.getLogger("desk").info("ready", extra={"port": 8000})
        logging.getLogger("desk").debug("not shown")
    finally:
        root.handlers[:], root.level = handlers, level
    [line] = capsys.readouterr().out.splitlines()
    assert json.loads(line)["port"] == 8000
