import hashlib
import http.server
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pytest

from sulba_fixtures import fetched_package

PACKAGE = bytes(range(256)) * 80


@dataclass
class Publisher:
    """A publisher's server for PACKAGE: the package it sends, whether it sends part of it when
    asked to, how many bytes it sends before it stops early, in how many answers, and each
    request's Range."""

    address: str = ""
    package: bytes = PACKAGE
    ranges: bool = True
    stops: int | None = None
    stopping: int = 1000
    requests: list[str | None] = field(default_factory=list)


@pytest.fixture
def publisher() -> Iterator[Publisher]:
    served = Publisher()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            asked = self.headers.get("Range")
            served.requests.append(asked)
            if self.path != "/package":
                self.send_error(404)
                return
            body = served.package
            part = bool(asked) and served.ranges
            start = int(asked.removeprefix("bytes=").removesuffix("-")) if asked and part else 0
            self.send_response(206 if part else 200)
            if part:
                self.send_header("Content-Range", f"bytes {start}-{len(body) - 1}/{len(body)}")
            self.send_header("Content-Length", str(len(body) - start))
            self.end_headers()
            stops = served.stops if len(served.requests) <= served.stopping else None
            end = len(body) if stops is None else start + stops
            self.wfile.write(body[start:end])

        def log_message(self, *args: Any) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    served.address = f"http://127.0.0.1:{server.server_port}"
    yield served
    server.shutdown()
    server.server_close()


def fetch(publisher: Publisher, path: str = "/package") -> bytes:
    sha256 = hashlib.sha256(PACKAGE).hexdigest()
    return fetched_package(f"{publisher.address}{path}", len(PACKAGE), sha256, "Go")


def test_a_package_is_fetched_once(publisher: Publisher) -> None:
    assert fetch(publisher) == PACKAGE
    assert publisher.requests == [None]


def test_a_package_the_publisher_stops_sending_early_is_asked_for_again_from_where_it_stopped(
    publisher: Publisher,
) -> None:
    publisher.stops = 8000
    assert fetch(publisher) == PACKAGE
    assert publisher.requests == [None, "bytes=8000-", "bytes=16000-"]


def test_a_publisher_that_sends_all_of_a_package_asked_for_in_part_is_heard(
    publisher: Publisher,
) -> None:
    publisher.stops = 8000
    publisher.stopping = 1
    publisher.ranges = False
    assert fetch(publisher) == PACKAGE
    assert publisher.requests == [None, "bytes=8000-"]


def test_a_publisher_that_keeps_stopping_is_asked_five_times(publisher: Publisher) -> None:
    publisher.stops = 1000
    with pytest.raises(RuntimeError, match="stopped sending Go after 5000 of 20480 bytes"):
        fetch(publisher)
    assert len(publisher.requests) == 5


def test_a_package_of_another_size_is_refused_at_once(publisher: Publisher) -> None:
    publisher.package = PACKAGE[:100]
    with pytest.raises(RuntimeError, match="sent a different Go from the one the lab was made"):
        fetch(publisher)
    assert publisher.requests == [None]


def test_a_package_other_than_the_pinned_one_is_refused(publisher: Publisher) -> None:
    publisher.package = bytes(len(PACKAGE))
    with pytest.raises(RuntimeError, match="sent a different Go from the one the lab was made"):
        fetch(publisher)
    assert publisher.requests == [None]


def test_a_package_the_publisher_does_not_have_is_asked_for_once(publisher: Publisher) -> None:
    with pytest.raises(RuntimeError, match="which didn't send it: HTTP Error 404"):
        fetch(publisher, "/gone")
    assert publisher.requests == [None]
