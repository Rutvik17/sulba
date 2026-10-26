"""The office's staff, from the ID token their sign-in gives: who they are, and the groups the
office lets them read by."""

from dataclasses import dataclass

import jwt

from sign_in import SignInError
from tokens import Keys

# The groups the office's directory puts its staff in, and the office's group each reads as.
GROUPS = {
    "ssa-team": "benefits",
    "va-team": "veterans",
    "reception": "front-desk",
    "managers": "supervisors",
}


@dataclass(frozen=True)
class Staff:
    """A member of staff: the subject their provider names them by, and the office's groups."""

    subject: str
    groups: frozenset[str]


async def staff_from(keys: Keys, id_token: str, client_id: str) -> Staff:
    """The member of staff the ID token names, in the office's groups that their directory's
    groups map to. SignInError when the token doesn't check out."""
    try:
        kid = jwt.get_unverified_header(id_token).get("kid")
        key = await keys.key(kid if isinstance(kid, str) else "")
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=keys.provider.issuer,
            options={
                "require": ["iss", "sub", "aud", "exp", "iat"],
                "strict_aud": True,
            },
        )
    except jwt.InvalidTokenError as error:
        raise SignInError(f"The ID token doesn't check out: {error}") from error
    given = claims.get("groups")
    names = given if isinstance(given, list) else []
    groups = frozenset(
        GROUPS[name] for name in names if isinstance(name, str) and name in GROUPS
    )
    return Staff(claims["sub"], groups)
