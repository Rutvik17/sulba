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
        raise NotImplementedError

    @property
    def challenge(self) -> str:
        """The verifier's S256 code challenge: its SHA-256, in base64url without padding."""
        raise NotImplementedError


async def discover(client: httpx.AsyncClient, issuer: str) -> Provider:
    """The provider at the issuer, from its discovery document. SignInError when the document
    can't be read, names another issuer, or offers no S256 code challenge."""
    raise NotImplementedError


def authorization_url(
    provider: Provider,
    client_id: str,
    redirect_uri: str,
    pending: Pending,
    scope: str = "openid email profile",
) -> str:
    """The address that asks the provider to sign a person in for the client, and send the
    browser back to the redirect URI with a code."""
    raise NotImplementedError
