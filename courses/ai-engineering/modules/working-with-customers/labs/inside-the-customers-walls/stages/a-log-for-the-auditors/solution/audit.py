"""The office's audit log: a line for each search, saying when, by whom under a pseudonym, in
which groups and what it found, with nothing that names the person or holds what they asked."""

import hashlib
import hmac
import json
from datetime import UTC, datetime

from access import Document
from staff import Staff


def pseudonym(key: bytes, subject: str) -> str:
    """The subject under the office's key: the first 16 hex digits of its HMAC-SHA256."""
    return hmac.new(key, subject.encode(), hashlib.sha256).hexdigest()[:16]


def entry(key: bytes, staff: Staff, found: list[Document], at: datetime) -> str:
    """The log's line, as JSON, for a search by the member of staff that found the documents
    at the time given, which must know its time zone."""
    if at.utcoffset() is None:
        raise ValueError("The time must know its time zone.")
    line = {
        "at": at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "who": pseudonym(key, staff.subject),
        "groups": sorted(staff.groups),
        "documents": [document.id for document in found],
    }
    return json.dumps(line, separators=(",", ":"))
