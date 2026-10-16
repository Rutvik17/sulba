import pytest
from httpx import ASGITransport, AsyncClient
from service import app


def send(loop, method, path, **options):
    """The app's response to one request, sent in process."""

    async def request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, path, **options)

    return loop.run_until_complete(request())


@pytest.mark.id("tst_fast01")
def test_health(loop):
    """Answers a GET"""
    response = send(loop, "GET", "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.id("tst_fast02")
def test_score(loop):
    """Reads a JSON body into its model"""
    response = send(loop, "POST", "/score", json={"days": 3, "visits": 2})
    assert response.json() == {"score": 7}


@pytest.mark.id("tst_fast03")
def test_invalid(loop):
    """Refuses a body out of range, and says where"""
    response = send(loop, "POST", "/score", json={"days": 30, "visits": 2})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "days"]


@pytest.mark.id("tst_fast04")
def test_def_endpoint(loop):
    """Runs a def endpoint and its dependency"""
    response = send(loop, "POST", "/weighted", json={"days": 3, "visits": 2})
    assert response.json() == {"score": 7}


@pytest.mark.id("tst_fast05")
def test_schema(loop):
    """Describes its endpoints in OpenAPI"""
    paths = send(loop, "GET", "/openapi.json").json()["paths"]
    assert sorted(paths) == ["/health", "/score", "/weighted"]
