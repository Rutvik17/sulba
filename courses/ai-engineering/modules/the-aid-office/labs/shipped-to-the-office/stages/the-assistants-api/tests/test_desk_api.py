import csv
import json

import numpy as np
import pytest
from desk_api import Settings, create_app, settings_from
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


@pytest.mark.id("tst_6w4t41")
def test_settings():
    """Takes its settings from the environment"""
    chosen = settings_from(
        {
            "OFFICE_DATABASE_URL": "postgresql://desk:secret@db:5432/office",
            "OFFICE_ISSUER": "https://sign-in.harbor.example",
            "OFFICE_CLIENT_ID": "desk",
            "OFFICE_CLIENT_SECRET": "a-long-secret",
        }
    )
    assert chosen.client_id == "desk"


@pytest.mark.id("tst_ct5miq")
def test_answer(loop, database, identity, model, office, asked):
    """Streams an answer from the office's pages to a student"""
    model.says("Renew it ", "each year [1].")
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "s1002")
        return await browser.post("/questions", json={"text": asked["q1"]})

    found = events(serving(loop, app, work).text)
    assert [name for name, _ in found] == ["piece", "piece", "verdict"]
    assert not found[-1][1]["to_staff"]


@pytest.mark.id("tst_z0izda")
def test_my_aid(loop, database, identity, model, office):
    """Gives a student their aid"""
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "s1002")
        return await browser.post(
            "/questions", json={"text": "My aid?", "about": "my aid"}
        )

    [(name, verdict)] = events(serving(loop, app, work).text)
    assert verdict["text"] == "\n".join(lines(record(office, "S1002")))
