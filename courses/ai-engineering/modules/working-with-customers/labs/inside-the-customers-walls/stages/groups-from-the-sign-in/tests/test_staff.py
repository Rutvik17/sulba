import pytest

from sign_in import SignInError, discover
from staff import Staff, staff_from
from tokens import Keys


def keys_of(identity, loop):
    client = identity.async_client()
    return Keys(client, loop.run_until_complete(discover(client, identity.issuer)))


@pytest.mark.id("tst_p36v4g")
def test_groups_from_the_directory(identity, loop):
    """Gives the office's groups for the directory's groups it knows, and leaves out the rest"""
    groups = ["ssa-team", "managers", "chess-club"]
    identity.person("linus", email="linus@example.com", groups=groups)
    keys = keys_of(identity, loop)
    token = identity.id_token("linus")
    staff = loop.run_until_complete(staff_from(keys, token, identity.client_id))
    assert staff == Staff("user-linus", frozenset({"benefits", "supervisors"}))


@pytest.mark.id("tst_8be4ed")
def test_no_groups(identity, loop):
    """Gives no groups for a token without the claim, or with one it can't read"""
    keys = keys_of(identity, loop)
    staff = loop.run_until_complete(
        staff_from(keys, identity.id_token(), identity.client_id)
    )
    assert staff == Staff("user-ada", frozenset())
    identity.person("mary", email="mary@example.com", groups="ssa-team")
    identity.person(
        "alan", email="alan@example.com", groups=[["va-team"], 7, "reception"]
    )
    for name, expected in [("mary", frozenset()), ("alan", frozenset({"front-desk"}))]:
        token = identity.id_token(name)
        found = loop.run_until_complete(staff_from(keys, token, identity.client_id))
        assert found.groups == expected


@pytest.mark.id("tst_025dcd")
def test_tokens_that_dont_check_out(identity, loop):
    """Refuses a token signed by a stranger, for another app, expired, or not a token"""
    identity.person("linus", email="linus@example.com", groups=["managers"])
    keys = keys_of(identity, loop)
    for token in [
        identity.id_token("linus", stranger=True),
        identity.id_token("linus", audience="another-app"),
        identity.id_token("linus", issuer="https://elsewhere.test"),
        identity.id_token("linus", lasts=-60),
        "not.a.token",
    ]:
        with pytest.raises(SignInError):
            loop.run_until_complete(staff_from(keys, token, identity.client_id))


@pytest.mark.id("tst_mcgdcf")
def test_a_new_key(identity, loop):
    """Takes a token signed with the provider's new key, after it rotates them"""
    keys = keys_of(identity, loop)
    loop.run_until_complete(staff_from(keys, identity.id_token(), identity.client_id))
    identity.rotate()
    staff = loop.run_until_complete(
        staff_from(keys, identity.id_token(), identity.client_id)
    )
    assert staff.subject == "user-ada"
