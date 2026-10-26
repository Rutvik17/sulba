A transport sees every request a client sends, redirects included, after httpx has parsed its address. Checking there, rather than where the desk builds its addresses, covers every address the desk didn't write itself: one a model put in a reply, a link in a document, or a redirect a server answered with.

The host is compared whole, as httpx parsed it, so `model.office.test@evil.test` is a request to `evil.test`, with `model.office.test` as its user name, and `2130706433`, which some systems read as an address by number, is a name the office didn't list. Comparing the start or the end of the address instead lets a host through that only looks like the office's.

`NotAllowed` is an `httpx.TransportError`, the kind of error a network that can't be reached raises, so the desk's code that already handles one, such as code that hands a caller to a person when the model can't be reached, handles a refused request the same way.

```python
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
        self.inner = inner
        self.allowed = {host.lower() for host in allowed}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host.lower()
        if host not in self.allowed:
            raise NotAllowed(f"Requests to {host} aren't allowed.", request=request)
        return await self.inner.handle_async_request(request)

    async def aclose(self) -> None:
        await self.inner.aclose()
```

A transport is a guard in the desk's own code. The office's network can enforce the same rule for every program on the machine, with a firewall or a proxy that allows only its hosts, and should: a guard in code only covers the code that goes through it.
