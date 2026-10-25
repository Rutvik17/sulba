import json
from datetime import UTC, datetime

import jwt
import pytest

from access import DOCUMENTS, Document
from sign_in import SignInError, discover
from staff_search import search_for
from tokens import Keys

KEY = b"the office's audit key"
AT = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)


def search(identity, loop, token, question, log, **options):
    client = identity.async_client()
    keys = Keys(client, loop.run_until_complete(discover(client, identity.issuer)))
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


@pytest.mark.id("tst_a7vcol")
def test_a_token_that_doesnt_check_out(identity, loop):
    """Refuses a token signed by a stranger, or for another app, whatever groups it claims"""
    identity.person("mallory", email="mallory@example.com", groups=["managers"])
    for token in [
        identity.id_token("mallory", stranger=True),
        identity.id_token("mallory", audience="another-app"),
    ]:
        with pytest.raises((SignInError, jwt.InvalidTokenError)):
            search(identity, loop, token, "Who agrees repayment plans?", [])


@pytest.mark.id("tst_9bxo18")
def test_k_of_what_they_may_read(identity, loop):
    """Gives the k best of the documents the person may read"""
    documents = [
        Document(
            "x1",
            "Repayment plans",
            "agree overpayment plan",
            frozenset({"supervisors"}),
        ),
        Document("x2", "Repayment plans", "agree plan", frozenset({"supervisors"})),
        Document("x3", "Repayment letters", "plan", frozenset({"benefits"})),
        Document("x4", "Repayment", "letters", frozenset({"benefits"})),
    ]
    identity.person("mary", email="mary@example.com", groups=["ssa-team"])
    question = "Can I agree a repayment plan for an overpayment?"
    token = identity.id_token("mary")
    found = search(identity, loop, token, question, [], documents=documents, k=2)
    assert found == ["x3", "x4"]


@pytest.mark.id("tst_4jj5ia")
def test_a_document_for_no_one(identity, loop):
    """Never gives a document that names no group"""
    groups = ["ssa-team", "va-team", "reception", "managers"]
    identity.person("linus", email="linus@example.com", groups=groups)
    question = "Which service will callers choose in the new phone menu?"
    found = search(identity, loop, identity.id_token("linus"), question, [], k=10)
    assert "d8" not in found
    assert all(DOCUMENTS[int(name[1:]) - 1].groups for name in found)


@pytest.mark.id("tst_wehqwf")
def test_nothing_they_asked_in_the_log(identity, loop):
    """Keeps what the person asked out of the audit log"""
    identity.person("linus", email="linus@example.com", groups=["ssa-team"])
    log = []
    question = "My caller Jane Doe at 12 Elm Street wants to open a claim"
    search(identity, loop, identity.id_token("linus"), question, log)
    (line,) = log
    assert set(json.loads(line)) == {"at", "who", "groups", "documents"}
    assert "Elm" not in line and "Jane" not in line
