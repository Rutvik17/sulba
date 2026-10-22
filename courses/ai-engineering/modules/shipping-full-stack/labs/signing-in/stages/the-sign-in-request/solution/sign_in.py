"""The first half of signing in with OpenID Connect: the provider's addresses, from its discovery
document, and the authorization request that sends the browser there, with the state, the nonce
and the PKCE verifier that tie the provider's answer to this one request."""

import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx


class SignInError(Exception):
    """Signing in failed, for the reason the message gives."""


@dataclass(frozen=True)
class Provider:
    """An OpenID provider: its issuer, and the addresses its discovery document gives."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str


@dataclass(frozen=True)
class Pending:
    """A sign-in on its way: the state, the nonce and the PKCE verifier of its request."""

    state: str
    nonce: str
    verifier: str

    @classmethod
    def new(cls) -> "Pending":
        """A sign-in with values no one can guess: 32 random bytes each, as 43 characters."""
        return cls(
            secrets.token_urlsafe(32),
            secrets.token_urlsafe(32),
            secrets.token_urlsafe(32),
        )

    @property
    def challenge(self) -> str:
        """The verifier's S256 code challenge: its SHA-256, in base64url without padding."""
        digest = hashlib.sha256(self.verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


async def discover(client: httpx.AsyncClient, issuer: str) -> Provider:
    """The provider at the issuer, from its discovery document. SignInError when the document
    can't be read, names another issuer, or offers no S256 code challenge."""
    url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
    try:
        response = await client.get(url)
    except httpx.HTTPError as error:
        raise SignInError(
            f"The provider's discovery document can't be read: {error}"
        ) from error
    if response.status_code != 200:
        raise SignInError(
            f"The provider's discovery document answered {response.status_code}."
        )
    document = response.json()
    if document.get("issuer") != issuer:
        raise SignInError("The discovery document names another issuer.")
    if "S256" not in document.get("code_challenge_methods_supported", []):
        raise SignInError("The provider doesn't offer S256 code challenges.")
    return Provider(
        issuer=issuer,
        authorization_endpoint=document["authorization_endpoint"],
        token_endpoint=document["token_endpoint"],
        jwks_uri=document["jwks_uri"],
    )


def authorization_url(
    provider: Provider,
    client_id: str,
    redirect_uri: str,
    pending: Pending,
    scope: str = "openid email profile",
) -> str:
    """The address that asks the provider to sign a person in for the client, and send the
    browser back to the redirect URI with a code."""
    query = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": pending.state,
        "nonce": pending.nonce,
        "code_challenge": pending.challenge,
        "code_challenge_method": "S256",
    }
    return f"{provider.authorization_endpoint}?{urlencode(query)}"
