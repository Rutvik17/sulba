import asyncio
import base64
import hashlib
import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

import httpx
import jwt
import pytest

from sulba_fixtures import ScriptedIdentity
from sulba_runner import run

VERIFIER = "a-verifier-of-forty-three-characters-or-more-x"


@pytest.fixture
def identity() -> ScriptedIdentity:
    return ScriptedIdentity()


def challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def authorization(identity: ScriptedIdentity, **changes: str | None) -> str:
    query = {
        "response_type": "code",
        "client_id": identity.client_id,
        "redirect_uri": identity.redirect_uri,
        "scope": "openid email",
        "state": "the-state",
        "nonce": "the-nonce",
        "code_challenge": challenge(VERIFIER),
        "code_challenge_method": "S256",
    } | changes
    present = {name: value for name, value in query.items() if value is not None}
    return f"{identity.issuer}/authorize?{urlencode(present)}"


def answer(back: str) -> dict[str, str]:
    return dict(parse_qsl(urlsplit(back).query))


def exchange(identity: ScriptedIdentity, given: str, **changes: str) -> httpx.Response:
    form = {
        "grant_type": "authorization_code",
        "code": given,
        "redirect_uri": identity.redirect_uri,
        "code_verifier": VERIFIER,
    } | changes
    with identity.client() as client:
        return client.post("/token", data=form, auth=(identity.client_id, identity.client_secret))


def signed_in(identity: ScriptedIdentity, name: str = "ada") -> httpx.Response:
    return exchange(identity, answer(identity.sign_in(authorization(identity), name))["code"])


def validated(identity: ScriptedIdentity, token: str) -> dict[str, Any]:
    with identity.client() as client:
        keys = jwt.PyJWKSet.from_dict(client.get("/keys").json())
    key = keys[jwt.get_unverified_header(token)["kid"]]
    return jwt.decode(
        token, key, algorithms=["RS256"], audience=identity.client_id, issuer=identity.issuer
    )


def test_discovery_names_the_providers_endpoints(identity: ScriptedIdentity) -> None:
    with identity.client() as client:
        found = client.get("/.well-known/openid-configuration").json()
    assert found["issuer"] == "https://id.test"
    assert found["authorization_endpoint"] == "https://id.test/authorize"
    assert found["token_endpoint"] == "https://id.test/token"
    assert found["jwks_uri"] == "https://id.test/keys"
    assert found["userinfo_endpoint"] == "https://id.test/userinfo"
    assert found["code_challenge_methods_supported"] == ["S256"]
    assert found["id_token_signing_alg_values_supported"] == ["RS256"]


def test_a_person_signs_in_and_their_id_token_validates(identity: ScriptedIdentity) -> None:
    back = identity.sign_in(authorization(identity), "grace")
    assert back.startswith("https://desk.test/auth/callback?")
    assert answer(back)["state"] == "the-state"
    response = exchange(identity, answer(back)["code"])
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    tokens = response.json()
    assert tokens["token_type"] == "Bearer"
    assert tokens["expires_in"] == 300
    claims = validated(identity, tokens["id_token"])
    assert claims["sub"] == "user-grace"
    assert claims["email"] == "grace@example.com"
    assert claims["name"] == "Grace"
    assert claims["nonce"] == "the-nonce"
    assert claims["exp"] - claims["iat"] == 300


def test_the_client_can_send_its_secret_in_the_form(identity: ScriptedIdentity) -> None:
    code = answer(identity.sign_in(authorization(identity)))["code"]
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": identity.redirect_uri,
        "code_verifier": VERIFIER,
        "client_id": identity.client_id,
        "client_secret": identity.client_secret,
    }
    with identity.client() as client:
        assert client.post("/token", data=form).status_code == 200


def test_userinfo_answers_the_access_token_it_gave(identity: ScriptedIdentity) -> None:
    access_token = signed_in(identity).json()["access_token"]
    with identity.client() as client:
        found = client.get("/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        refused = client.get("/userinfo", headers={"Authorization": "Bearer another"})
    assert found.json() == {"sub": "user-ada", "email": "ada@example.com", "name": "Ada"}
    assert refused.status_code == 401
    assert refused.headers["www-authenticate"] == 'Bearer error="invalid_token"'


def test_a_persons_own_claims_go_in_their_tokens_and_userinfo(identity: ScriptedIdentity) -> None:
    identity.person("linus", email="linus@example.com", groups=["benefits", "supervisors"])
    tokens = signed_in(identity, "linus").json()
    claims = validated(identity, tokens["id_token"])
    assert claims["sub"] == "user-linus"
    assert claims["groups"] == ["benefits", "supervisors"]
    with identity.client() as client:
        bearer = {"Authorization": f"Bearer {tokens['access_token']}"}
        found = client.get("/userinfo", headers=bearer).json()
    assert found["groups"] == ["benefits", "supervisors"]
    assert "groups" not in validated(identity, signed_in(identity, "ada").json()["id_token"])


def test_a_code_works_once(identity: ScriptedIdentity) -> None:
    code = answer(identity.sign_in(authorization(identity)))["code"]
    assert exchange(identity, code).status_code == 200
    again = exchange(identity, code)
    assert (again.status_code, again.json()) == (400, {"error": "invalid_grant"})


@pytest.mark.parametrize(
    "changes",
    [
        {"code_verifier": "another-verifier-of-forty-three-characters-x"},
        {"redirect_uri": "https://desk.test/elsewhere"},
        {"code": "a-code-it-never-gave"},
    ],
)
def test_an_exchange_that_doesnt_fit_the_grant_is_refused(
    identity: ScriptedIdentity, changes: dict[str, str]
) -> None:
    code = answer(identity.sign_in(authorization(identity)))["code"]
    response = exchange(identity, code, **changes)
    assert (response.status_code, response.json()) == (400, {"error": "invalid_grant"})


def test_a_client_with_the_wrong_secret_is_refused(identity: ScriptedIdentity) -> None:
    code = answer(identity.sign_in(authorization(identity)))["code"]
    form = {"grant_type": "authorization_code", "code": code, "code_verifier": VERIFIER}
    with identity.client() as client:
        response = client.post("/token", data=form, auth=(identity.client_id, "a-guess"))
    assert (response.status_code, response.json()) == (401, {"error": "invalid_client"})
    assert response.headers["www-authenticate"] == "Basic"


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"client_id": "another-app"}, "The provider knows no client by that id."),
        (
            {"redirect_uri": "https://elsewhere.test/callback"},
            "The redirect URI isn't the one registered for the client.",
        ),
    ],
)
def test_a_request_it_cant_send_back_raises(
    identity: ScriptedIdentity, changes: dict[str, str], error: str
) -> None:
    with pytest.raises(ValueError, match=error):
        identity.sign_in(authorization(identity, **changes))


def test_a_request_to_another_address_raises(identity: ScriptedIdentity) -> None:
    with pytest.raises(ValueError, match="isn't the provider's authorization endpoint"):
        identity.sign_in(authorization(identity).replace("/authorize", "/login"))


@pytest.mark.parametrize(
    "changes",
    [
        {"code_challenge_method": "plain"},
        {"code_challenge": None, "code_challenge_method": None},
        {"scope": "email"},
        {"response_type": "token"},
    ],
)
def test_a_request_that_doesnt_fit_comes_back_with_an_error(
    identity: ScriptedIdentity, changes: dict[str, str | None]
) -> None:
    back = identity.sign_in(authorization(identity, **changes))
    assert answer(back) == {"error": "invalid_request", "state": "the-state"}


def test_a_person_who_declines_comes_back_with_access_denied(identity: ScriptedIdentity) -> None:
    assert answer(identity.declines(authorization(identity))) == {
        "error": "access_denied",
        "state": "the-state",
    }


@pytest.mark.parametrize(
    ("options", "error"),
    [
        ({"audience": "another-app"}, jwt.InvalidAudienceError),
        ({"issuer": "https://elsewhere.test"}, jwt.InvalidIssuerError),
        ({"lasts": -60}, jwt.ExpiredSignatureError),
    ],
)
def test_its_tokens_of_another_shape_fail_validation(
    identity: ScriptedIdentity, options: dict[str, Any], error: type[Exception]
) -> None:
    with pytest.raises(error):
        validated(identity, identity.id_token("ada", **options))


def test_a_strangers_token_is_signed_with_a_key_it_doesnt_publish(
    identity: ScriptedIdentity,
) -> None:
    token = identity.id_token("ada", stranger=True)
    with pytest.raises(KeyError):
        validated(identity, token)
    with identity.client() as client:
        published = jwt.PyJWKSet.from_dict(client.get("/keys").json())["key-1"]
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, published, algorithms=["RS256"], audience=identity.client_id)


def test_the_token_endpoint_gives_a_scripted_answer_once(identity: ScriptedIdentity) -> None:
    identity.returns(id_token=identity.id_token("grace", audience="another-app"))
    scripted = signed_in(identity).json()
    assert scripted["token_type"] == "Bearer"
    assert jwt.decode(scripted["id_token"], options={"verify_signature": False})["sub"] == (
        "user-grace"
    )
    with pytest.raises(jwt.InvalidAudienceError):
        validated(identity, scripted["id_token"])
    assert validated(identity, signed_in(identity).json()["id_token"])["sub"] == "user-ada"


def test_after_a_rotation_both_keys_are_published(identity: ScriptedIdentity) -> None:
    before = signed_in(identity).json()["id_token"]
    identity.rotate()
    after = signed_in(identity).json()["id_token"]
    with identity.client() as client:
        kids = [key["kid"] for key in client.get("/keys").json()["keys"]]
    assert kids == ["key-1", "key-2"]
    assert jwt.get_unverified_header(before)["kid"] == "key-1"
    assert jwt.get_unverified_header(after)["kid"] == "key-2"
    assert validated(identity, before)["sub"] == validated(identity, after)["sub"] == "user-ada"


def test_it_keeps_each_request_it_received(identity: ScriptedIdentity) -> None:
    signed_in(identity)
    [token] = identity.requests
    assert (token.method, token.path) == ("POST", "/token")
    assert token.headers["authorization"].startswith("Basic ")
    assert token.body["grant_type"] == "authorization_code"
    assert token.body["code_verifier"] == VERIFIER


def test_an_async_client_reaches_it_too(identity: ScriptedIdentity) -> None:
    async def keys() -> list[str]:
        async with identity.async_client() as client:
            response = await client.get("/keys")
        return [key["kid"] for key in response.json()["keys"]]

    assert asyncio.run(keys()) == ["key-1"]


SESSION = {
    "tests/test_sign_in.py": """
import pytest


@pytest.mark.id("tst_idn001")
def test_sign_in(identity):
    back = identity.sign_in(
        "https://id.test/authorize?response_type=code&client_id=desk"
        "&redirect_uri=https%3A%2F%2Fdesk.test%2Fauth%2Fcallback&scope=openid"
        "&code_challenge=abc&code_challenge_method=S256&state=s"
    )
    assert back.startswith("https://desk.test/auth/callback?code=")
""",
}


def test_a_sessions_tests_can_ask_for_it() -> None:
    result = json.loads(run(json.dumps(SESSION), json.dumps(["tests/test_sign_in.py"])))
    assert [(test["name"], test["status"]) for test in result["tests"]] == [
        ("test_sign_in", "pass")
    ]
