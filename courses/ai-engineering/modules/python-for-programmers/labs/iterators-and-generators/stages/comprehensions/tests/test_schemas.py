import pytest

from walk import assign, boolean, explain, number, omit, pick, string

PERSON = {"name": string, "age": number, "email": string}


@pytest.mark.id("tst_ulwmg3")
def test_pick():
    """Picks the fields named, in their order"""
    # As superstruct's fixtures in test/validation/pick do.
    assert pick(PERSON, ["name"]) == {"name": string}
    found = pick(PERSON, ["email", "name"])
    assert list(found) == ["email", "name"]
    assert found["email"] is string


@pytest.mark.id("tst_lmtsby")
def test_omit():
    """Omits the fields named, keeping the schema's order"""
    found = omit(PERSON, ["age"])
    assert found == {"name": string, "email": string}
    assert list(found) == ["name", "email"]
    assert omit(PERSON, ["height"]) == PERSON


@pytest.mark.id("tst_3chivw")
def test_assign():
    """Joins schemas, a later field winning"""
    found = assign({"id": number, "name": string}, {"name": boolean, "age": number})
    assert found == {"id": number, "name": boolean, "age": number}
    assert list(found) == ["id", "name", "age"]
    assert assign() == {}
    assert assign(PERSON) == PERSON


@pytest.mark.id("tst_k8diz6")
def test_new_schemas():
    """Leaves the schemas it's given as they were"""
    before = dict(PERSON)
    for found in [pick(PERSON, list(PERSON)), omit(PERSON, []), assign(PERSON)]:
        assert found is not PERSON
        found["extra"] = boolean
    assert before == PERSON


@pytest.mark.id("tst_xvx98g")
def test_explain():
    """Explains a failure as superstruct does"""
    message = "Expected a string, but received: False"
    assert explain(("emails", 1), message) == f"At path: emails.1 -- {message}"
    assert explain(("address", "street"), message) == (
        f"At path: address.street -- {message}"
    )
    assert explain((), message) == message
