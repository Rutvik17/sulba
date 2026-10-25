"""The office's staff, from the ID token their sign-in gives: who they are, and the groups the
office lets them read by."""

from dataclasses import dataclass

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
    raise NotImplementedError
