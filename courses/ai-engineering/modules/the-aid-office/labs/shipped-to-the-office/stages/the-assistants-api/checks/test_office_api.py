import csv
import json
import logging

import numpy as np
import pytest
from desk_api import Settings, create_app
from answers import STAFF
from httpx import ASGITransport, AsyncClient
from index import DOCUMENT, connect, read
from office import QUERY
from records import lines, record
from setup import setup

SCALE = 32767


def rows(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def vectors(path, name):
    return {
        row[name]: np.array(
            [int(row[f"e_{i}"]) for i in range(1, 769)], dtype=np.float32
        )
        / SCALE
        for row in rows(path)
    }


@pytest.fixture(scope="module")
def asked():
    """The office's questions and the other services', by id."""
    found = rows("data/questions.csv") + rows("data/other-questions.csv")
    return {row["question"]: row["text"] for row in found}


@pytest.fixture
def office(database, model, identity, asked):
    """The office's database, set up, and its students known to the college's provider."""
    by_passage = vectors("data/passage-vectors.csv", "passage")
    by_question = vectors("data/question-vectors.csv", "question")
    model.embeds(
        {
            **{DOCUMENT + p.text: by_passage[p.id] for p in read("data/passages.csv")},
            **{QUERY + text: by_question[name] for name, text in asked.items()},
        }
    )
    for name in ("s1002", "s1003"):
        identity.person(name, email=f"{name}@harbor.example")
    with connect(database) as conn:
        setup(conn, model.client())
        yield conn


def settings(database, identity):
    return Settings(
        model_url="http://127.0.0.1:9931/v1",
        database_url=database,
        issuer=identity.issuer,
        client_id=identity.client_id,
        client_secret=identity.client_secret,
        public_url="https://desk.test",
    )


def made(database, identity, model):
    return create_app(
        settings(database, identity),
        client=model.client(),
        identity=identity.async_client(),
    )


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


async def sign_in(browser, identity, name):
    started = await browser.get("/auth/sign-in")
    return await browser.get(identity.sign_in(started.headers["location"], name))


def events(text):
    found = []
    for block in text.split("\n\n"):
        fields = dict(
            line.split(": ", 1) for line in block.splitlines() if ": " in line
        )
        if "event" in fields:
            found.append((fields["event"], json.loads(fields["data"])))
    return found


def tickets(conn):
    return conn.execute("SELECT student, question FROM tickets ORDER BY id").fetchall()


@pytest.mark.id("tst_79reaf")
def test_own_aid(loop, database, identity, model, office):
    """A student's own aid, whatever the address names"""
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "s1002")
        return await browser.post(
            "/questions?student=S1003", json={"text": "My aid?", "about": "my aid"}
        )

    [(name, verdict)] = events(serving(loop, app, work).text)
    assert verdict["text"] == "\n".join(lines(record(office, "S1002")))


@pytest.mark.id("tst_eq34gc")
def test_visitor(loop, database, identity, model, office, asked):
    """A visitor's question for staff answered, with no ticket"""
    app = made(database, identity, model)

    async def work(browser):
        return await browser.post("/questions", json={"text": asked["o2"]})

    assert serving(loop, app, work).status_code == 200
    assert tickets(office) == []


@pytest.mark.id("tst_omxklv")
def test_quiet_log(loop, database, identity, model, office, asked, caplog):
    """No question or student in the log"""
    caplog.set_level(logging.INFO)
    model.says("Renew it each year [1].")
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "s1002")
        return await browser.post("/questions", json={"text": asked["q1"]})

    serving(loop, app, work)
    kept = " ".join(each.getMessage() for each in caplog.records)
    assert asked["q1"] not in kept and "S1002" not in kept


@pytest.mark.id("tst_qlhg0r")
def test_staff_verdict(loop, database, identity, model, office, asked):
    """An answer that cites nothing ends with the verdict that takes its place"""
    model.says("You can renew it ", "online.")
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "s1002")
        return await browser.post("/questions", json={"text": asked["q1"]})

    found = events(serving(loop, app, work).text)
    assert found[-1] == ("verdict", {"text": STAFF, "pages": [], "to_staff": True})
