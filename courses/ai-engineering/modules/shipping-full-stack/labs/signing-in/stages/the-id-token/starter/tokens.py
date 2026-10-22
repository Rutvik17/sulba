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
        raise NotImplementedError


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
    raise NotImplementedError
