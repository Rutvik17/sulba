from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


def pinned(requirement):
    """The package's name and version when the requirement pins one exactly, or None."""
    parsed = Requirement(requirement)
    specifiers = list(parsed.specifier)
    if len(specifiers) == 1 and specifiers[0].operator == "==":
        return canonicalize_name(parsed.name), specifiers[0].version
    return None
