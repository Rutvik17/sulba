import httpx
import pytest

from walls import NotAllowed, Walled


def office():
    """A stand-in for the office's services that answers every request, and what it got."""
    received = []

    def answer(request):
        received.append(str(request.url))
        return httpx.Response(200, json={"host": request.url.host})

    return httpx.MockTransport(answer), received


@pytest.mark.id("tst_sgbgyt")
def test_the_offices_hosts(loop):
    """Passes requests to the office's hosts on"""
    inner, received = office()

    async def run():
        async with httpx.AsyncClient(transport=Walled(inner)) as client:
            model = await client.get("https://model.office.test/v1/models")
            sign_in = await client.get(
                "https://id.office.test/.well-known/openid-configuration"
            )
        return model, sign_in

    model, sign_in = loop.run_until_complete(run())
    assert model.json() == {"host": "model.office.test"} and sign_in.status_code == 200
    assert len(received) == 2


@pytest.mark.id("tst_ietp8m")
def test_another_host(loop):
    """Refuses a request to a host the office doesn't allow"""
    inner, received = office()
    client = httpx.AsyncClient(transport=Walled(inner, ["model.office.test"]))
    with pytest.raises(NotAllowed):
        loop.run_until_complete(client.get("https://id.office.test/keys"))
    assert received == []
