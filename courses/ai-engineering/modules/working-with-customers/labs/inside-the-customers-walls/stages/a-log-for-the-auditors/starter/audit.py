"""The office's audit log: a line for each search, saying when, by whom under a pseudonym, in
which groups and what it found, with nothing that names the person or holds what they asked."""

from datetime import datetime

from access import Document
from staff import Staff


def pseudonym(key: bytes, subject: str) -> str:
    """The subject under the office's key: the first 16 hex digits of its HMAC-SHA256."""
    raise NotImplementedError


def entry(key: bytes, staff: Staff, found: list[Document], at: datetime) -> str:
    """The log's line, as JSON, for a search by the member of staff that found the documents
    at the time given, which must know its time zone."""
    raise NotImplementedError
