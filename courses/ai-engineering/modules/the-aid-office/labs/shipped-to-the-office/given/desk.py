from dataclasses import dataclass

from answers import answer
from records import lines, record

SIGN_IN = "Sign in to see your aid, so the office can tell which record is yours."
STAFF_SIGNED_OUT = "The office's staff can answer this. Sign in and ask again, so they can reply to you by email."
NO_RECORD = "The office has no record for you for 2026-27."


@dataclass(frozen=True)
class Reply:
    text: str
    pages: list[str]
    to_staff: bool


def create_tickets(conn):
    conn.execute(
        "CREATE TABLE tickets (id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY, "
        "student text NOT NULL, question text NOT NULL, asked timestamptz NOT NULL DEFAULT now())"
    )


def respond(conn, client, student, question, about="pages"):
    """The reply to a question: the signed-in student's own aid, from their record, when it's
    about their aid, and the answer from the office's pages otherwise, with a ticket for the
    office's staff when the answer goes to them. student is None when no one is signed in."""
    if about == "my aid":
        if student is None:
            return Reply(SIGN_IN, [], False)
        found = record(conn, student)
        if found is None:
            return Reply(NO_RECORD, [], False)
        return Reply("\n".join(lines(found)), [], False)
    answered = answer(conn, client, question)
    if not answered.to_staff:
        return Reply(answered.text, answered.pages, False)
    if student is None:
        return Reply(STAFF_SIGNED_OUT, [], True)
    conn.execute(
        "INSERT INTO tickets (student, question) VALUES (%s, %s)", (student, question)
    )
    return Reply(answered.text, [], True)
