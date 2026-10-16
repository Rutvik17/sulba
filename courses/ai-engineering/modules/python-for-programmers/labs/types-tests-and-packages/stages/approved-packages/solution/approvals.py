"""The clinic's check of the packages the service installs."""

import tomllib

from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name


def unapproved(lock: str, approved: dict[str, str]) -> list[str]:
    """A message for each package in the lock file that the approved list doesn't approve,
    in the lock file's order."""
    listed = {canonicalize_name(name): versions for name, versions in approved.items()}
    problems = []
    for package in tomllib.loads(lock)["package"]:
        if "editable" in package["source"]:
            continue
        name, version = package["name"], package["version"]
        versions = listed.get(canonicalize_name(name))
        if versions is None:
            problems.append(f"{name} {version} isn't on the approved list")
        elif version not in SpecifierSet(versions):
            problems.append(f"{name} {version} is outside the approved {versions}")
    return problems
