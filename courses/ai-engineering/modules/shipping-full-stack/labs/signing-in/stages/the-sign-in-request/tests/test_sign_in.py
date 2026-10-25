import base64
import hashlib
import re
from urllib.parse import parse_qsl, urlsplit

import httpx
import pytest

from sign_in import Pending, Provider, SignInError, authorization_url, discover


def provider(loop, identity):
    return loop.run_until_complete(discover(identity.async_client(), identity.issuer))


def query(url):
    return dict(parse_qsl(urlsplit(url).query))


def answering(document):
    """A client whose every request gets the discovery document given."""
    return httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=document)
        )
    )


@pytest.mark.id("tst_5sbqmc")
def test_the_provider_from_its_discovery_document(loop, identity):
    """The provider's addresses come from its discovery document"""
    found = provider(loop, identity)
    assert found == Provider(
        issuer="https://id.test",
        authorization_endpoint="https://id.test/authorize",
        token_endpoint="https://id.test/token",
        jwks_uri="https://id.test/keys",
    )
    assert [(each.method, each.path) for each in identity.requests] == [
        ("GET", "/.well-known/openid-configuration")
    ]


@pytest.mark.id("tst_qvx1uy")
def test_a_document_for_another_issuer_is_refused(loop, identity):
    """A discovery document that names another issuer is refused"""
    with identity.client() as client:
        document = client.get("/.well-known/openid-configuration").json()
    document["issuer"] = "https://elsewhere.test"
    with pytest.raises(SignInError):
        loop.run_until_complete(discover(answering(document), "https://id.test"))


@pytest.mark.id("tst_24rfuf")
def test_a_provider_without_s256_is_refused(loop, identity):
    """A provider that offers no S256 code challenge, or none at all, is refused"""
    with identity.client() as client:
        document = client.get("/.well-known/openid-configuration").json()
    for methods in (["plain"], None):
        if methods is None:
            del document["code_challenge_methods_supported"]
        else:
            document["code_challenge_methods_supported"] = methods
        with pytest.raises(SignInError):
            loop.run_until_complete(discover(answering(document), "https://id.test"))


@pytest.mark.id("tst_r5umxw")
def test_a_document_that_cant_be_read_is_refused(loop):
    """A discovery document that answers with an error, or not at all, is refused"""
    failing = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )

    def unreachable(request):
        raise httpx.ConnectError("No route to host", request=request)

    gone = httpx.AsyncClient(transport=httpx.MockTransport(unreachable))
    for client in (failing, gone):
        with pytest.raises(SignInError):
            loop.run_until_complete(discover(client, "https://id.test"))


@pytest.mark.id("tst_1oli3j")
def test_each_sign_in_has_values_of_its_own():
    """Each sign-in's state, nonce and verifier are new, and different from each other"""
    made = [Pending.new() for _ in range(50)]
    values = [
        value for each in made for value in (each.state, each.nonce, each.verifier)
    ]
    assert len(set(values)) == len(values)


@pytest.mark.id("tst_byfkrb")
def test_a_verifier_rfc_7636_allows():
    """The verifier is 43 to 128 of the characters RFC 7636 allows"""
    for _ in range(50):
        verifier = Pending.new().verifier
        assert re.fullmatch(r"[A-Za-z0-9\-._~]{43,128}", verifier)


@pytest.mark.id("tst_ozp1wt")
def test_the_challenge_is_the_verifiers_s256():
    """The code challenge is the verifier's SHA-256 in base64url, without padding"""
    pending = Pending("s", "n", "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")
    # RFC 7636's own example, from its appendix B.
    assert pending.challenge == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
    verifier = Pending.new().verifier
    digest = hashlib.sha256(verifier.encode()).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    assert Pending("s", "n", verifier).challenge == expected


@pytest.mark.id("tst_ijkcm1")
def test_the_authorization_request(loop, identity):
    """The request asks for a code, for openid, with the state, nonce and S256 challenge"""
    pending = Pending.new()
    url = authorization_url(
        provider(loop, identity), "desk", "https://desk.test/auth/callback", pending
    )
    assert url.startswith("https://id.test/authorize?")
    assert query(url) == {
        "response_type": "code",
        "client_id": "desk",
        "redirect_uri": "https://desk.test/auth/callback",
        "scope": "openid email profile",
        "state": pending.state,
        "nonce": pending.nonce,
        "code_challenge": pending.challenge,
        "code_challenge_method": "S256",
    }


@pytest.mark.id("tst_mdzopb")
def test_the_provider_signs_a_person_in_from_it(loop, identity):
    """The provider takes the request and sends the browser back with a code and the state"""
    pending = Pending.new()
    url = authorization_url(
        provider(loop, identity), identity.client_id, identity.redirect_uri, pending
    )
    back = identity.sign_in(url, "grace")
    assert back.startswith(f"{identity.redirect_uri}?")
    answer = query(back)
    assert answer["state"] == pending.state
    assert answer["code"]
