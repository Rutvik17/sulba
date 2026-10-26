import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta, timezone

import pytest

from access import DOCUMENTS
from audit import entry, pseudonym
from staff import Staff

KEY = b"the office's audit key"
LINUS = Staff("user-linus", frozenset({"supervisors", "benefits"}))


@pytest.mark.id("tst_rt2wtr")
def test_the_line():
    """Writes when, the pseudonym, the groups and the documents found"""
    at = datetime(2026, 11, 2, 9, 30, 15, 250_000, tzinfo=UTC)
    line = entry(KEY, LINUS, [DOCUMENTS[2], DOCUMENTS[1]], at)
    who = hmac.new(KEY, b"user-linus", hashlib.sha256).hexdigest()[:16]
    assert json.loads(line) == {
        "at": "2026-11-02T09:30:15Z",
        "who": who,
        "groups": ["benefits", "supervisors"],
        "documents": ["d3", "d2"],
    }
    assert "\n" not in line


@pytest.mark.id("tst_zhv675")
def test_nothing_that_names_them():
    """Keeps the subject out of the line, under a pseudonym that's the same for the same key"""
    at = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)
    line = entry(KEY, LINUS, [], at)
    assert "linus" not in line
    assert pseudonym(KEY, "user-linus") == pseudonym(KEY, "user-linus")
    assert pseudonym(KEY, "user-linus") != pseudonym(b"another key", "user-linus")
    assert pseudonym(KEY, "user-linus") != pseudonym(KEY, "user-grace")
    assert len(pseudonym(KEY, "user-linus")) == 16


@pytest.mark.id("tst_w1pcgd")
def test_times_in_utc():
    """Writes the time in UTC, and refuses a time that doesn't know its zone"""
    eastern = timezone(timedelta(hours=-5))
    at = datetime(2026, 11, 2, 23, 45, tzinfo=eastern)
    assert json.loads(entry(KEY, LINUS, [], at))["at"] == "2026-11-03T04:45:00Z"
    with pytest.raises(ValueError):
        entry(KEY, LINUS, [], datetime(2026, 11, 2, 9, 30))
