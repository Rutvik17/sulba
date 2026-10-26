from dataclasses import dataclass

ROLE = "office_assistant"


@dataclass(frozen=True)
class Award:
    award: str
    offered: int
    accepted: int
    paid: int


@dataclass(frozen=True)
class Record:
    student: str
    fafsa: bool
    awards: list[Award]


def create(conn):
    """The tables students and awards, which ROLE reads only for the student named by the
    transaction's app.student."""
    raise NotImplementedError


def load(conn):
    """The office's students and awards, from office_records, into the tables."""
    raise NotImplementedError


def record(conn, student):
    """The student's record, read as ROLE with app.student set for one transaction, or None
    for a student the office doesn't have."""
    raise NotImplementedError


def lines(record):
    """The record as the office words it, a line for each award, dollars to the dollar."""
    raise NotImplementedError
