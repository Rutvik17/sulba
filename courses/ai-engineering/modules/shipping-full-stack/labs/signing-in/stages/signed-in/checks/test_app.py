import json
from urllib.parse import parse_qsl, urlsplit

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app import Settings, create_app, settings_from


def settings(database, identity, public_url="https://desk.test"):
    return Settings(
        model_url="http://127.0.0.1:9931/v1",
        database_url=database,
        running=1,
        waiting=8,
        seconds=120,
        issuer=identity.issuer,
        client_id=identity.client_id,
        client_secret=identity.client_secret,
        public_url=public_url,
    )


def events(text):
    found = []
    for block in text.split("\n\n"):
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line
        )
        if "event" in fields:
            found.append((fields["event"], json.loads(fields["data"])))
    return found


def serving(loop, app, work):
    """Runs work(browser) against the app, between its start and its stop, with a browser
    that keeps the app's cookies."""

    async def go():
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="https://desk.test"
            ) as browser:
                return await work(browser)

    return loop.run_until_complete(go())


async def sign_in(browser, identity, name="ada"):
    started = await browser.get("/auth/sign-in")
    return await browser.get(identity.sign_in(started.headers["location"], name))


async def converse(browser, content="When do you open?"):
    """A new conversation with one message in it, and the reply."""
    started = (await browser.post("/conversations", json={})).json()["id"]
    reply = await browser.post(
        f"/conversations/{started}/messages", json={"content": content}
    )
    return started, reply


def made(database, identity, model):
    return create_app(
        settings(database, identity),
        client=model.async_client(timeout=300),
        identity=identity.async_client(),
    )


ENVIRONMENT = {
    "DESK_DATABASE_URL": "postgresql://desk:secret@db:5432/desk",
    "DESK_ISSUER": "https://accounts.example.com",
    "DESK_CLIENT_ID": "desk",
    "DESK_CLIENT_SECRET": "a-long-secret",
}


def refused(environ):
    with pytest.raises(ValueError) as error:
        settings_from(environ)
    return str(error.value)


@pytest.mark.id("tst_s2x61a")
def test_the_secret_stays_out_of_sight(loop, database, identity):
    """The provider's settings have no defaults, the issuer is served over HTTPS and the
    public address has no path, and the secret shows in neither the settings' repr nor their
    JSON"""
    for variable in ("DESK_ISSUER", "DESK_CLIENT_ID", "DESK_CLIENT_SECRET"):
        without = {k: v for k, v in ENVIRONMENT.items() if k != variable}
        assert variable in refused(without)
    assert "DESK_ISSUER" in refused(ENVIRONMENT | {"DESK_ISSUER": "http://id.test"})
    for address in ("https://desk.test/app", "desk.test", "https://desk.test/"):
        assert "DESK_PUBLIC_URL" in refused(ENVIRONMENT | {"DESK_PUBLIC_URL": address})
    chosen = settings_from(ENVIRONMENT)
    for shown in (repr(chosen), str(chosen), chosen.model_dump_json()):
        assert "a-long-secret" not in shown


@pytest.mark.id("tst_sn1dev")
def test_cookies_only_over_https(loop, database, identity, model):
    """Served over HTTPS, the desk's cookies are Secure, and the provider sends the browser
    back to the public address's /auth/callback"""
    app = made(database, identity, model)

    async def work(browser):
        started = await browser.get("/auth/sign-in")
        back = await browser.get(identity.sign_in(started.headers["location"]))
        return started, back

    started, back = serving(loop, app, work)
    request = dict(parse_qsl(urlsplit(started.headers["location"]).query))
    assert request["redirect_uri"] == "https://desk.test/auth/callback"
    for response in (started, back):
        assert "Secure" in response.headers["set-cookie"]
        assert "HttpOnly" in response.headers["set-cookie"]


@pytest.mark.id("tst_r57jgx")
def test_no_changes_from_other_sites(loop, database, identity, model):
    """A request that would change something is refused with 403 when the browser says it
    comes from another site, by Sec-Fetch-Site or, without it, by Origin; one from the
    desk's own pages, or from a program that isn't a browser, goes through"""
    app = made(database, identity, model)
    elsewhere = [
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "same-site"},
        {"Sec-Fetch-Site": "none"},
        {"Origin": "https://elsewhere.test"},
        {"Origin": "null"},
    ]
    here = [
        {"Sec-Fetch-Site": "same-origin", "Origin": "https://desk.test"},
        {"Origin": "https://desk.test"},
        {},
    ]

    async def work(browser):
        await sign_in(browser, identity)
        blocked = [
            (await browser.post("/conversations", json={}, headers=each)).status_code
            for each in elsewhere
        ]
        out = await browser.post("/auth/sign-out", headers=elsewhere[0])
        allowed = [
            (await browser.post("/conversations", json={}, headers=each)).status_code
            for each in here
        ]
        read = await browser.get("/conversations", headers=elsewhere[0])
        return blocked, out, allowed, read, (await browser.get("/me")).status_code

    blocked, out, allowed, read, me = serving(loop, app, work)
    assert blocked == [403] * 5
    assert out.status_code == 403
    assert allowed == [201, 201, 201]
    assert read.status_code == 200
    assert me == 200


@pytest.mark.id("tst_bcigbm")
def test_each_persons_own(loop, database, identity, model):
    """Each person lists, reads, replies in and counts the usage of their own conversations
    alone: someone else's is 404"""
    model.says("We open at 9.", usage=(700, 30))
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "ada")
        started, _ = await converse(browser)
        browser.cookies.clear()
        await sign_in(browser, identity, "grace")
        return (
            (await browser.get("/conversations")).json(),
            (await browser.get(f"/conversations/{started}")).status_code,
            (
                await browser.post(
                    f"/conversations/{started}/messages", json={"content": "Hi"}
                )
            ).status_code,
            (await browser.get("/usage")).json(),
        )

    listed, read, said, usage = serving(loop, app, work)
    assert listed == []
    assert (read, said) == (404, 404)
    assert usage == []


@pytest.mark.id("tst_0d1mqw")
def test_the_app_needs_its_provider(loop, database, identity, model):
    """The app doesn't start when the provider's discovery document can't be read"""
    failing = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )
    app = create_app(
        settings(database, identity),
        client=model.async_client(timeout=300),
        identity=failing,
    )

    async def start():
        async with app.router.lifespan_context(app):
            pass

    with pytest.raises(Exception, match="discovery document"):
        loop.run_until_complete(start())
