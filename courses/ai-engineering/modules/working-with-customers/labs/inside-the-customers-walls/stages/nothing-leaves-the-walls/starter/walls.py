"""The desk's requests kept inside the office's network: a transport that sends a request only
to a host the office allows, and refuses every other before it leaves."""

from collections.abc import Iterable

import httpx

# The office's own services: its model server and its sign-in.
ALLOWED = ["model.office.test", "id.office.test"]


class NotAllowed(httpx.TransportError):
    """A request to a host the office doesn't allow, refused before it was sent."""


class Walled(httpx.AsyncBaseTransport):
    """A transport that passes a request to the one it wraps only when its host, in any case,
    is one of the allowed."""

    def __init__(
        self, inner: httpx.AsyncBaseTransport, allowed: Iterable[str] = ALLOWED
    ) -> None:
        raise NotImplementedError

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        raise NotImplementedError

    async def aclose(self) -> None:
        raise NotImplementedError
