import base64
import json
from urllib.parse import parse_qsl, urlsplit

import pytest

from sign_in import Pending, SignInError, authorization_url, discover
from tokens import Keys, Person, person_from


class Desk:
    """The desk signing people in at the scripted provider, as the browser and the app."""

    def __init__(self, loop, identity):
        self.loop = loop
        self.identity = identity
        self.client = identity.async_client()
        provider = loop.run_until_complete(discover(self.client, identity.issuer))
        self.keys = Keys(self.client, provider)

    def start(self, name="ada"):
        """A new sign-in, and the provider's answer once the person signs in."""
        pending = Pending.new()
        url = authorization_url(
            self.keys.provider,
            self.identity.client_id,
            self.identity.redirect_uri,
            pending,
        )
        back = self.identity.sign_in(url, name)
        return pending, dict(parse_qsl(urlsplit(back).query))

    def finish(self, pending, answer):
        return self.loop.run_until_complete(
            person_from(
                self.client,
                self.keys,
                client_id=self.identity.client_id,
                client_secret=self.identity.client_secret,
                redirect_uri=self.identity.redirect_uri,
                pending=pending,
                answer=answer,
            )
        )

    def sign_in(self, name="ada"):
        return self.finish(*self.start(name))

    def requests(self, path):
        return [each for each in self.identity.requests if each.path == path]


@pytest.mark.id("tst_cno919")
def test_a_person_signs_in(loop, identity):
    """The person the provider signs in comes back, named by its issuer and their subject"""
    desk = Desk(loop, identity)
    assert desk.sign_in("grace") == Person(
        issuer="https://id.test",
        subject="user-grace",
        email="grace@example.com",
        name="Grace",
    )


@pytest.mark.id("tst_u6vuno")
def test_the_code_is_exchanged_with_the_verifier(loop, identity):
    """The code goes to the token endpoint with the redirect URI, the verifier and the desk's
    secret"""
    desk = Desk(loop, identity)
    pending, answer = desk.start()
    desk.finish(pending, answer)
    [token] = desk.requests("/token")
    assert token.method == "POST"
    assert token.body == {
        "grant_type": "authorization_code",
        "code": answer["code"],
        "redirect_uri": "https://desk.test/auth/callback",
        "code_verifier": pending.verifier,
    }
    pair = base64.b64decode(token.headers["authorization"].removeprefix("Basic "))
    assert pair.decode() == "desk:desk-client-secret"


@pytest.mark.id("tst_alaaj7")
def test_a_person_who_declines_isnt_signed_in(loop, identity):
    """An answer with an error is refused, and no code is exchanged"""
    desk = Desk(loop, identity)
    pending = Pending.new()
    url = authorization_url(
        desk.keys.provider, identity.client_id, identity.redirect_uri, pending
    )
    answer = dict(parse_qsl(urlsplit(identity.declines(url)).query))
    with pytest.raises(SignInError):
        desk.finish(pending, answer)
    assert desk.requests("/token") == []


@pytest.mark.id("tst_9cxz2h")
def test_an_answer_to_another_request_is_refused(loop, identity):
    """An answer whose state isn't the sign-in's, or that has none, is refused before its
    code is exchanged"""
    desk = Desk(loop, identity)
    pending, answer = desk.start()
    for changed in (answer | {"state": Pending.new().state}, {"code": answer["code"]}):
        with pytest.raises(SignInError):
            desk.finish(pending, changed)
    assert desk.requests("/token") == []


@pytest.mark.id("tst_qt792z")
def test_a_code_works_once(loop, identity):
    """The same answer a second time is refused, as the provider gives a code once"""
    desk = Desk(loop, identity)
    pending, answer = desk.start()
    desk.finish(pending, answer)
    with pytest.raises(SignInError):
        desk.finish(pending, answer)


@pytest.mark.id("tst_bicyt2")
def test_a_token_for_another_app_is_refused(loop, identity):
    """An ID token for another audience, from another issuer, or out of date is refused"""
    desk = Desk(loop, identity)
    for shape in ({"audience": "another-app"}, {"issuer": "https://elsewhere.test"}):
        pending, answer = desk.start()
        identity.returns(
            id_token=identity.id_token("ada", nonce=pending.nonce, **shape)
        )
        with pytest.raises(SignInError):
            desk.finish(pending, answer)
    pending, answer = desk.start()
    identity.returns(id_token=identity.id_token("ada", nonce=pending.nonce, lasts=-60))
    with pytest.raises(SignInError):
        desk.finish(pending, answer)


@pytest.mark.id("tst_zfle9g")
def test_a_token_for_another_sign_in_is_refused(loop, identity):
    """An ID token with another nonce, or none, is refused"""
    desk = Desk(loop, identity)
    for nonce in (Pending.new().nonce, None):
        pending, answer = desk.start()
        identity.returns(id_token=identity.id_token("ada", nonce=nonce))
        with pytest.raises(SignInError):
            desk.finish(pending, answer)


@pytest.mark.id("tst_1hi6i6")
def test_a_token_the_provider_didnt_sign_is_refused(loop, identity):
    """An ID token signed with a key the provider doesn't publish is refused"""
    desk = Desk(loop, identity)
    pending, answer = desk.start()
    identity.returns(
        id_token=identity.id_token("ada", nonce=pending.nonce, stranger=True)
    )
    with pytest.raises(SignInError):
        desk.finish(pending, answer)


@pytest.mark.id("tst_n5sv1k")
def test_an_unsigned_token_is_refused(loop, identity):
    """An ID token whose header says it has no signature is refused"""
    desk = Desk(loop, identity)
    pending, answer = desk.start()
    signed = identity.id_token("ada", nonce=pending.nonce)
    _, claims, _ = signed.split(".")
    header = {"alg": "none", "typ": "JWT", "kid": "key-1"}
    head = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    identity.returns(id_token=f"{head}.{claims}.")
    with pytest.raises(SignInError):
        desk.finish(pending, answer)


@pytest.mark.id("tst_575xhl")
def test_no_id_token_is_refused(loop, identity):
    """A token response without an ID token is refused"""
    desk = Desk(loop, identity)
    pending, answer = desk.start()
    identity.returns(id_token=None)
    with pytest.raises(SignInError):
        desk.finish(pending, answer)


@pytest.mark.id("tst_v2c0sj")
def test_the_keys_are_fetched_once(loop, identity):
    """The provider's keys are fetched for the first sign-in, and not again for the next"""
    desk = Desk(loop, identity)
    desk.sign_in("ada")
    desk.sign_in("grace")
    assert len(desk.requests("/keys")) == 1


@pytest.mark.id("tst_2osqch")
def test_the_keys_are_fetched_again_after_a_rotation(loop, identity):
    """A token signed with a key the desk hasn't seen fetches the keys again, once"""
    desk = Desk(loop, identity)
    desk.sign_in("ada")
    identity.rotate()
    assert desk.sign_in("grace").subject == "user-grace"
    assert desk.sign_in("ada").subject == "user-ada"
    assert len(desk.requests("/keys")) == 2
