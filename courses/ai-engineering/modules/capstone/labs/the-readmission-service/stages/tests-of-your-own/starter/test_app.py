"""Tests of the readmission service, sent to it in process as the planners' system would."""

from httpx import ASGITransport, AsyncClient

import app
from features import INPUTS, stays
from train import load


def send(loop, method, path, body=None):
    """The service's response to one request, sent in process."""

    async def request():
        transport = ASGITransport(app=app.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=body)

    return loop.run_until_complete(request())


def test_health(loop):
    assert send(loop, "GET", "/health").json() == {"status": "ok"}
