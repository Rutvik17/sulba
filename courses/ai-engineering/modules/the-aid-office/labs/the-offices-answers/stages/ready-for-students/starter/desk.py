from dataclasses import dataclass

SIGN_IN = "Sign in to see your aid, so the office can tell which record is yours."
STAFF_SIGNED_OUT = "The office's staff can answer this. Sign in and ask again, so they can reply to you by email."
NO_RECORD = "The office has no record for you for 2026-27."


@dataclass(frozen=True)
class Reply:
    text: str
    pages: list[str]
    to_staff: bool


def create_tickets(conn):
    raise NotImplementedError


def respond(conn, client, student, question, about="pages"):
    """The reply to a question: the signed-in student's own aid, from their record, when it's
    about their aid, and the answer from the office's pages otherwise, with a ticket for the
    office's staff when the answer goes to them. student is None when no one is signed in."""
    raise NotImplementedError
