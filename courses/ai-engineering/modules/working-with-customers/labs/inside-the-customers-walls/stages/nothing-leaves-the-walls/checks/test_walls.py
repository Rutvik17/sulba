import httpx
import pytest

from walls import NotAllowed, Walled


def office(redirect_to=None):
    """A stand-in for the office's services, and the addresses it was sent."""
    received = []

    def answer(request):
        received.append(str(request.url))
        if redirect_to and request.url.path == "/moved":
            return httpx.Response(302, headers={"Location": redirect_to})
        return httpx.Response(200)

    return httpx.MockTransport(answer), received


def refused(loop, url, allowed, **options):
    inner, received = office(**options)
    client = httpx.AsyncClient(transport=Walled(inner, allowed), follow_redirects=True)
    with pytest.raises(NotAllowed):
        loop.run_until_complete(client.get(url))
    return received


@pytest.mark.id("tst_smfzre")
def test_hosts_by_name_exactly(loop):
    """Allows a host by its whole name, not by a part of it"""
    for url in [
        "https://evil-model.office.test/v1",
        "https://model.office.test.evil.test/v1",
        "https://office.test/v1",
        "https://model.office.testing/v1",
        "https://www.model.office.test/v1",
    ]:
        assert refused(loop, url, ["model.office.test"]) == []


@pytest.mark.id("tst_dome93")
def test_any_case(loop):
    """Matches host names in any case, in the request and in the list"""
    inner, received = office()
    client = httpx.AsyncClient(transport=Walled(inner, ["Model.Office.TEST"]))
    response = loop.run_until_complete(
        client.get("https://MODEL.office.test/v1/models")
    )
    assert response.status_code == 200 and len(received) == 1


@pytest.mark.id("tst_x1he5r")
def test_addresses_in_disguise(loop):
    """Refuses a redirect out, a host after a user name, and an address by number"""
    received = refused(
        loop,
        "https://model.office.test/moved",
        ["model.office.test"],
        redirect_to="https://evil.test/collect",
    )
    assert received == ["https://model.office.test/moved"]
    for url in [
        "https://model.office.test@evil.test/v1",
        "http://10.0.0.5/v1",
        "http://[::1]:9931/v1",
        "http://2130706433/v1",
    ]:
        assert refused(loop, url, ["model.office.test"]) == []


@pytest.mark.id("tst_48jj0u")
def test_an_error_clients_already_handle(loop):
    """Raises an httpx.TransportError, which code that handles httpx's errors catches"""
    inner, _ = office()
    client = httpx.AsyncClient(transport=Walled(inner, []))
    with pytest.raises(httpx.TransportError):
        loop.run_until_complete(client.get("https://model.office.test/v1"))
