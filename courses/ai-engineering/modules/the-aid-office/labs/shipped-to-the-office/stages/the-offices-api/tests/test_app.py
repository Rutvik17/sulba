import csv
import json

import numpy as np
import pytest
from app import NOT_A_STUDENT, Settings, create_app, settings_from
from desk import NO_RECORD, SIGN_IN, STAFF_SIGNED_OUT
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


@pytest.mark.id("tst_nwss95")
def test_settings_from_the_environment():
    """The database, the provider and the desk's id and secret come from their variables,
    and the rest have their defaults"""
    chosen = settings_from(
        {
            "OFFICE_DATABASE_URL": "postgresql://desk:secret@db:5432/office",
            "OFFICE_ISSUER": "https://sign-in.harbor.example",
            "OFFICE_CLIENT_ID": "desk",
            "OFFICE_CLIENT_SECRET": "a-long-secret",
        }
    )
    assert chosen.issuer == "https://sign-in.harbor.example"
    assert chosen.client_secret.get_secret_value() == "a-long-secret"
    assert chosen.model_url == "http://127.0.0.1:9931/v1"
    assert chosen.public_url == "http://127.0.0.1:8000"
    with pytest.raises(ValueError, match="OFFICE_DATABASE_URL"):
        settings_from({"OFFICE_ISSUER": "https://sign-in.harbor.example"})


@pytest.mark.id("tst_jd7mlt")
def test_answer_as_it_comes(loop, database, identity, model, office, asked):
    """Sends each piece, then the verdict with the pages the answer cites"""
    model.says("Renew it ", "each year [1].")
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "s1002")
        return await browser.post("/questions", json={"text": asked["q1"]})

    reply = serving(loop, app, work)
    assert reply.headers["content-type"].startswith("text/event-stream")
    found = events(reply.text)
    assert found[:2] == [
        ("piece", {"text": "Renew it "}),
        ("piece", {"text": "each year [1]."}),
    ]
    name, verdict = found[2]
    assert name == "verdict" and verdict["text"] == "Renew it each year [1]."
    assert len(verdict["pages"]) == 1 and not verdict["to_staff"]
    assert tickets(office) == []


@pytest.mark.id("tst_zyrm21")
def test_my_aid(loop, database, identity, model, office):
    """Gives a signed-in student their own aid, and asks a visitor to sign in"""
    app = made(database, identity, model)

    async def work(browser):
        visitor = await browser.post(
            "/questions", json={"text": "My aid?", "about": "my aid"}
        )
        await sign_in(browser, identity, "s1003")
        mine = await browser.post(
            "/questions", json={"text": "My aid?", "about": "my aid"}
        )
        return visitor, mine

    visitor, mine = serving(loop, app, work)
    assert events(visitor.text) == [
        ("verdict", {"text": SIGN_IN, "pages": [], "to_staff": False})
    ]
    text = (
        "\n".join(lines(record(office, "S1003")))
        if record(office, "S1003")
        else NO_RECORD
    )
    assert events(mine.text) == [
        ("verdict", {"text": text, "pages": [], "to_staff": False})
    ]


@pytest.mark.id("tst_8zejtc")
def test_staff(loop, database, identity, model, office, asked):
    """Writes a ticket for a student's question that goes to staff, and none for a visitor's"""
    app = made(database, identity, model)

    async def work(browser):
        visitor = await browser.post("/questions", json={"text": asked["o2"]})
        await sign_in(browser, identity, "s1002")
        student = await browser.post("/questions", json={"text": asked["o2"]})
        return visitor, student

    visitor, student = serving(loop, app, work)
    assert events(visitor.text)[-1] == (
        "verdict",
        {"text": STAFF_SIGNED_OUT, "pages": [], "to_staff": True},
    )
    assert events(student.text)[-1][1]["to_staff"]
    assert tickets(office) == [("S1002", asked["o2"])]


@pytest.mark.id("tst_ximjln")
def test_students_only(loop, database, identity, model, office):
    """Refuses someone the college signs in who isn't one of the office's students"""
    app = made(database, identity, model)

    async def work(browser):
        await sign_in(browser, identity, "ada")
        return await browser.post(
            "/questions", json={"text": "My aid?", "about": "my aid"}
        )

    refused = serving(loop, app, work)
    assert refused.status_code == 403
    assert refused.json()["detail"] == NOT_A_STUDENT


@pytest.mark.id("tst_tcj94y")
def test_refused(loop, database, identity, model, office):
    """Refuses an empty or long question, another subject, and a question from another site"""
    app = made(database, identity, model)

    async def work(browser):
        bodies = [
            {"text": "   "},
            {"text": "a" * 1001},
            {"text": "Hi", "about": "fees"},
        ]
        statuses = [
            (await browser.post("/questions", json=body)).status_code for body in bodies
        ]
        elsewhere = await browser.post(
            "/questions", json={"text": "Hi"}, headers={"Sec-Fetch-Site": "cross-site"}
        )
        return statuses, elsewhere.status_code

    assert serving(loop, app, work) == ([422, 422, 422], 403)
