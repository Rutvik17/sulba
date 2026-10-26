"""The second half of signing in: the provider's answer at the redirect URI, its code exchanged
for an ID token, and the token checked before the person it names is trusted."""

from collections.abc import Mapping
from dataclasses import dataclass

import httpx
import jwt

from sign_in import Pending, Provider, SignInError


@dataclass(frozen=True)
class Person:
    """Someone the provider signed in: its issuer and their subject, which together name them,
    and the email and name the provider gave, if any."""

    issuer: str
    subject: str
    email: str | None
    name: str | None


class Keys:
    """The provider's signing keys, from its JWK Set: fetched the first time a key is needed,
    and again when a token names a key they don't hold, as after the provider rotates them."""

    def __init__(self, client: httpx.AsyncClient, provider: Provider) -> None:
        self.client = client
        self.provider = provider
        self.held: dict[str, jwt.PyJWK] = {}

    async def key(self, kid: str) -> jwt.PyJWK:
        """The key with the id. SignInError when the provider doesn't publish one."""
        if kid not in self.held:
            try:
                response = await self.client.get(self.provider.jwks_uri)
            except httpx.HTTPError as error:
                raise SignInError(
                    f"The provider's keys can't be read: {error}"
                ) from error
            if response.status_code != 200:
                raise SignInError(
                    f"The provider's keys answered {response.status_code}."
                )
            found = jwt.PyJWKSet.from_dict(response.json()).keys
            self.held = {key.key_id: key for key in found if key.key_id is not None}
        if kid not in self.held:
            raise SignInError(
                "The ID token is signed with a key the provider doesn't publish."
            )
        return self.held[kid]


async def person_from(
    client: httpx.AsyncClient,
    keys: Keys,
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    pending: Pending,
    answer: Mapping[str, str],
) -> Person:
    """The person the provider signed in, from its answer at the redirect URI to the pending
    sign-in's request. SignInError when the provider refused, the answer isn't to this request,
    the code can't be exchanged, or the ID token doesn't check out."""
    provider = keys.provider
    if "error" in answer:
        raise SignInError(f"The provider didn't sign the person in: {answer['error']}.")
    if answer.get("state") != pending.state:
        raise SignInError("The answer's state isn't this sign-in's.")
    if not answer.get("code"):
        raise SignInError("The answer has no code.")
    try:
        response = await client.post(
            provider.token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": answer["code"],
                "redirect_uri": redirect_uri,
                "code_verifier": pending.verifier,
            },
            auth=(client_id, client_secret),
        )
    except httpx.HTTPError as error:
        raise SignInError(f"The token endpoint can't be reached: {error}") from error
    if response.status_code != 200:
        raise SignInError(f"The token endpoint answered {response.status_code}.")
    id_token = response.json().get("id_token")
    if not isinstance(id_token, str):
        raise SignInError("The token endpoint gave no ID token.")
    try:
        kid = jwt.get_unverified_header(id_token).get("kid")
        key = await keys.key(kid if isinstance(kid, str) else "")
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=provider.issuer,
            options={
                "require": ["iss", "sub", "aud", "exp", "iat", "nonce"],
                "strict_aud": True,
            },
        )
    except jwt.InvalidTokenError as error:
        raise SignInError(f"The ID token doesn't check out: {error}") from error
    if claims["nonce"] != pending.nonce:
        raise SignInError("The ID token's nonce isn't this sign-in's.")
    return Person(
        issuer=claims["iss"],
        subject=claims["sub"],
        email=claims.get("email"),
        name=claims.get("name"),
    )
