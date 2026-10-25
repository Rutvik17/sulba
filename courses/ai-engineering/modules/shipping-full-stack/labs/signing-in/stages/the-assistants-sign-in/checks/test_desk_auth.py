import psycopg
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from psycopg_pool import ConnectionPool

from conversations import install
from conversations import router as conversations_router
from desk_auth import Registration, router
from migrations import MIGRATIONS, migrate
from sessions import (
    SESSION_COOKIE,
    SESSION_MIGRATIONS,
    Account,
    Sessions,
    signed_in,
)
from sign_in import discover
from store import OWNERS, Store
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
        app.include_router(conversations_router)
        app.state.pool = pool
        app.state.conversations = Store(pool)
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


@pytest.mark.id("tst_tx9m41")
def test_back_stays_on_this_site(loop, app, identity):
    """A sign-in sends the person back to a path on this site, and anywhere else to /"""

    async def work(browser):
        found = []
        for back in (
            "https://elsewhere.test/sign-in",
            "//elsewhere.test",
            "/\\elsewhere.test",
            "/\t/elsewhere.test",
        ):
            browser.cookies.clear()
            found.append(
                (await sign_in(browser, identity, back=back)).headers["location"]
            )
        return found

    assert browsing(loop, app, work) == ["/", "/", "/", "/"]


@pytest.mark.id("tst_er3vgg")
def test_a_sign_in_gives_a_new_session(loop, app, identity):
    """Signing in gives the browser a session token it didn't have before, and a token set
    in the browser before then signs no one in"""

    async def work(browser):
        browser.cookies.set(
            SESSION_COOKIE, "a-token-someone-else-chose", domain="desk.test"
        )
        await sign_in(browser, identity)
        given = browser.cookies.get(SESSION_COOKIE)
        planted = await browser.get(
            "/me", headers={"Cookie": f"{SESSION_COOKIE}=a-token-someone-else-chose"}
        )
        return given, planted

    given, planted = browsing(loop, app, work)
    assert given != "a-token-someone-else-chose"
    assert planted.status_code == 403


@pytest.mark.id("tst_70pgsx")
def test_a_person_is_their_issuer_and_subject(loop, app, identity):
    """Someone else with the same email signs in to an account of their own, and doesn't
    find the other person's conversations"""
    identity.person("mallory", email="ada@example.com")

    async def work(browser):
        await sign_in(browser, identity, "ada")
        ada = (await browser.get("/me")).json()
        started = (await browser.post("/conversations", json={})).json()["id"]
        browser.cookies.clear()
        await sign_in(browser, identity, "mallory")
        mallory = (await browser.get("/me")).json()
        found = await browser.get(f"/conversations/{started}")
        return ada, mallory, found

    ada, mallory, found = browsing(loop, app, work)
    assert mallory["id"] != ada["id"]
    assert mallory["name"] == "Mallory"
    assert found.status_code == 404


@pytest.mark.id("tst_q7q07e")
def test_signing_out_ends_the_session(loop, app, identity):
    """After signing out, the session's token signs no one in, wherever it's sent from"""

    async def work(browser):
        await sign_in(browser, identity)
        token = browser.cookies.get(SESSION_COOKIE)
        await browser.post("/auth/sign-out")
        return await browser.get("/me", headers={"Cookie": f"{SESSION_COOKIE}={token}"})

    assert browsing(loop, app, work).status_code == 403
