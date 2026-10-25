import psycopg
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg_pool import ConnectionPool

from conversations import install
from desk_auth import Registration, router
from migrations import MIGRATIONS, migrate
from sessions import (
    SESSION_COOKIE,
    SESSION_MIGRATIONS,
    SIGN_IN_COOKIE,
    Account,
    Sessions,
    signed_in,
)
from sign_in import discover
from store import OWNERS
from tokens import Keys


@pytest.fixture
def app(loop, database, identity):
    with psycopg.connect(database, autocommit=True) as conn:
        migrate(conn, [*MIGRATIONS, *SESSION_MIGRATIONS, OWNERS])
    client = identity.async_client()
    provider = loop.run_until_complete(discover(client, identity.issuer))
    with ConnectionPool(database, kwargs={"autocommit": True}) as pool:
        app = FastAPI()
        install(app)
        app.include_router(router)
        app.state.pool = pool
        app.state.sessions = Sessions(pool)
        app.state.provider = provider
        app.state.keys = Keys(client, provider)
        app.state.registration = Registration(
            identity.client_id, identity.client_secret, identity.redirect_uri, True
        )

        @app.get("/me")
        def me(person: Account = Depends(signed_in)) -> Account:
            return person

        yield app


def browsing(loop, app, work):
    """Runs work(browser) with a browser at the desk, which keeps the desk's cookies."""

    async def go():
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="https://desk.test"
        ) as browser:
            return await work(browser)

    return loop.run_until_complete(go())


async def sign_in(browser, identity, name="ada", back="/"):
    """Signs the person in as a browser does, and gives the desk's last answer."""
    started = await browser.get("/auth/sign-in", params={"back": back})
    assert started.status_code == 303
    return await browser.get(identity.sign_in(started.headers["location"], name))


@pytest.mark.id("tst_7btbqr")
def test_signing_in_sends_the_browser_to_the_provider(loop, app, identity):
    """Signing in redirects to the provider, with the sign-in kept in a cookie for /auth"""

    async def work(browser):
        return await browser.get("/auth/sign-in")

    started = browsing(loop, app, work)
    assert started.status_code == 303
    assert started.headers["location"].startswith("https://id.test/authorize?")
    cookie = started.headers["set-cookie"]
    assert cookie.startswith(f"{SIGN_IN_COOKIE}=")
    for attribute in (
        "HttpOnly",
        "Secure",
        "SameSite=lax",
        "Path=/auth",
        "Max-Age=600",
    ):
        assert attribute in cookie


@pytest.mark.id("tst_j5nu0r")
def test_a_person_signs_in(loop, app, identity):
    """The provider's answer signs the person in, and sends them back where they started"""

    async def work(browser):
        back = await sign_in(browser, identity, "grace", "/conversations")
        return back, await browser.get("/me")

    back, me = browsing(loop, app, work)
    assert back.status_code == 303
    assert back.headers["location"] == "/conversations"
    assert SESSION_COOKIE in back.headers["set-cookie"]
    assert "HttpOnly" in back.headers["set-cookie"]
    assert me.json()["email"] == "grace@example.com"


@pytest.mark.id("tst_6id08h")
def test_a_sign_in_that_wasnt_started_is_refused(loop, app, identity):
    """An answer that comes back to a browser without its sign-in cookie is refused"""

    async def work(browser):
        started = await browser.get("/auth/sign-in")
        back = identity.sign_in(started.headers["location"])
        browser.cookies.clear()
        refused = await browser.get(back)
        return refused, await browser.get("/me")

    refused, me = browsing(loop, app, work)
    assert refused.status_code == 400
    assert me.status_code == 403


@pytest.mark.id("tst_u4o0jq")
def test_a_person_who_declines_isnt_signed_in(loop, app, identity):
    """A person who declines at the provider comes back to a 400, and isn't signed in"""

    async def work(browser):
        started = await browser.get("/auth/sign-in")
        refused = await browser.get(identity.declines(started.headers["location"]))
        return refused, await browser.get("/me")

    refused, me = browsing(loop, app, work)
    assert refused.status_code == 400
    assert me.status_code == 403


@pytest.mark.id("tst_8emcri")
def test_signing_out(loop, app, identity):
    """Signing out answers 204, and the browser is signed out"""

    async def work(browser):
        await sign_in(browser, identity)
        out = await browser.post("/auth/sign-out")
        return out, await browser.get("/me")

    out, me = browsing(loop, app, work)
    assert out.status_code == 204
    assert me.status_code == 403
