import json
from datetime import UTC, datetime

import pytest

from audit import pseudonym
from sign_in import discover
from staff_search import search_for
from tokens import Keys

KEY = b"the office's audit key"
AT = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)


def search(identity, loop, name, question, log, **options):
    client = identity.async_client()
    keys = Keys(client, loop.run_until_complete(discover(client, identity.issuer)))
    token = identity.id_token(name)
    found = search_for(
        keys,
        token,
        question,
        client_id=identity.client_id,
        key=KEY,
        log=log,
        at=AT,
        **options,
    )
    return [document.id for document in loop.run_until_complete(found)]


@pytest.mark.id("tst_ad2zvf")
def test_a_supervisors_search(identity, loop):
    """Finds the repayment documents for a supervisor"""
    identity.person("linus", email="linus@example.com", groups=["managers"])
    question = "Can I agree a repayment plan for an overpayment?"
    assert search(identity, loop, "linus", question, []) == ["d2", "d3"]


@pytest.mark.id("tst_1mnvdm")
def test_a_line_for_each_search(identity, loop):
    """Adds a line to the log for each search, under the person's pseudonym"""
    identity.person("linus", email="linus@example.com", groups=["managers", "ssa-team"])
    log = []
    search(identity, loop, "linus", "How do I open a claim?", log)
    search(identity, loop, "linus", "Who agrees repayment plans?", log)
    assert len(log) == 2
    first = json.loads(log[0])
    assert first["who"] == pseudonym(KEY, "user-linus")
    assert first["groups"] == ["benefits", "supervisors"]
    assert first["at"] == "2026-11-02T09:30:00Z"


@pytest.mark.id("tst_xjeaz1")
def test_no_groups(identity, loop):
    """Finds nothing for someone in none of the office's groups"""
    assert search(identity, loop, "ada", "How do I open a benefits claim?", []) == []
